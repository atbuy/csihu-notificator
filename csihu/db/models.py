import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import declarative_base

from csihu.settings import get_settings


def get_engine_url() -> str:
    """Get the database URL."""

    settings = get_settings()
    driver = "postgresql+asyncpg"
    url = (
        f"{driver}://{settings.postgres_user}:{settings.postgres_pass}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )
    return url


def get_engine() -> AsyncEngine:
    """Get the engine for the database."""

    engine_url = get_engine_url()
    return create_async_engine(engine_url, echo=False)


async def create_all_tables():
    """Create all the tables in the database if they don't exist."""

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


Base = declarative_base()


metadata = sa.MetaData()
Base = declarative_base(metadata=metadata)


class AnnouncementsORM(Base):
    __tablename__ = "announcement"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    link = Column(String(100), nullable=False)
