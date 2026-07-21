import uuid
from pathlib import Path

from ..config import UPLOAD_DIR


def save_upload(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(data)
    return str(dest)


def read_file(path: str) -> bytes:
    return Path(path).read_bytes()


def delete_upload(path: str) -> None:
    Path(path).unlink(missing_ok=True)
