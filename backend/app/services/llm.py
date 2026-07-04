"""LLM Provider 抽象层。

生产: MiniMax(OpenAI 兼容) 流式 chat/completions。
降级: 无 API Key 时使用 Mock, 基于检索上下文生成结构化评审, 保证离线自验证。
"""

import json
from collections.abc import AsyncIterator

import httpx

from ..config import settings


async def stream_chat(
    system_prompt: str,
    user_prompt: str,
    images: list[str] | None = None,
    mock_payload: dict | None = None,
) -> AsyncIterator[str]:
    if settings.llm_is_mock:
        async for tok in _mock_stream(mock_payload or {}):
            yield tok
        return
    async for tok in _minimax_stream(system_prompt, user_prompt, images):
        yield tok


async def _minimax_stream(
    system_prompt: str, user_prompt: str, images: list[str] | None
) -> AsyncIterator[str]:
    content: list | str
    if images:
        content = [{"type": "text", "text": user_prompt}]
        for url in images:
            content.append({"type": "image_url", "image_url": {"url": url}})
    else:
        content = user_prompt

    model = settings.llm_vision_model if images else settings.llm_model
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        "stream": True,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue


async def _mock_stream(payload: dict) -> AsyncIterator[str]:
    """基于检索到的上下文构造一个结构化评审(演示/离线用)。"""
    question: str = payload.get("question", "")
    citations: list[dict] = payload.get("citations", [])
    has_doc: bool = payload.get("has_doc", False)

    cites = [
        {"document": c.get("document", "知识库"), "snippet": c.get("snippet", "")[:80], "score": round(c.get("score", 0.0), 3)}
        for c in citations[:2]
    ]

    items = []
    if citations:
        items.append(
            {
                "risk_level": "medium",
                "location": "个人信息收集环节" if has_doc else f"咨询问题: {question[:30]}",
                "verdict": "根据知识库中的隐私合规要求, 需确认是否遵循最小必要原则并取得明示同意。",
                "suggestion": "补充数据收集清单与用途说明, 在采集前提供独立的同意勾选项, 避免默认勾选。",
                "citations": cites,
            }
        )
        items.append(
            {
                "risk_level": "low",
                "location": "数据存储与传输",
                "verdict": "敏感个人信息需加密存储与传输。",
                "suggestion": "对敏感字段启用加密, 传输链路使用 TLS, 并做好访问审计。",
                "citations": cites[:1],
            }
        )
        summary = f"[Mock 模式] 已比对知识库 {len(citations)} 个相关片段, 识别到 {len(items)} 项待关注的隐私合规风险。"
    else:
        items.append(
            {
                "risk_level": "compliant",
                "location": "-",
                "verdict": "当前知识库中未检索到与该问题直接相关的合规依据。",
                "suggestion": "请先在知识库中上传相关隐私合规文档, 或补充更具体的问题描述。",
                "citations": [],
            }
        )
        summary = "[Mock 模式] 未检索到相关知识库依据, 建议补充资料后重试。"

    result = {"summary": summary, "items": items}
    text = json.dumps(result, ensure_ascii=False)
    # 分块 yield 模拟流式
    step = 24
    for i in range(0, len(text), step):
        yield text[i : i + step]
