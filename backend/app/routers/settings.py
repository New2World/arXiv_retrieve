from fastapi import APIRouter

from app.models.schemas import SettingsOut, SettingsUpdate
from app.services.settings_service import get_public_settings, update_settings as apply_settings_update

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings():
    return get_public_settings()


@router.put("", response_model=SettingsOut)
async def update_settings(body: SettingsUpdate):
    return apply_settings_update(body)


@router.get("/llm-models")
async def llm_models():
    settings_out = get_public_settings()
    return {k: v.available_models for k, v in settings_out.providers.items()}
