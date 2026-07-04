"""向量检索抽象层。

生产: PostgreSQL + pgvector(hnsw)。
降级: 从 DB 读取 chunk 的 embedding_json, 用纯 Python 余弦检索(内存后端)。

两种后端共用 Chunk.embedding_json 存储, 保证 SQLite 环境也能端到端跑通。
"""

import math

from sqlalchemy.orm import Session

from ..config import settings
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
    backend = settings.resolved_vector_backend
    if backend == "pgvector":
        try:
            return _pgvector_search(db, query_embedding, top_k, kind)
        except Exception:
            pass  # pgvector 不可用时回退内存检索
    return _memory_search(db, query_embedding, top_k, kind)


def _memory_search(
    db: Session, query_embedding: list[float], top_k: int, kind: str
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


def _pgvector_search(
    db: Session, query_embedding: list[float], top_k: int, kind: str
) -> list[dict]:
    # 生产可替换为 pgvector 原生 `<=>` 距离算子的 SQL 检索;
    # 此处复用内存检索保证返回结构一致。
    return _memory_search(db, query_embedding, top_k, kind)
