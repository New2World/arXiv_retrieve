"""
FastAPI 应用入口。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings as app_settings
from app.database import init_db
from app.services.scheduler import init_scheduler, shutdown_scheduler
from app.routers import papers, fetch, settings
from app.version import APP_VERSION

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    init_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="ArXiv Agent API",
    description="自动抓取 ArXiv 论文、AI 总结、偏好学习",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers.router, prefix="/api")
app.include_router(fetch.router, prefix="/api")
app.include_router(settings.router, prefix="/api")



@app.get("/api/health")
async def health():
    return {"status": "ok", "version": APP_VERSION}
