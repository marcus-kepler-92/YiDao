from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# 本地开发加载 .env（生产可以只用系统环境变量）
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    api_prefix_v1: str = "/api/v1"
    # -----------------------
    # 应用
    # -----------------------
    app_name: str = "YiDao"
    app_env: str = "development"  # development / staging / production
    app_host: str = "0.0.0.0"
    app_port: int = 9000
    debug: bool = False
    timezone: str = "Asia/Shanghai"

    # -----------------------
    # PostgreSQL
    # -----------------------
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str
    db_password: str
    db_name: str

    # 可直接从 .env 读取 DATABASE_URL，也可以在下面动态拼接
    database_url: str | None = None

    db_pool_size: int = 10
    db_max_overflow: int = 20

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str | None, info: ValidationInfo):
        # 如果 .env 里已经给了 DATABASE_URL 就直接用
        if v:
            return v

        data = info.data  # 其他字段已解析的值
        user = data.get("db_user")
        password = data.get("db_password")
        host = data.get("db_host", "localhost")
        port = data.get("db_port", 5432)
        name = data.get("db_name")

        if not all([user, password, name]):
            raise ValueError("DATABASE_URL or DB_USER/DB_PASSWORD/DB_NAME must be set")

        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

    # -----------------------
    # Redis
    # -----------------------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None

    redis_db_cache: int = 0
    redis_db_session: int = 1
    redis_db_celery_broker: int = 2
    redis_db_celery_backend: int = 3

    @property
    def redis_base_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def redis_cache_url(self) -> str:
        return f"{self.redis_base_url}/{self.redis_db_cache}"

    @property
    def redis_session_url(self) -> str:
        return f"{self.redis_base_url}/{self.redis_db_session}"

    # -----------------------
    # Celery
    # -----------------------
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v: str | None, info: ValidationInfo):
        if v:
            return v

        data = info.data
        host = data.get("redis_host", "localhost")
        port = data.get("redis_port", 6379)
        db = data.get("redis_db_celery_broker", 2)
        password = data.get("redis_password")
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v: str | None, info: ValidationInfo):
        if v:
            return v

        data = info.data
        host = data.get("redis_host", "localhost")
        port = data.get("redis_port", 6379)
        db = data.get("redis_db_celery_backend", 3)
        password = data.get("redis_password")
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    celery_task_always_eager: bool = False
    celery_task_soft_time_limit: int = 30
    celery_task_time_limit: int = 60

    # -----------------------
    # JWT / 安全
    # -----------------------
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 30 * 24 * 60
    password_hash_scheme: str = "bcrypt"

    # -----------------------
    # CORS（用 pydantic 原生 JSON 解析）
    # -----------------------
    cors_allow_origins: List[str] = []
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    cors_allow_headers: List[str] = ["Authorization", "Content-Type"]
    cors_allow_credentials: bool = True

    # -----------------------
    # 日志 / 监控
    # -----------------------
    log_level: str = "INFO"
    log_json: bool = False

    enable_metrics: bool = True
    prometheus_metrics_path: str = "/metrics"

    # Tracing
    enable_tracing: bool = True
    otlp_endpoint: str = "http://localhost:4317"

    # -----------------------
    # Rate Limiting
    # -----------------------
    enable_rate_limit: bool = True
    rate_limit_default: str = "200/minute"  # Default rate limit per IP

    # -----------------------
    # AI / LLM
    # -----------------------
    llm_provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # -----------------------
    # Langfuse
    # -----------------------
    langfuse_enabled: bool = True
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "http://localhost:3100"

    # -----------------------
    # pydantic Settings 配置
    # -----------------------
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
