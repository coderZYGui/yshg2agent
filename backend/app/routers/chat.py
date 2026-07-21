import base64
import json
import mimetypes
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Document, User
from ..schemas import ChatRequest
from ..services import llm, storage
from ..services.bailian_files import BailianFileError

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


def _attachment_docs(
    db: Session, document_ids: list[int], owner_id: int
) -> list[dict]:
    if not document_ids:
        return []

    docs = (
        db.query(Document)
        .filter(
            Document.id.in_(document_ids),
            Document.owner_id == owner_id,
            Document.kind == "review",
        )
        .all()
    )
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
        path = Path(doc["storage_path"])
        if not path.exists():
            continue
        file_id = await llm.upload_session_file(
            str(path), doc["filename"], doc["mime"]
        )
        if file_id:
            file_ids.append(file_id)
    return file_ids


def _delete_attachment_docs(db: Session, docs: list[dict], owner_id: int) -> None:
    document_ids = [doc["id"] for doc in docs]
    if not document_ids:
        return
    rows = (
        db.query(Document)
        .filter(
            Document.id.in_(document_ids),
            Document.owner_id == owner_id,
            Document.kind == "review",
        )
        .all()
    )
    for row in rows:
        storage.delete_upload(row.storage_path)
        db.delete(row)
    db.commit()


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    docs = _attachment_docs(db, req.document_ids, user.id)
    image_urls = _image_data_urls(docs)
    user_prompt = _build_bailian_prompt(req.role, req.message, docs)

    mock_payload = {
        "question": req.message,
        "has_doc": bool(req.document_ids),
    }

    async def event_gen() -> AsyncIterator[str]:
        yield _sse(
            "meta",
            {
                "attachments": len(docs),
                "images": len(image_urls),
            },
        )

        try:
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
        except BailianFileError as exc:
            yield _sse("error", {"message": str(exc)})
        except Exception:
            yield _sse("error", {"message": "智能体调用失败，请稍后重试。"})
        else:
            review = _extract_json(buffer) or {
                "summary": buffer,
                "items": [],
            }

            yield _sse("review", review)
            yield _sse("done", {})
        finally:
            _delete_attachment_docs(db, docs, user.id)

    return StreamingResponse(event_gen(), media_type="text/event-stream")
