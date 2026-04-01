"""
论文筛选服务。

筛选流程（三步漏斗）：
  1. 关键词过滤：标题/摘要包含任一关键词（可选）
  2. 偏好评分：对每篇论文计算 preference_score（由 preference_service 提供）
  3. Top-N 选取：按 preference_score DESC 取前 N 篇
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.arxiv_service import RawPaper


def keyword_filter(papers: list["RawPaper"], keywords: list[str]) -> list["RawPaper"]:
    """
    若 keywords 为空，直接全部通过。
    否则保留 title 或 abstract 中含有任一关键词（大小写不敏感）的论文。
    """
    if not keywords:
        return papers

    normalized_keywords = [k.strip().casefold() for k in keywords if k.strip()]
    if not normalized_keywords:
        return papers

    result = []
    for p in papers:
        text = (p.title + " " + p.abstract).casefold()
        if any(kw in text for kw in normalized_keywords):
            result.append(p)
    return result


def rank_and_select(
    papers: list["RawPaper"],
    preference_scores: dict[str, float],
    top_n: int = 10,
) -> list["RawPaper"]:
    """
    按偏好分数降序排列，取前 top_n 篇。
    preference_scores: {paper_id: score}（score 默认 0.0）
    """
    scored = [(p, preference_scores.get(p.id, 0.0)) for p in papers]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored[:top_n]]
