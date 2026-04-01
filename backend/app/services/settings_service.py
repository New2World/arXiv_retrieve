import json
from pathlib import Path

from dotenv import set_key, unset_key

from app.config import APP_CONFIG_FILE, ENV_FILE, settings
from app.models.schemas import (
    ProviderConfig,
    ProviderConfigPublic,
    ProviderConfigUpdate,
    SettingsOut,
    SettingsUpdate,
)
from app.services.scheduler import update_scheduler_job


def _default_api_key(provider_name: str) -> str:
    return "ollama" if provider_name == "ollama" else "none"


def _env_key(provider_name: str) -> str:
    return f"{provider_name.upper()}_API_KEY"


def _has_api_key(provider_name: str, provider: ProviderConfig) -> bool:
    return provider.api_key not in ("", None, "none", _default_api_key(provider_name))


def get_public_settings() -> SettingsOut:
    providers = {
        name: ProviderConfigPublic(
            model=provider.model,
            base_url=provider.base_url,
            available_models=list(provider.available_models),
            has_api_key=_has_api_key(name, provider),
        )
        for name, provider in settings.providers.items()
    }

    return SettingsOut(
        llm_provider=settings.llm_provider,
        llm_max_tokens=settings.llm_max_tokens,
        llm_concurrency=settings.llm_concurrency,
        llm_wait_seconds=settings.llm_wait_seconds,
        providers=providers,
        arxiv_categories=settings.arxiv_categories,
        arxiv_max_results=settings.arxiv_max_results,
        arxiv_days=settings.arxiv_days,
        papers_per_day=settings.papers_per_day,
        keywords=settings.keywords,
        auto_fetch_enabled=settings.auto_fetch_enabled,
        auto_fetch_cron=settings.auto_fetch_cron,
    )


def _merge_provider_update(
    provider_name: str,
    current: ProviderConfig,
    incoming: ProviderConfigUpdate,
) -> ProviderConfig:
    api_key = current.api_key
    if incoming.clear_api_key:
        api_key = _default_api_key(provider_name)
    elif incoming.api_key is not None and incoming.api_key.strip():
        api_key = incoming.api_key.strip()

    return ProviderConfig(
        model=incoming.model if incoming.model is not None else current.model,
        api_key=api_key,
        base_url=incoming.base_url if incoming.base_url is not None else current.base_url,
        available_models=(
            incoming.available_models
            if incoming.available_models is not None
            else list(current.available_models)
        ),
    )


def _persist_provider_secrets() -> None:
    env_path = Path(ENV_FILE)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.touch(exist_ok=True)

    for provider_name, provider in settings.providers.items():
        env_key = _env_key(provider_name)
        if _has_api_key(provider_name, provider):
            set_key(str(env_path), env_key, provider.api_key or "")
        else:
            unset_key(str(env_path), env_key)


def _persist_app_config() -> None:
    APP_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    dumped = settings.model_dump()
    providers = {}
    for provider_name, provider in dumped["providers"].items():
        provider_dump = dict(provider)
        provider_dump.pop("api_key", None)
        providers[provider_name] = provider_dump

    dumped["providers"] = providers

    with APP_CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(dumped, f, indent=4, ensure_ascii=False)


def update_settings(body: SettingsUpdate) -> SettingsOut:
    updates = body.model_dump(exclude_none=True)
    provider_updates = body.providers

    for key, value in updates.items():
        if key == "providers":
            merged_providers = {}
            for provider_name, current_provider in settings.providers.items():
                incoming = provider_updates.get(provider_name) if provider_updates is not None else None
                merged_providers[provider_name] = (
                    _merge_provider_update(provider_name, current_provider, incoming)
                    if incoming is not None
                    else current_provider
                )
            settings.providers = merged_providers
            continue

        setattr(settings, key, value)

    _persist_provider_secrets()
    _persist_app_config()
    update_scheduler_job(settings)
    return get_public_settings()
