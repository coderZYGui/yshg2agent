import base64
import json
import mimetypes
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..deps import get_current_user
from ..models import Conversation, Document, Message, User
from ..schemas import ChatRequest
from ..services import llm

router = APIRouter(prefix="/api/chat", tags=["chat"])

ROLE_LABELS = {
    "pm": "产品经理",
    "qa": "测试开发工程师",
    "legal": "法务",
}


def _sse(event: str, data: dict | str) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _extract_json(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _attachment_docs(db: Session, document_ids: list[int]) -> list[dict]:
    if not document_ids:
        return []

    docs = db.query(Document).filter(Document.id.in_(document_ids)).all()
    payloads = []
    for doc in docs:
        mime = doc.mime or mimetypes.guess_type(doc.filename)[0] or ""
        payloads.append(
            {
                "id": doc.id,
                "filename": doc.filename,
                "mime": mime,
                "storage_path": doc.storage_path,
                "is_image": mime.startswith("image/"),
            }
        )
    return payloads


def _image_data_urls(docs: list[dict]) -> list[str]:
    urls = []
    for doc in docs:
        if not doc["is_image"]:
            continue
        path = Path(doc["storage_path"])
        if not path.exists():
            continue
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        urls.append(f"data:{doc['mime']};base64,{data}")
    return urls


def _build_bailian_prompt(role: str, message: str, docs: list[dict]) -> str:
    role_label = ROLE_LABELS.get(role, ROLE_LABELS["pm"])
    attachment_names = [doc["filename"] for doc in docs]
    parts = [
        f"当前用户角色：{role_label}",
        f"用户问题：{message}",
    ]
    if attachment_names:
        parts.append("用户已上传附件：" + "、".join(attachment_names))
    parts.append(
        "请直接基于百炼应用内已配置的隐私合规知识库，以及本次问题和附件内容进行分析。"
        "如果有图片附件，请识别图片中的隐私合规风险。"
        "优先快速输出结论，再输出完整的风险点、合规判定、整改建议和引用依据。"
    )
    return "\n".join(parts)


async def _upload_session_files(docs: list[dict]) -> list[str]:
    file_ids = []
    for doc in docs:
        if doc["is_image"]:
            continue
        path = Path(doc["storage_path"])
        if not path.exists():
            continue
        try:
            file_id = await llm.upload_session_file(
                str(path), doc["filename"], doc["mime"]
            )
        except Exception:
            file_id = None
        if file_id:
            file_ids.append(file_id)
    return file_ids


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv: Conversation | None = None
    if req.conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == req.conversation_id, Conversation.user_id == user.id)
            .first()
        )
    if conv is None:
        conv = Conversation(
            user_id=user.id, title=req.message[:20] or "新会话", role=req.role
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    conv_id = conv.id
    docs = _attachment_docs(db, req.document_ids)
    image_urls = _image_data_urls(docs)
    user_prompt = _build_bailian_prompt(req.role, req.message, docs)

    db.add(
        Message(
            conversation_id=conv_id,
            role="user",
            content=req.message,
            attachments=req.document_ids,
        )
    )
    db.commit()

    mock_payload = {
        "question": req.message,
        "has_doc": bool(req.document_ids),
    }

    async def event_gen() -> AsyncIterator[str]:
        yield _sse(
            "meta",
            {
                "conversation_id": conv_id,
                "attachments": len(docs),
                "images": len(image_urls),
            },
        )

        session_file_ids = await _upload_session_files(docs)

        buffer = ""
        async for token in llm.stream_chat(
            "",
            user_prompt,
            images=image_urls,
            session_file_ids=session_file_ids,
            mock_payload=mock_payload,
        ):
            buffer += token
            yield _sse("token", {"t": token})

        review = _extract_json(buffer) or {
            "summary": buffer,
            "items": [],
        }
        summary = review.get("summary", "")

        with SessionLocal() as wdb:
            wdb.add(
                Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=summary or buffer[:500],
                    review_result=review,
                )
            )
            wdb.commit()

        yield _sse("review", review)
        yield _sse("done", {"conversation_id": conv_id})

    return StreamingResponse(event_gen(), media_type="text/event-stream")
