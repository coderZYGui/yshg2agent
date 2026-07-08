from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import AuditLog, Document, User
from ..schemas import DocumentOut
from ..services import storage

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("", response_model=list[DocumentOut])
def list_knowledge(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return (
        db.query(Document)
        .filter(Document.kind == "knowledge")
        .order_by(Document.created_at.desc())
        .all()
    )


@router.post("", response_model=DocumentOut)
async def add_knowledge(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await file.read()
    path = storage.save_upload(file.filename or "kb.bin", data)
    doc = Document(
        owner_id=user.id,
        filename=file.filename or "kb.bin",
        mime=file.content_type or "",
        storage_path=path,
        kind="knowledge",
        parse_status="parsing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    doc.summary = "百炼知识库请在阿里云百炼控制台维护；本地仅保存上传记录。"
    doc.parse_status = "done"
    db.add(AuditLog(user_id=user.id, action="add_knowledge", target=doc.filename))
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}")
def delete_knowledge(
    doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.kind == "knowledge"
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="知识库文档不存在")
    db.delete(doc)
    db.add(AuditLog(user_id=user.id, action="delete_knowledge", target=doc.filename))
    db.commit()
    return {"ok": True}
