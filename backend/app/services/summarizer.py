"""
论文总结服务。

Token 效率设计：
  1. 先筛选，后总结：只对最终选出的 Top-N 篇调用 LLM
  2. 复用已保存的 summary：若数据库已有 summary 则跳过
  3. 使用精简 prompt：结构化输出，控制 max_tokens
  4. 并发总结（asyncio.gather）但限制并发数避免限流
"""

from __future__ import annotations
import asyncio
import os
from datetime import date, datetime
from typing import TYPE_CHECKING
import httpx
import fitz

if TYPE_CHECKING:
    from app.services.llm.base import BaseLLMClient
    from app.services.arxiv_service import RawPaper

# Token-efficient Chinese summary prompt
_SUMMARY_SYSTEM = (
    """你是一位 AI 研究助理，擅长用精炼的中文总结计算机领域学术论文。**输出格式固定，不要添加额外内容**。"""
)

_SUMMARY_TEMPLATE = """\
标题：{title}
原文：
{full_text}
---
请根据论文，**严格按照**以下格式进行总结，保证内容完整前提下尽量简洁：

**研究背景与动机**：（解决了什么问题，为什么重要）

**核心贡献**：（与已有论文相比，提出了什么新东西）

**方法**：（怎么解决的）

**主要结果**：（取得了什么成果）
"""


async def _extract_pdf_text(pdf_url: str) -> str:
    """Download and extract the text content of an ArXiv PDF file asynchronously."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(pdf_url, timeout=20.0, follow_redirects=True)
            resp.raise_for_status()
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=resp.content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        print(f"Failed to extract PDF {pdf_url}: {e}")
        return ""


async def summarize_paper(
    paper: "RawPaper",
    llm: "BaseLLMClient",
    max_tokens: int = 800,
) -> str:
    """调用 LLM 生成单篇论文的中文总结。"""
    # Fetch full text from ArXiv PDF
    full_text = await _extract_pdf_text(paper.pdf_url)
    if not full_text.strip():
        full_text = f"无法抓取全文，仅提供摘要参考：\n{paper.abstract}"
    
    # Cap string length at 40,000 characters to prevent huge token cascades while summarizing
    full_text = full_text[:40000]

    prompt = _SUMMARY_TEMPLATE.format(
        title=paper.title,
        full_text=full_text,
    )

    messages = [
        {"role": "system", "content": _SUMMARY_SYSTEM},
        {"role": "user", "content": prompt},
    ]

    return await llm.complete(messages, max_tokens=max_tokens)


async def summarize_batch(
    papers: list["RawPaper"],
    llm: "BaseLLMClient",
    max_tokens: int = 800,
    concurrency: int = 1,
    wait_seconds: int = 10,
) -> dict[str, str]:
    """
    进行批量论文总结，支持并发限制及每个请求结束后的强制定时休眠防封禁。
    
    Returns:
        {paper_id: summary_text}
    """
    sem = asyncio.Semaphore(concurrency)
    results: dict[str, str] = {}

    async def _safe_summarize(paper: "RawPaper"):
        async with sem:
            for attempt in range(3):
                try:
                    summary = await summarize_paper(paper, llm, max_tokens)
                    results[paper.id] = summary
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt == 2:  # Last attempt failed
                        results[paper.id] = f"[总结失败: {e}]"
                        break
                        
                    err_str = str(e).lower()
                    if "429" in err_str or "too many requests" in err_str:
                        # 触发 429 频率限制时，立刻按照用户界面的休眠时长进行退避
                        await asyncio.sleep(wait_seconds if wait_seconds > 0 else 5)
                    else:
                        # 其他非常规网络异常情况，退避 2 秒或 4 秒
                        await asyncio.sleep(2 ** (attempt + 1))
                        
            # 单篇论文彻底处理完成后（无论最终成功还是绝对失败），均保底执行标准冷却休眠
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

    await asyncio.gather(*[_safe_summarize(p) for p in papers])
    return results


