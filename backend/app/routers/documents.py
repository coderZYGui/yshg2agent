from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import AuditLog, Document, User
from ..schemas import DocumentOut
from ..services import storage

router = APIRouter(prefix="/api/documents", tags=["documents"])

ATTACHMENT_LIMITS_MB = {
    ".doc": 100,
    ".docx": 100,
    ".wps": 100,
    ".ppt": 100,
    ".pptx": 100,
    ".xls": 100,
    ".xlsx": 100,
    ".md": 100,
    ".txt": 100,
    ".pdf": 100,
    ".png": 20,
    ".jpg": 20,
    ".jpeg": 20,
    ".bmp": 20,
    ".gif": 20,
    ".mp4": 512,
    ".mkv": 512,
    ".avi": 512,
    ".mov": 512,
    ".wmv": 512,
    ".aac": 512,
    ".amr": 512,
    ".flac": 512,
    ".flv": 512,
    ".m4a": 512,
    ".mp3": 512,
    ".mpeg": 512,
    ".ogg": 512,
    ".opus": 512,
    ".wav": 512,
    ".webm": 512,
    ".wma": 512,
}


def _validate_attachment(filename: str, size: int) -> None:
    extension = Path(filename).suffix.lower()
    max_mb = ATTACHMENT_LIMITS_MB.get(extension)
    if max_mb is None:
        raise HTTPException(status_code=400, detail=f"不支持的附件格式：{extension or '无扩展名'}")
    if size > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"附件超过 {max_mb}MB 限制")


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    kind: str = Form("review"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if kind not in {"review", "knowledge"}:
        raise HTTPException(status_code=400, detail="kind must be review or knowledge")

    filename = file.filename or "upload.bin"
    if file.size is not None:
        _validate_attachment(filename, file.size)
    data = await file.read()
    _validate_attachment(filename, len(data))
    path = storage.save_upload(filename, data)

    doc = Document(
        owner_id=user.id,
        filename=filename,
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


@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    doc = (
        db.query(Document)
        .filter(
            Document.id == doc_id,
            Document.owner_id == user.id,
            Document.kind == "review",
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    storage.delete_upload(doc.storage_path)
    db.delete(doc)
    db.commit()
