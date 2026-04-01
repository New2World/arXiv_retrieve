from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # await conn.run_sync(_ensure_paper_columns)


# def _ensure_paper_columns(sync_conn) -> None:
#     inspector = inspect(sync_conn)
#     if "papers" not in inspector.get_table_names():
#         return

#     existing_columns = {col["name"] for col in inspector.get_columns("papers")}
#     required_columns = {
#         "summary_clicks": "ALTER TABLE papers ADD COLUMN summary_clicks INTEGER NOT NULL DEFAULT 0",
#         "source_clicks": "ALTER TABLE papers ADD COLUMN source_clicks INTEGER NOT NULL DEFAULT 0",
#         "last_clicked_at": "ALTER TABLE papers ADD COLUMN last_clicked_at DATETIME",
#     }

#     for column_name, ddl in required_columns.items():
#         if column_name not in existing_columns:
#             sync_conn.execute(text(ddl))

#     sync_conn.execute(text("""
#         UPDATE papers
#         SET fetch_date = COALESCE(DATE(created_at), DATE('now'))
#         WHERE fetch_date IS NULL
#     """))


async def get_db():
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
