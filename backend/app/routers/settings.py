"""
Settings 路由：读取 / 更新应用配置。

设计：运行时修改会写入 .env 文件，并热更新 settings 对象。
"""
import os
from fastapi import APIRouter
from app.config import settings, APP_CONFIG_FILE
import json
from app.models.schemas import SettingsOut, SettingsUpdate
from dotenv import set_key
from app.services.scheduler import update_scheduler_job

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings():
    return SettingsOut(
        llm_provider=settings.llm_provider,
        llm_max_tokens=settings.llm_max_tokens,
        llm_concurrency=settings.llm_concurrency,
        llm_wait_seconds=settings.llm_wait_seconds,
        providers=settings.providers,
        arxiv_categories=settings.arxiv_categories,
        arxiv_max_results=settings.arxiv_max_results,
        arxiv_days=settings.arxiv_days,
        papers_per_day=settings.papers_per_day,
        keywords=settings.keywords,
        summaries_dir=settings.summaries_dir,
        auto_fetch_enabled=settings.auto_fetch_enabled,
        auto_fetch_cron=settings.auto_fetch_cron,
    )


@router.put("", response_model=SettingsOut)
async def update_settings(body: SettingsUpdate):
    """热更新 settings 对象，提取密钥至 .env 文件并持久化结构到 config.json 文件。"""
    updates = body.model_dump(exclude_none=True)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    
    # Update in-memory settings
    for key in updates.keys():
        if key == "providers":
            new_providers = getattr(body, key)
            for pk, pv in new_providers.items():
                if pv.api_key and pv.api_key != "ENV_MAPPED":
                    env_key = f"{pk.upper()}_API_KEY"
                    set_key(env_path, env_key, pv.api_key)
            setattr(settings, key, new_providers)
        else:
            setattr(settings, key, getattr(body, key))
        
    # Write ALL settings to JSON
    if os.path.dirname(APP_CONFIG_FILE):
        os.makedirs(os.path.dirname(APP_CONFIG_FILE), exist_ok=True)
        
    dumped = settings.model_dump()
    if "providers" in dumped:
        for pk, pv in dumped["providers"].items():
            pv["api_key"] = "ENV_MAPPED"
            
    with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dumped, f, indent=4, ensure_ascii=False)
        
    # Hot-reload the background task execution daemon using exactly these new configurations
    update_scheduler_job(settings)

    return await get_settings()


@router.get("/llm-models")
async def llm_models():
    """返回各 provider 的常用模型列表，供前端展示。"""
    return {k: v.available_models for k, v in settings.providers.items()}

