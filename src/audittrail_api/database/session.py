"""Async database engine and session lifecycle."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from audittrail_api.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped database session."""

    async with session_factory() as session:
        yield session


async def create_schema() -> None:
    """Create tables for local development and disposable tests."""

    from audittrail_api.database import models  # noqa: F401
    from audittrail_api.database.base import Base

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Release pooled database connections during shutdown."""

    await engine.dispose()
