from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
KNOWLEDGE_INDEX_FILE = KNOWLEDGE_DIR / "chunks.json"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "隐私合规智能评审"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 1440
    access_password: str = "local666"
    algorithm: str = "HS256"

    database_url: str = ""
    vector_backend: str = "local"

    llm_provider: str = "minimax"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.minimaxi.com/v1"
    llm_model: str = "MiniMax-M1"
    llm_vision_model: str = "MiniMax-VL"

    dashscope_api_key: str = ""
    dashscope_app_id: str = ""
    dashscope_model_id: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"

    alibaba_cloud_access_key_id: str = ""
    alibaba_cloud_access_key_secret: str = ""
    bailian_workspace_id: str = ""
    bailian_region_id: str = "cn-beijing"
    bailian_file_poll_interval_seconds: float = 2.0
    bailian_file_ready_timeout_seconds: int = 300

    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = "bge-m3"
    embedding_dim: int = 1024

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"

    @property
    def resolved_vector_backend(self) -> str:
        return self.vector_backend or "local"

    @property
    def llm_is_mock(self) -> bool:
        if self.llm_provider == "dashscope_app":
            return not (self.dashscope_api_key and self.dashscope_app_id)
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
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
