import asyncio

import pytest
from fastapi import HTTPException

from app.routers import chat, documents
from app.services.bailian_files import BailianFileError


def test_upload_session_files_includes_images(monkeypatch, tmp_path):
    image = tmp_path / "screen.png"
    image.write_bytes(b"png")
    document = tmp_path / "policy.md"
    document.write_text("policy", encoding="utf-8")
    calls = []

    async def fake_upload(path, filename, mime):
        calls.append((path, filename, mime))
        return f"file_session_{len(calls)}"

    monkeypatch.setattr(chat.llm, "upload_session_file", fake_upload)
    docs = [
        {
            "filename": "screen.png",
            "mime": "image/png",
            "storage_path": str(image),
            "is_image": True,
        },
        {
            "filename": "policy.md",
            "mime": "text/markdown",
            "storage_path": str(document),
            "is_image": False,
        },
    ]

    file_ids = asyncio.run(chat._upload_session_files(docs))

    assert file_ids == ["file_session_1", "file_session_2"]
    assert [call[1] for call in calls] == ["screen.png", "policy.md"]


def test_upload_session_files_surfaces_errors(monkeypatch, tmp_path):
    document = tmp_path / "policy.md"
    document.write_text("policy", encoding="utf-8")

    async def fake_upload(path, filename, mime):
        raise BailianFileError("附件解析失败")

    monkeypatch.setattr(chat.llm, "upload_session_file", fake_upload)
    docs = [
        {
            "filename": "policy.md",
            "mime": "text/markdown",
            "storage_path": str(document),
            "is_image": False,
        }
    ]

    with pytest.raises(BailianFileError, match="附件解析失败"):
        asyncio.run(chat._upload_session_files(docs))


def test_attachment_validation_rejects_unsupported_format():
    with pytest.raises(HTTPException, match="不支持的附件格式"):
        documents._validate_attachment("payload.exe", 1024)


def test_attachment_validation_enforces_image_limit():
    with pytest.raises(HTTPException, match="20MB"):
        documents._validate_attachment("screen.png", 20 * 1024 * 1024 + 1)


def test_attachment_validation_accepts_supported_document():
    documents._validate_attachment("policy.pdf", 100 * 1024 * 1024)
