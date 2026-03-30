from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
import json
from dotenv import load_dotenv
from app.models.schemas import ProviderConfig

load_dotenv()

def get_default_providers() -> dict[str, ProviderConfig]:
    return {
        "openai": ProviderConfig(model="gpt-5.4-mini", api_key="none", base_url="https://api.openai.com/v1", available_models=["gpt-5.4", "gpt-5.4-mini", "gpt-5.3-instant"]),
        "anthropic": ProviderConfig(model="claude-4.6-sonnet", api_key="none", base_url="none", available_models=["claude-4.6-sonnet", "claude-4.6-opus"]),
        "gemini": ProviderConfig(model="gemini-3.1-flash-lite", api_key="none", base_url="none", available_models=["gemini-3.1-flash-lite", "gemini-3.1-flash-live", "gemini-3.1-pro"]),
        "glm": ProviderConfig(model="glm-5.1", api_key="none", base_url="https://open.bigmodel.cn/api/paas/v4", available_models=["glm-5.1", "glm-5", "glm-5-turbo"]),
        "kimi": ProviderConfig(model="moonshot-k2.5", api_key="none", base_url="https://api.moonshot.cn/v1", available_models=["moonshot-k2.5", "moonshot-k2-thinking"]),
        "qwen": ProviderConfig(model="qwen3.5-plus", api_key="none", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", available_models=["qwen3.5-plus", "qwen3-max-thinking", "qwen3.5-max"]),
        "ollama": ProviderConfig(model="llama3", api_key="ollama", base_url="http://localhost:11434/v1", available_models=["llama3", "mistral", "qwen2.5", "deepseek-r1"])
    }



class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/arxiv_agent.db"

    # ArXiv
    arxiv_categories: list[str] = ["cs.AI", "cs.LG", "cs.CV"]
    arxiv_max_results: int = 200  # fetch pool before filtering
    arxiv_days: int = 7
    papers_per_day: int = 10

    # LLM
    llm_provider: str = "openai"  # openai|anthropic|gemini|glm|kimi|qwen|ollama
    llm_max_tokens: int = 800  # keep summaries concise → fewer tokens
    llm_concurrency: int = 1
    llm_wait_seconds: int = 10
    providers: dict[str, ProviderConfig] = Field(default_factory=get_default_providers)

    # Keywords filter
    keywords: list[str] = []

    # Storage
    summaries_dir: str = "./data/summaries"

    # Schedule (cron-style, default 8am every day)
    auto_fetch_cron: str = "0 8 * * *"
    auto_fetch_enabled: bool = False

    model_config = {
        "env_file": ".env", 
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


settings = Settings()

# Ensure data directories exist
os.makedirs(settings.summaries_dir, exist_ok=True)
os.makedirs("./data", exist_ok=True)

APP_CONFIG_FILE = "./config.json"

if os.path.exists(APP_CONFIG_FILE):
    try:
        with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
            app_data = json.load(f)
            for k, v in app_data.items():
                if hasattr(settings, k) and v is not None:
                    if k == "providers":
                        new_provs = {}
                        for pk, pv in v.items():
                            # Load dynamic secrets natively from .env mapping
                            env_key = f"{pk.upper()}_API_KEY"
                            env_val = os.getenv(env_key)
                            if env_val:
                                pv["api_key"] = env_val
                            
                            new_provs[pk] = ProviderConfig(**pv)
                        setattr(settings, k, new_provs)
                    else:
                        setattr(settings, k, v)
    except Exception as e:
        print(f"Failed to load app config from JSON: {e}")
