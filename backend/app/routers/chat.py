import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..deps import get_current_user
from ..models import Conversation, Message, User
from ..schemas import ChatRequest
from ..services import llm, rag
from ..services.prompts import build_system_prompt, build_user_prompt
from ..services.redaction import redact

router = APIRouter(prefix="/api/chat", tags=["chat"])


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


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 会话
    conv: Conversation | None = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == req.conversation_id, Conversation.user_id == user.id
        ).first()
    if conv is None:
        conv = Conversation(user_id=user.id, title=req.message[:20] or "新会话", role=req.role)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    conv_id = conv.id

    # 保存用户消息
    db.add(Message(conversation_id=conv_id, role="user", content=req.message,
                   attachments=req.document_ids))
    db.commit()

    # 检索 + 组装(在请求线程内完成, 结果传入生成器)
    safe_query, _ = redact(req.message)
    results = rag.retrieve(db, safe_query, top_k=5)
    context = rag.build_context(results)
    doc_text = rag.collect_document_text(db, req.document_ids)
    safe_doc, _ = redact(doc_text)

    system_prompt = build_system_prompt(req.role)
    user_prompt = build_user_prompt(safe_query, context, safe_doc)

    mock_payload = {
        "question": req.message,
        "has_doc": bool(req.document_ids),
        "citations": [
            {"document": r["document"], "snippet": r["text"], "score": r["score"]}
            for r in results
        ],
    }

    async def event_gen() -> AsyncIterator[str]:
        yield _sse("meta", {"conversation_id": conv_id, "retrieved": len(results)})

        buffer = ""
        async for token in llm.stream_chat(
            system_prompt, user_prompt, mock_payload=mock_payload
        ):
            buffer += token
            yield _sse("token", {"t": token})

        review = _extract_json(buffer) or {
            "summary": buffer[:200],
            "items": [],
        }
        summary = review.get("summary", "")

        # 独立 session 写库(避免与请求 session 生命周期冲突)
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
