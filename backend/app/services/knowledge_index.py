import json
from datetime import datetime, timezone

from ..config import KNOWLEDGE_INDEX_FILE
from ..models import Document


def _read_index() -> list[dict]:
    if not KNOWLEDGE_INDEX_FILE.exists():
        return []
    try:
        data = json.loads(KNOWLEDGE_INDEX_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _write_index(rows: list[dict]) -> None:
    KNOWLEDGE_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_INDEX_FILE.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def sync_document(document: Document, chunks: list[str]) -> None:
    rows = [row for row in _read_index() if row.get("document_id") != document.id]
    now = datetime.now(timezone.utc).isoformat()
    rows.extend(
        {
            "document_id": document.id,
            "filename": document.filename,
            "kind": document.kind,
            "seq": seq,
            "text": text,
            "updated_at": now,
        }
        for seq, text in enumerate(chunks)
    )
    rows.sort(
        key=lambda row: (
            str(row.get("kind", "")),
            str(row.get("filename", "")),
            int(row.get("seq", 0)),
        )
    )
    _write_index(rows)


def delete_document(document_id: int) -> None:
    _write_index([row for row in _read_index() if row.get("document_id") != document_id])
