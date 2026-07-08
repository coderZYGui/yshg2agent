from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import AuditLog, Document, User
from ..schemas import DocumentOut
from ..services import storage

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    kind: str = Form("review"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if kind not in {"review", "knowledge"}:
        raise HTTPException(status_code=400, detail="kind must be review or knowledge")

    data = await file.read()
    path = storage.save_upload(file.filename or "upload.bin", data)

    doc = Document(
        owner_id=user.id,
        filename=file.filename or "upload.bin",
        mime=file.content_type or "",
        storage_path=path,
        kind=kind,
        parse_status="parsing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    doc.summary = "已上传，聊天时将直接转发给百炼应用处理。"
    doc.parse_status = "done"
    db.add(AuditLog(user_id=user.id, action="upload_document", target=doc.filename))
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    return doc
