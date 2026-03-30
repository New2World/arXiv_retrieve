import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.db_models import FetchLog
from app.models.schemas import FetchLogOut, FetchStatusOut
from app.services.fetch_orchestrator import run_fetch, is_fetch_running

router = APIRouter(prefix="/fetch", tags=["fetch"])
logger = logging.getLogger(__name__)


async def _background_fetch():
    """在独立 session 中运行 fetch（background task 不共享请求 session）。"""
    async with AsyncSessionLocal() as db:
        await run_fetch(db)


@router.post("/trigger", response_model=FetchStatusOut)
async def trigger_fetch(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    if is_fetch_running():
        raise HTTPException(status_code=409, detail="Fetch already in progress")
    background_tasks.add_task(_background_fetch)
    return FetchStatusOut(running=True)


@router.get("/status", response_model=FetchStatusOut)
async def fetch_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FetchLog).order_by(desc(FetchLog.started_at)).limit(1)
    )
    last_log = result.scalar_one_or_none()
    return FetchStatusOut(
        running=is_fetch_running(),
        last_log=FetchLogOut.model_validate(last_log) if last_log else None,
    )


@router.get("/logs", response_model=list[FetchLogOut])
async def fetch_logs(db: AsyncSession = Depends(get_db), limit: int = 20):
    result = await db.execute(
        select(FetchLog).order_by(desc(FetchLog.started_at)).limit(limit)
    )
    return result.scalars().all()
