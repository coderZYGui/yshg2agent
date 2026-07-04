"""Embedding 抽象层。

生产: 调用 BGE-M3 兼容的 embedding API。
降级: 无 Key 时使用确定性本地向量(基于字符 n-gram 哈希), 保证离线可检索。
"""

import hashlib
import math

import httpx

from ..config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if settings.embedding_is_local:
        return [_local_embed(t) for t in texts]
    return _api_embed(texts)


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def _api_embed(texts: list[str]) -> list[list[float]]:
    url = f"{settings.embedding_base_url.rstrip('/')}/embeddings"
    headers = {"Authorization": f"Bearer {settings.embedding_api_key}"}
    payload = {"model": settings.embedding_model, "input": texts}
    with httpx.Client(timeout=60) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()["data"]
    return [item["embedding"] for item in data]


def _local_embed(text: str) -> list[float]:
    """确定性哈希向量: 将 2-gram 映射到固定维度并做 L2 归一化(纯 Python)。"""
    dim = min(settings.embedding_dim, 512)
    vec = [0.0] * dim
    for tok in _tokenize(text):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def _tokenize(text: str) -> list[str]:
    text = text.lower().strip()
    chars = [c for c in text if not c.isspace()]
    grams = ["".join(chars[i : i + 2]) for i in range(len(chars) - 1)]
    words = [w for w in text.split() if w]
    return grams + words if grams else words
