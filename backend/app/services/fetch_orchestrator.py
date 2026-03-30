"""
论文抓取编排器（Orchestrator）。

将 arxiv_service / filter_service / preference_service / summarizer 串联起来，
对外暴露单一的 run_fetch() 函数，供 router 和定时任务调用。
"""

from __future__ import annotations
import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as _default_settings
from app.models.db_models import Paper, FetchLog
from app.services.arxiv_service import fetch_recent_papers
from app.services.filter_service import keyword_filter, rank_and_select
from app.services.preference_service import compute_preference_scores
from app.services.summarizer import summarize_batch
from app.services.llm.factory import create_llm_client

logger = logging.getLogger(__name__)

_fetch_running = False


def is_fetch_running() -> bool:
    return _fetch_running


async def run_fetch(db: AsyncSession, cfg=None) -> FetchLog:
    """
    完整的日报生成流程：
      1. 从 ArXiv 拉取论文
      2. 关键词过滤
      3. 偏好评分 + Top-N 选取
      4. LLM 总结（跳过已总结的）
      5. 写入数据库
      6. 生成 markdown 文件
    """
    global _fetch_running
    if _fetch_running:
        raise RuntimeError("Already fetching")

    _fetch_running = True
    s = cfg or _default_settings

    log = FetchLog(started_at=datetime.utcnow(), status="running")
    db.add(log)
    await db.commit()
    await db.refresh(log)

    try:
        from sqlalchemy import delete
        await db.execute(delete(Paper).where(Paper.is_disliked == True))
        
        # 1. Fetch
        logger.info("Fetching ArXiv papers...")
        raw_papers = await fetch_recent_papers(
            categories=s.arxiv_categories,
            hours=s.arxiv_days * 24,
            max_results=s.arxiv_max_results,
        )
        log.fetched_count = len(raw_papers)
        logger.info(f"Fetched {len(raw_papers)} papers")

        # 2. Keyword filter
        filtered = keyword_filter(raw_papers, s.keywords)
        logger.info(f"After keyword filter: {len(filtered)} papers")

        # 3. Preference scoring + Top-N
        rated_result = await db.execute(
            select(Paper).where(Paper.user_rating.is_not(None))
        )
        rated_papers = list(rated_result.scalars().all())

        pref_scores = compute_preference_scores(filtered, rated_papers)
        selected = rank_and_select(filtered, pref_scores, top_n=s.papers_per_day)
        logger.info(f"Selected top {len(selected)} papers")

        # 4. Summarize (skip already summarized papers in DB)
        existing_ids_result = await db.execute(
            select(Paper.id, Paper.summary).where(Paper.id.in_([p.id for p in selected]))
        )
        existing = {row.id: row.summary for row in existing_ids_result}

        to_summarize = [p for p in selected if not existing.get(p.id)]
        summaries: dict[str, str] = {}

        if to_summarize:
            llm = create_llm_client(s)
            logger.info(f"Summarizing {len(to_summarize)} papers with {llm.provider_name}...")
            summaries = await summarize_batch(
                to_summarize,
                llm,
                max_tokens=s.llm_max_tokens,
                concurrency=s.llm_concurrency,
                wait_seconds=s.llm_wait_seconds,
            )

        today = date.today()

        # 5. Upsert papers into DB
        for paper in selected:
            summary = summaries.get(paper.id) or existing.get(paper.id)
            existing_row = await db.get(Paper, paper.id)
            if existing_row:
                existing_row.summary = summary or existing_row.summary
                existing_row.ai_score = pref_scores.get(paper.id, 0.0)
                existing_row.is_selected = True
                existing_row.fetch_date = today
            else:
                db.add(Paper(
                    id=paper.id,
                    title=paper.title,
                    authors=paper.authors,
                    abstract=paper.abstract,
                    categories=paper.categories,
                    published=paper.published,
                    url=paper.url,
                    pdf_url=paper.pdf_url,
                    comment=paper.comment,
                    summary=summary,
                    ai_score=pref_scores.get(paper.id, 0.0),
                    fetch_date=today,
                    is_selected=True,
                ))


        log.status = "done"
        log.selected_count = len(selected)
        log.finished_at = datetime.utcnow()

    except Exception as e:
        logger.exception("Fetch failed")
        log.status = "error"
        log.error = str(e)
        log.finished_at = datetime.utcnow()

    finally:
        _fetch_running = False
        await db.commit()
        await db.refresh(log)

    return log
