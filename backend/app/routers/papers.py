from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import Paper
from app.models.schemas import PaperOut, RateRequest, DislikeRequest

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=list[PaperOut])
async def list_papers(
    fetch_date: Optional[date] = Query(None, description="Filter by fetch date (YYYY-MM-DD)"),
    selected_only: bool = Query(True, description="Only return top-N selected papers"),
    latest_fetch: bool = Query(False, description="Filter universally down exclusively to the maximum recorded chronologic boundary."),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Paper).order_by(desc(Paper.ai_score), desc(Paper.published))
    if latest_fetch:
        from sqlalchemy import func
        max_date_res = await db.execute(select(func.max(Paper.fetch_date)))
        max_date = max_date_res.scalar()
        if max_date:
            stmt = stmt.where(Paper.fetch_date == max_date)
    elif fetch_date:
        stmt = stmt.where(Paper.fetch_date == fetch_date)
        
    if selected_only:
        stmt = stmt.where(Paper.is_selected == True)
        
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{paper_id}", response_model=PaperOut)
async def get_paper(paper_id: str, db: AsyncSession = Depends(get_db)):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.post("/{paper_id}/rate", response_model=PaperOut)
async def rate_paper(
    paper_id: str,
    body: RateRequest,
    db: AsyncSession = Depends(get_db),
):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    paper.user_rating = body.rating
    await db.commit()
    await db.refresh(paper)
    return paper


@router.put("/{paper_id}/dislike", response_model=PaperOut)
async def toggle_dislike(
    paper_id: str,
    body: DislikeRequest,
    db: AsyncSession = Depends(get_db),
):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    paper.is_disliked = body.is_disliked
    await db.commit()
    await db.refresh(paper)
    return paper


@router.get("/history/dates")
async def list_dates(db: AsyncSession = Depends(get_db)):
    """返回有论文记录的日期列表，供历史页面使用。"""
    result = await db.execute(
        select(Paper.fetch_date)
        .where(Paper.fetch_date.is_not(None))
        .distinct()
        .order_by(desc(Paper.fetch_date))
    )
    dates = [row[0].isoformat() for row in result.all() if row[0]]
    return {"dates": dates}
