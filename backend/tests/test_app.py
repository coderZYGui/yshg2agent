import asyncio
import json
from http import HTTPStatus
from types import SimpleNamespace

from app.database import SessionLocal
from app.models import Chunk, Conversation, Message
from app.services import llm, parser
from app.services.redaction import redact


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_mode"] == "mock"


def test_register_login_me(client):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "pw12345", "role": "legal"},
    )
    resp = client.post(
        "/api/auth/login", data={"username": "alice", "password": "pw12345"}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "pm"


def test_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "correct1", "role": "pm"},
    )
    resp = client.post(
        "/api/auth/login", data={"username": "bob", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_seeded_knowledge(client, auth_headers):
    resp = client.get("/api/knowledge", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 4  # 内置知识库样本


def test_conversations_are_available_without_bearer_token(client):
    resp = client.get("/api/conversations")
    assert resp.status_code == 200


def test_chunk_text():
    text = "a" * 1500
    chunks = parser.chunk_text(text, size=600, overlap=100)
    assert len(chunks) >= 3
    assert all(len(c) <= 600 for c in chunks)


def test_redaction():
    text = "联系电话13800138000, 邮箱 test@example.com"
    redacted, stats = redact(text)
    assert "13800138000" not in redacted
    assert "[手机号]" in redacted
    assert "[邮箱]" in redacted
    assert stats["[手机号]"] == 1


def test_dashscope_text_extracts_application_output():
    assert llm._dashscope_text({"output": {"text": "hello"}}) == "hello"
    assert (
        llm._dashscope_text({"choices": [{"delta": {"content": "fallback"}}]})
        == "fallback"
    )
    assert llm._dashscope_text({"output": {}}) == ""


def test_dashscope_sdk_stream_uses_images_and_session_files(monkeypatch):
    calls = []

    class FakeApplication:
        @staticmethod
        def call(**kwargs):
            calls.append(kwargs)
            return iter(
                [
                    SimpleNamespace(
                        status_code=HTTPStatus.OK,
                        output=SimpleNamespace(text="first"),
                    ),
                    SimpleNamespace(
                        status_code=HTTPStatus.OK,
                        output=SimpleNamespace(text=" second"),
                    ),
                ]
            )

    monkeypatch.setattr(llm, "Application", FakeApplication)
    monkeypatch.setattr(llm.settings, "dashscope_model_id", "qwen3.7-max")

    async def collect():
        return [
            token
            async for token in llm._dashscope_app_stream(
                "system", "question", ["data:image/png;base64,abc"], ["file_session_1"]
            )
        ]

    assert asyncio.run(collect()) == ["first", " second"]
    assert calls == [
        {
            "api_key": llm.settings.dashscope_api_key,
            "app_id": llm.settings.dashscope_app_id,
            "prompt": "system\n\nquestion",
            "stream": True,
            "incremental_output": True,
            "has_thoughts": False,
            "enable_thinking": False,
            "image_list": ["data:image/png;base64,abc"],
            "rag_options": {"session_file_ids": ["file_session_1"]},
            "model_id": "qwen3.7-max",
        }
    ]


def test_chat_stream_returns_review(client, auth_headers):
    payload = {
        "role": "pm",
        "message": "我们要收集用户的身份证号和人脸信息用于实名认证, 是否合规?",
        "document_ids": [],
    }
    with client.stream(
        "POST", "/api/chat/stream", json=payload, headers=auth_headers
    ) as resp:
        assert resp.status_code == 200
        raw = "".join(resp.iter_text())

    assert "event: token" in raw
    assert "event: review" in raw
    assert "event: done" in raw

    # 解析 review 事件
    review_data = None
    for block in raw.split("\n\n"):
        if block.startswith("event: review"):
            data_line = [l for l in block.splitlines() if l.startswith("data:")][0]
            review_data = json.loads(data_line[len("data:"):].strip())
    assert review_data is not None
    assert "items" in review_data
    assert len(review_data["items"]) >= 1


def test_chat_stream_does_not_persist_conversation_history(client, auth_headers):
    with SessionLocal() as db:
        conversation_count = db.query(Conversation).count()
        message_count = db.query(Message).count()

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"role": "pm", "message": "请检查这段隐私条款", "document_ids": []},
        headers=auth_headers,
    ) as resp:
        assert resp.status_code == 200
        assert "event: done" in "".join(resp.iter_text())

    with SessionLocal() as db:
        assert db.query(Conversation).count() == conversation_count
        assert db.query(Message).count() == message_count


def test_knowledge_upload_and_retrieve(client, auth_headers):
    content = (
        "本产品在注册环节强制收集用户通讯录和精确定位信息, 且未提供单独同意选项。"
    ).encode("utf-8")
    files = {"file": ("kb_test.md", content, "text/markdown")}
    resp = client.post("/api/knowledge", files=files, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["parse_status"] == "done"


def test_document_upload_does_not_create_local_chunks(client, auth_headers):
    files = {"file": ("prd.md", b"# PRD\ncollect contacts", "text/markdown")}
    resp = client.post(
        "/api/documents/upload",
        data={"kind": "review"},
        files=files,
        headers=auth_headers,
    )
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    with SessionLocal() as db:
        assert db.query(Chunk).filter(Chunk.document_id == doc_id).count() == 0


def test_review_attachment_is_removed_after_chat_finishes(client, auth_headers):
    files = {"file": ("temporary.md", b"temporary review content", "text/markdown")}
    upload = client.post(
        "/api/documents/upload",
        data={"kind": "review"},
        files=files,
        headers=auth_headers,
    )
    assert upload.status_code == 200
    doc_id = upload.json()["id"]
    assert client.get(f"/api/documents/{doc_id}", headers=auth_headers).status_code == 200

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"role": "pm", "message": "请评审附件", "document_ids": [doc_id]},
        headers=auth_headers,
    ) as response:
        assert response.status_code == 200
        assert "event: done" in "".join(response.iter_text())

    assert client.get(f"/api/documents/{doc_id}", headers=auth_headers).status_code == 404
