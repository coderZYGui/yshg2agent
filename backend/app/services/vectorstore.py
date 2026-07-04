"""Local vector search over chunks stored in SQLite.

The MVP intentionally avoids external vector infrastructure. Embeddings are
stored as JSON on each Chunk row and searched with cosine similarity in process.
"""

import math

from sqlalchemy.orm import Session

from ..models import Chunk, Document


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def search(
    db: Session,
    query_embedding: list[float],
    top_k: int = 5,
    kind: str = "knowledge",
) -> list[dict]:
    rows = (
        db.query(Chunk, Document.filename)
        .join(Document, Chunk.document_id == Document.id)
        .filter(Chunk.kind == kind, Chunk.embedding_json.isnot(None))
        .all()
    )
    if not rows:
        return []

    scored: list[tuple[float, Chunk, str]] = []
    for chunk, filename in rows:
        score = _cosine(query_embedding, chunk.embedding_json or [])
        scored.append((score, chunk, filename))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "chunk_id": c.id,
            "document_id": c.document_id,
            "document": fname,
            "text": c.text,
            "score": s,
        }
        for s, c, fname in scored[:top_k]
    ]
