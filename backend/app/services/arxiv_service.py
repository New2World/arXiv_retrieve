"""
ArXiv 论文抓取服务。

策略：先多抓（max_results），再交给 filter_service 精选。
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Reuse one client so arxiv.py can keep its internal last-request timestamp
# across fetches; otherwise a fresh client can skip the initial delay and hit
# the API too aggressively on back-to-back runs.
_ARXIV_CLIENT = arxiv.Client(page_size=100, delay_seconds=3, num_retries=3)
_ARXIV_CLIENT_LOCK = asyncio.Lock()
_ARXIV_PAGE_SIZE_CAP = 1000


@dataclass
class RawPaper:
    id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published: Optional[datetime]
    url: str
    pdf_url: str
    comment: Optional[str]


def _collect_recent_papers(
    search: arxiv.Search,
    cutoff: datetime,
) -> list[RawPaper]:
    papers: list[RawPaper] = []

    for result in _ARXIV_CLIENT.results(search):
        pub = result.published
        if pub and pub.replace(tzinfo=timezone.utc) < cutoff:
            break  # results sorted desc -> stop early
        papers.append(
            RawPaper(
                id=result.get_short_id(),
                title=result.title.strip(),
                authors=[a.name for a in result.authors],
                abstract=result.summary.strip(),
                categories=result.categories,
                published=pub,
                url=result.entry_id,
                pdf_url=result.pdf_url or "",
                comment=result.comment,
            )
        )

    return papers


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
async def fetch_recent_papers(
    categories: list[str],
    hours: int = 24,
    max_results: int = 200,
) -> list[RawPaper]:
    """
    从 ArXiv 抓取指定分类在最近 hours 小时内提交的论文。

    优先把 submittedDate 时间窗口下推到查询条件里，减少无效翻页；
    同时保留本地 cutoff 作为兜底过滤。
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)
    category_query = " OR ".join(f"cat:{c}" for c in categories)
    submitted_range = f"submittedDate:[{cutoff.strftime('%Y%m%d%H%M')} TO {now.strftime('%Y%m%d%H%M')}]"
    query = f"({category_query}) AND {submitted_range}"

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    async with _ARXIV_CLIENT_LOCK:
        page_size = max(1, min(max_results, _ARXIV_PAGE_SIZE_CAP))
        _ARXIV_CLIENT.page_size = page_size
        logger.info(
            "Fetching arXiv papers",
            extra={
                "categories": categories,
                "hours": hours,
                "max_results": max_results,
                "page_size": page_size,
            },
        )
        return await asyncio.to_thread(_collect_recent_papers, search, cutoff)
