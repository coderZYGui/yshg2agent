"""PII 脱敏层: 调用云端 LLM 前对敏感信息做占位替换。"""

import re

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("[手机号]", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    (
        "[身份证]",
        re.compile(r"(?<!\d)\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"),
    ),
    ("[银行卡]", re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
    ("[邮箱]", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
]


def redact(text: str) -> tuple[str, dict[str, int]]:
    """返回脱敏后的文本与命中统计。"""
    stats: dict[str, int] = {}
    for placeholder, pattern in _PATTERNS:
        matches = pattern.findall(text)
        if matches:
            stats[placeholder] = len(matches)
            text = pattern.sub(placeholder, text)
    return text, stats
