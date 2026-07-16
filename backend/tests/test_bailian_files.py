import asyncio
import hashlib
from types import SimpleNamespace

import pytest

from app.services import bailian_files


def _response(data):
    return SimpleNamespace(body=SimpleNamespace(data=data))


def _configure(monkeypatch):
    monkeypatch.setattr(bailian_files.settings, "alibaba_cloud_access_key_id", "ak")
    monkeypatch.setattr(
        bailian_files.settings, "alibaba_cloud_access_key_secret", "secret"
    )
    monkeypatch.setattr(bailian_files.settings, "bailian_workspace_id", "ws")
    monkeypatch.setattr(bailian_files.settings, "bailian_file_poll_interval_seconds", 0)
    monkeypatch.setattr(bailian_files.settings, "bailian_file_ready_timeout_seconds", 1)


def test_upload_session_file_uses_sdk_and_waits_until_ready(monkeypatch, tmp_path):
    _configure(monkeypatch)
    path = tmp_path / "proof.md"
    path.write_bytes(b"attachment proof")
    calls = []

    class FakeClient:
        def apply_file_upload_lease(self, category_id, workspace_id, request):
            calls.append(("lease", category_id, workspace_id, request))
            return _response(
                SimpleNamespace(
                    file_upload_lease_id="lease-1",
                    param=SimpleNamespace(
                        method="PUT",
                        url="https://upload.example.test/file",
                        headers={"X-bailian-extra": "signed"},
                    ),
                )
            )

        def add_file(self, workspace_id, request):
            calls.append(("add", workspace_id, request))
            return _response(SimpleNamespace(file_id="file_session_123"))

        def describe_file(self, workspace_id, file_id, request):
            calls.append(("describe", workspace_id, file_id, request))
            status = "PARSING" if len([c for c in calls if c[0] == "describe"]) == 1 else "FILE_IS_READY"
            return _response(SimpleNamespace(status=status, parse_error_message=None))

    uploads = []
    monkeypatch.setattr(bailian_files, "_make_client", lambda: FakeClient())
    monkeypatch.setattr(
        bailian_files,
        "_upload_binary",
        lambda method, url, headers, file_path: uploads.append(
            (method, url, headers, file_path)
        ),
    )

    file_id = asyncio.run(
        bailian_files.upload_session_file(str(path), "proof.md")
    )

    assert file_id == "file_session_123"
    lease_request = calls[0][3]
    assert calls[0][1:3] == ("default", "ws")
    assert lease_request.category_type == "SESSION_FILE"
    assert lease_request.file_name == "proof.md"
    assert lease_request.md_5 == hashlib.md5(b"attachment proof").hexdigest()
    assert lease_request.size_in_bytes == str(len(b"attachment proof"))
    assert uploads == [
        (
            "PUT",
            "https://upload.example.test/file",
            {"X-bailian-extra": "signed"},
            path,
        )
    ]
    add_request = calls[1][2]
    assert add_request.category_id == "default"
    assert add_request.category_type == "SESSION_FILE"
    assert add_request.lease_id == "lease-1"
    assert len([c for c in calls if c[0] == "describe"]) == 2


def test_upload_session_file_rejects_non_session_file_id(monkeypatch, tmp_path):
    _configure(monkeypatch)
    path = tmp_path / "proof.txt"
    path.write_text("proof", encoding="utf-8")

    class FakeClient:
        def apply_file_upload_lease(self, category_id, workspace_id, request):
            return _response(
                SimpleNamespace(
                    file_upload_lease_id="lease-1",
                    param=SimpleNamespace(method="PUT", url="https://upload", headers={}),
                )
            )

        def add_file(self, workspace_id, request):
            return _response(SimpleNamespace(file_id="ordinary-uuid"))

    monkeypatch.setattr(bailian_files, "_make_client", lambda: FakeClient())
    monkeypatch.setattr(bailian_files, "_upload_binary", lambda *args: None)

    with pytest.raises(bailian_files.BailianFileError, match="file_session_"):
        asyncio.run(bailian_files.upload_session_file(str(path), "proof.txt"))


def test_upload_session_file_surfaces_parse_failure(monkeypatch, tmp_path):
    _configure(monkeypatch)
    path = tmp_path / "proof.txt"
    path.write_text("proof", encoding="utf-8")

    class FakeClient:
        def apply_file_upload_lease(self, category_id, workspace_id, request):
            return _response(
                SimpleNamespace(
                    file_upload_lease_id="lease-1",
                    param=SimpleNamespace(method="PUT", url="https://upload", headers={}),
                )
            )

        def add_file(self, workspace_id, request):
            return _response(SimpleNamespace(file_id="file_session_123"))

        def describe_file(self, workspace_id, file_id, request):
            return _response(
                SimpleNamespace(status="PARSE_FAILED", parse_error_message="bad file")
            )

    monkeypatch.setattr(bailian_files, "_make_client", lambda: FakeClient())
    monkeypatch.setattr(bailian_files, "_upload_binary", lambda *args: None)

    with pytest.raises(bailian_files.BailianFileError, match="bad file"):
        asyncio.run(bailian_files.upload_session_file(str(path), "proof.txt"))
