from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


# ─── Paper ───────────────────────────────────────────────────────────────────

class PaperBase(BaseModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    categories: list[str] = Field(default_factory=list)
    published: Optional[datetime] = None
    url: str = ""
    pdf_url: str = ""
    comment: Optional[str] = None


class PaperOut(PaperBase):
    summary: Optional[str] = None
    ai_score: Optional[float] = None
    user_rating: Optional[int] = None
    summary_clicks: int = 0
    source_clicks: int = 0
    last_clicked_at: Optional[datetime] = None
    fetch_date: Optional[date] = None
    is_selected: bool = False
    is_disliked: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RateRequest(BaseModel):
    rating: int = Field(..., ge=0, le=5)

class DislikeRequest(BaseModel):
    is_disliked: bool


class PaperClickRequest(BaseModel):
    target: str = Field(..., pattern="^(summary|source)$")



# ─── Settings ────────────────────────────────────────────────────────────────

class ProviderConfig(BaseModel):
    model: str = "none"
    api_key: Optional[str] = ""
    base_url: Optional[str] = ""
    available_models: list[str] = Field(default_factory=list)


class ProviderConfigPublic(BaseModel):
    model: str = "none"
    base_url: Optional[str] = ""
    available_models: list[str] = Field(default_factory=list)
    has_api_key: bool = False


class ProviderConfigUpdate(BaseModel):
    model: Optional[str] = None
    api_key: Optional[str] = None
    clear_api_key: bool = False
    base_url: Optional[str] = None
    available_models: Optional[list[str]] = None


class SettingsOut(BaseModel):
    llm_provider: str
    llm_max_tokens: int
    llm_concurrency: int
    llm_wait_seconds: int
    providers: dict[str, ProviderConfigPublic]
    arxiv_categories: list[str]
    arxiv_max_results: int
    arxiv_days: int
    papers_per_day: int
    keywords: list[str]
    auto_fetch_enabled: bool
    auto_fetch_cron: str


class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_max_tokens: Optional[int] = None
    llm_concurrency: Optional[int] = None
    llm_wait_seconds: Optional[int] = None
    providers: Optional[dict[str, ProviderConfigUpdate]] = None
    arxiv_categories: Optional[list[str]] = None
    arxiv_max_results: Optional[int] = Field(default=None, le=3000)
    arxiv_days: Optional[int] = Field(default=None, le=7)
    papers_per_day: Optional[int] = Field(default=None, le=200)
    keywords: Optional[list[str]] = None
    auto_fetch_enabled: Optional[bool] = None
    auto_fetch_cron: Optional[str] = None


# ─── Fetch ───────────────────────────────────────────────────────────────────

class FetchLogOut(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    fetched_count: int
    selected_count: int
    error: Optional[str] = None

    model_config = {"from_attributes": True}


class FetchStatusOut(BaseModel):
    running: bool
    last_log: Optional[FetchLogOut] = None
