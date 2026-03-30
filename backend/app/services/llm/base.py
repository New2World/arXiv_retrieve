"""
LLM 抽象基类与统一接口。

设计原则：
- OpenAI / Kimi / Qwen / GLM / Ollama 均兼容 OpenAI SDK，只需传入不同 base_url/key。
- Anthropic 和 Gemini 使用各自 SDK，但对外暴露相同的 `complete()` 接口。
- 这样后续新增 provider 只需继承 BaseLLMClient 即可，无需修改上层代码。
"""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """所有 LLM 客户端必须实现此接口。"""

    @abstractmethod
    async def complete(self, messages: list[dict], max_tokens: int = 800) -> str:
        """
        发送对话请求并返回文本响应。

        Args:
            messages: OpenAI 格式的消息列表 [{"role": "user", "content": "..."}]
            max_tokens: 最大生成 token 数

        Returns:
            模型生成的文本字符串
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 标识符，用于日志。"""
        ...
