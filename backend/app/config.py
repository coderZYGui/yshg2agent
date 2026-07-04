from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "隐私合规智能评审"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 1440
    algorithm: str = "HS256"

    database_url: str = ""

    vector_backend: str = ""  # pgvector | memory | ""(auto)

    llm_provider: str = "minimax"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.minimaxi.com/v1"
    llm_model: str = "MiniMax-M1"
    llm_vision_model: str = "MiniMax-VL"

    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = "bge-m3"
    embedding_dim: int = 1024

    storage_backend: str = "local"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "compliance"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"

    @property
    def resolved_vector_backend(self) -> str:
        if self.vector_backend:
            return self.vector_backend
        # auto: 使用 postgres 时启用 pgvector, 否则内存降级
        return "pgvector" if self.resolved_database_url.startswith("postgresql") else "memory"

    @property
    def llm_is_mock(self) -> bool:
        return not self.llm_api_key

    @property
    def embedding_is_local(self) -> bool:
        return not self.embedding_api_key

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
