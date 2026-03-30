"""
ArXiv 论文抓取服务。

策略：先多抓（max_results），再交给 filter_service 精选。
"""

from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional

import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential


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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_recent_papers(
    categories: list[str],
    hours: int = 24,
    max_results: int = 200,
) -> list[RawPaper]:
    """
    从 ArXiv 抓取指定分类在最近 hours 小时内提交的论文。

    注意：arxiv API 按 SubmittedDate 排序，取前 max_results 条后再按时间窗口过滤。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = " OR ".join(f"cat:{c}" for c in categories)
    client = arxiv.Client(page_size=100, delay_seconds=3, num_retries=3)

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers: list[RawPaper] = []

    def _sync_fetch():
        for result in client.results(search):
            pub = result.published
            if pub and pub.replace(tzinfo=timezone.utc) < cutoff:
                break  # results sorted desc → stop early
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

    await asyncio.to_thread(_sync_fetch)
    return papers
