"""
用户偏好学习服务。

算法（轻量 TF-IDF 余弦相似度）：
  1. 收集评分大于一定阈值的论文作为"正样本"
  2. 对正样本标题+摘要做 TF-IDF 向量化
  3. 对待评分论文计算与正样本的平均余弦相似度作为偏好分
  4. 若无历史评分，所有论文返回 0.0 (均等)

token 效率考量：
  - 纯本地计算，不调用任何 LLM API
  - 只在拿到筛选候选池后调用一次，而非逐篇调用
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.arxiv_service import RawPaper
    from app.models.db_models import Paper


def compute_preference_scores(
    candidates: list["RawPaper"],
    rated_papers: list["Paper"],
    positive_threshold: int = 1,
) -> dict[str, float]:
    """
    返回 {paper_id: preference_score}，分数越高越受用户偏好。

    Args:
        candidates: 待排序的候选论文（来自 ArXiv)
        rated_papers: 数据库中有用户评分的论文
        positive_threshold: rating >= 此值视为正样本
    """
    positive = [
        p for p in rated_papers
        if p.user_rating is not None and p.user_rating >= positive_threshold
    ]

    scores = {p.id: 0.0 for p in candidates}

    if not positive or not candidates:
        return scores

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        pos_texts = [f"{p.title} {p.abstract}" for p in positive]
        cand_texts = [f"{p.title} {p.abstract}" for p in candidates]

        vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        all_texts = pos_texts + cand_texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        pos_matrix = tfidf_matrix[: len(pos_texts)]
        cand_matrix = tfidf_matrix[len(pos_texts) :]

        # shape: (n_candidates, n_positive)
        sim_matrix = cosine_similarity(cand_matrix, pos_matrix)
        mean_scores = sim_matrix.mean(axis=1)  # average similarity to positives

        for paper, score in zip(candidates, mean_scores):
            scores[paper.id] = float(score)

    except Exception:
        pass  # fallback: all zeros

    return scores
