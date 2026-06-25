from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "SculptNexus"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite+aiosqlite:///./ri_platform.db"
    DATABASE_ECHO: bool = False
    # Used only for Alembic migrations against Supabase — pgbouncer transaction-mode pooling
    # (DATABASE_URL, port 6543) breaks asyncpg's prepared statements during DDL. Use the
    # Supabase *session pooler* (port 5432, same pooler.supabase.com host), NOT the true
    # direct db.<ref>.supabase.co:5432 connection — that one is IPv6-only and unreachable
    # from IPv4-only hosts like Render. Falls back to DATABASE_URL when unset (SQLite, plain Postgres).
    MIGRATION_DATABASE_URL: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_REFRESH_SECRET_KEY: str = "change-me-refresh-in-production"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    SENTRY_DSN: str = ""

    SCHEDULER_BACKEND: str = "apscheduler"

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"


settings = Settings()
