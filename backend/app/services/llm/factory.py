"""
LLM 客户端工厂。

OpenAI 兼容 providers（共用一套 SDK，只换 base_url + key）：
  - openai   → https://api.openai.com/v1
  - kimi     → https://api.moonshot.cn/v1
  - qwen     → https://dashscope.aliyuncs.com/compatible-mode/v1
  - glm      → https://open.bigmodel.cn/api/paas/v4
  - ollama   → http://localhost:11434/v1  (key = "ollama")

独立 SDK：
  - anthropic
  - gemini
"""

from __future__ import annotations
from typing import Optional
from app.services.llm.base import BaseLLMClient


# ── OpenAI-compatible client ──────────────────────────────────────────────────

class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, api_key: str, base_url: str, model: str, name: str):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    async def complete(self, messages: list[dict], max_tokens: int = 800) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


# ── Anthropic client ──────────────────────────────────────────────────────────

class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def complete(self, messages: list[dict], max_tokens: int = 800) -> str:
        # Convert OpenAI-format messages to Anthropic format
        system = ""
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                user_messages.append({"role": m["role"], "content": m["content"]})

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system or "You are a helpful research assistant.",
            messages=user_messages,
        )
        return response.content[0].text


# ── Gemini client ─────────────────────────────────────────────────────────────

class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str):
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def complete(self, messages: list[dict], max_tokens: int = 800) -> str:
        import asyncio
        from google import genai
        # Concatenate messages to single prompt (Gemini free-tier doesn't support chat history well)
        prompt = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )
        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model,
            contents={"text": prompt},
            config=genai.types.GenerateContentConfig(
                temperature=0.3,
                top_k=30,
                top_p=0.95,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text


# ── Factory ───────────────────────────────────────────────────────────────────

_OPENAI_COMPATIBLE: dict[str, dict] = {
    "openai": {"base_url_field": "openai_base_url", "key_field": "openai_api_key"},
    "kimi":   {"base_url": "https://api.moonshot.cn/v1",             "key_field": "kimi_api_key"},
    "qwen":   {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "key_field": "qwen_api_key"},
    "glm":    {"base_url": "https://open.bigmodel.cn/api/paas/v4",   "key_field": "glm_api_key"},
}


def create_llm_client(settings) -> BaseLLMClient:
    """根据 settings 创建对应的 LLM 客户端实例。"""
    provider = settings.llm_provider.lower()
    cfg = settings.providers.get(provider)
    
    if not cfg:
        raise ValueError(f"Provider {provider} format missing from new JSON schema migrations.")
        
    model = cfg.model
    api_key = cfg.api_key
    base_url = cfg.base_url

    if provider in _OPENAI_COMPATIBLE:
        return OpenAICompatibleClient(api_key=api_key, base_url=base_url, model=model, name=provider)

    if provider == "ollama":
        return OpenAICompatibleClient(api_key=api_key, base_url=base_url, model=model, name="ollama")

    if provider == "anthropic":
        return AnthropicClient(api_key=api_key, model=model)

    if provider == "gemini":
        return GeminiClient(api_key=api_key, model=model)

    raise ValueError(f"Unknown LLM provider: {provider}")
