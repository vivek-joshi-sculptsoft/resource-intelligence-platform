from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs: dict = {
    "echo": settings.DATABASE_ECHO,
}

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10
    # PgBouncer transaction-mode pooling (e.g. Supabase pooler) doesn't support
    # server-side prepared statements — asyncpg must not cache them.
    _engine_kwargs["connect_args"] = {"statement_cache_size": 0}

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    """Create all tables directly (used for SQLite local dev instead of Alembic)."""
    import app.modules.nonhuman_costs.models  # noqa: F401 — register table with Base.metadata
    from app.shared.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
