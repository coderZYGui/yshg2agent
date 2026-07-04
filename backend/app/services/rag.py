"""RAG 流程编排: 入库(切片->embedding->存储) 与 检索(embedding->检索->组装上下文)。"""

from sqlalchemy.orm import Session

from ..models import Chunk, Document
from . import embeddings, knowledge_index, parser, vectorstore


def ingest_document(db: Session, document: Document, full_text: str) -> int:
    """将文档切片、向量化并写入 chunks。返回切片数。"""
    # 清理旧切片
    db.query(Chunk).filter(Chunk.document_id == document.id).delete()

    pieces = parser.chunk_text(full_text)
    if not pieces:
        knowledge_index.sync_document(document, [])
        return 0

    vectors = embeddings.embed_texts(pieces)
    for seq, (text, vec) in enumerate(zip(pieces, vectors, strict=True)):
        db.add(
            Chunk(
                document_id=document.id,
                seq=seq,
                text=text,
                kind=document.kind,
                embedding_json=vec,
                meta={"filename": document.filename},
            )
        )
    db.commit()
    knowledge_index.sync_document(document, pieces)
    return len(pieces)


def retrieve(db: Session, query: str, top_k: int = 5) -> list[dict]:
    q_vec = embeddings.embed_query(query)
    results = vectorstore.search(db, q_vec, top_k=top_k, kind="knowledge")
    return _rerank(query, results, top_k)


def _rerank(query: str, results: list[dict], top_k: int) -> list[dict]:
    """轻量重排: 结合向量分与关键词命中(生产可替换为 BGE-reranker)。"""
    q_terms = {t for t in query.lower() if not t.isspace()}
    for r in results:
        text = r["text"].lower()
        overlap = sum(1 for t in q_terms if t in text)
        r["rerank_score"] = r["score"] + 0.02 * overlap
    results.sort(key=lambda x: x["rerank_score"], reverse=True)
    return results[:top_k]


def build_context(results: list[dict]) -> str:
    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(
            f"[片段{i}] 来源:《{r['document']}》 相关度:{r['score']:.3f}\n{r['text']}"
        )
    return "\n\n".join(blocks)


def collect_document_text(db: Session, document_ids: list[int]) -> str:
    if not document_ids:
        return ""
    docs = db.query(Document).filter(Document.id.in_(document_ids)).all()
    parts = []
    for d in docs:
        chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == d.id)
            .order_by(Chunk.seq)
            .all()
        )
        text = "\n".join(c.text for c in chunks)
        parts.append(f"《{d.filename}》\n{text}")
    return "\n\n".join(parts)
