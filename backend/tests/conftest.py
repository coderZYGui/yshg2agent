import os
import tempfile

os.environ.setdefault("DATABASE_URL", "")  # 使用 SQLite 降级
os.environ.setdefault("LLM_API_KEY", "")  # Mock LLM
os.environ.setdefault("EMBEDDING_API_KEY", "")  # 本地 embedding

# 为测试使用独立临时 SQLite 库, 避免污染开发库
_tmp = tempfile.mkdtemp(prefix="compliance_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/api/auth/register",
        json={"username": "tester", "password": "test123", "role": "pm"},
    )
    resp = client.post(
        "/api/auth/login", data={"username": "tester", "password": "test123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
