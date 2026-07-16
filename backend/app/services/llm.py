"""LLM provider layer."""

import asyncio
import json
from collections.abc import AsyncIterator
from http import HTTPStatus

import httpx
from dashscope import Application

from ..config import settings
from . import bailian_files


async def stream_chat(
    system_prompt: str,
    user_prompt: str,
    images: list[str] | None = None,
    session_file_ids: list[str] | None = None,
    mock_payload: dict | None = None,
) -> AsyncIterator[str]:
    if settings.llm_is_mock:
        async for tok in _mock_stream(mock_payload or {}):
            yield tok
        return
    if settings.llm_provider == "dashscope_app":
        async for tok in _dashscope_app_stream(
            system_prompt, user_prompt, images, session_file_ids
        ):
            yield tok
        return
    async for tok in _minimax_stream(system_prompt, user_prompt, images):
        yield tok


async def upload_session_file(path: str, filename: str, mime: str = "") -> str | None:
    if settings.llm_is_mock:
        return None
    return await bailian_files.upload_session_file(path, filename)


def _join_prompts(system_prompt: str, user_prompt: str) -> str:
    return f"{system_prompt}\n\n{user_prompt}".strip()


def _dashscope_text(obj: dict) -> str:
    output = obj.get("output")
    if isinstance(output, dict):
        text = output.get("text")
        if isinstance(text, str):
            return text

    choices = obj.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0]
        delta = choice.get("delta") if isinstance(choice, dict) else None
        if isinstance(delta, dict) and isinstance(delta.get("content"), str):
            return delta["content"]

    return ""


async def _dashscope_app_stream(
    system_prompt: str,
    user_prompt: str,
    images: list[str] | None,
    session_file_ids: list[str] | None,
) -> AsyncIterator[str]:
    options: dict = {
        "api_key": settings.dashscope_api_key,
        "app_id": settings.dashscope_app_id,
        "prompt": _join_prompts(system_prompt, user_prompt),
        "stream": True,
        "incremental_output": True,
        "has_thoughts": False,
        "enable_thinking": False,
    }
    if images:
        options["image_list"] = images
    if session_file_ids:
        options["rag_options"] = {"session_file_ids": session_file_ids}
    if settings.dashscope_model_id:
        options["model_id"] = settings.dashscope_model_id

    responses = await asyncio.to_thread(Application.call, **options)
    iterator = iter(responses)
    sentinel = object()
    while True:
        response = await asyncio.to_thread(next, iterator, sentinel)
        if response is sentinel:
            break
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError(
                "DashScope application request failed: "
                f"request_id={response.request_id}, "
                f"code={response.status_code}, message={response.message}"
            )
        text = getattr(response.output, "text", "")
        if text:
            yield text


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
    question: str = payload.get("question", "")
    has_doc: bool = payload.get("has_doc", False)

    items = [
        {
            "risk_level": "medium",
            "location": "附件或描述内容" if has_doc else f"咨询问题: {question[:30]}",
            "verdict": "Mock 模式未调用百炼，仅用于本地联调。",
            "suggestion": "配置 DASHSCOPE_API_KEY 与 DASHSCOPE_APP_ID 后将调用百炼应用。",
            "citations": [],
        }
    ]
    summary = "[Mock 模式] 当前未配置百炼应用，已返回本地演示结果。"
    result = {"summary": summary, "items": items}
    text = json.dumps(result, ensure_ascii=False)
    step = 24
    for i in range(0, len(text), step):
        yield text[i : i + step]
