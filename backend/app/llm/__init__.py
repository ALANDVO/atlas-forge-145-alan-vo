"""LLM provider adapters.

Every adapter implements :class:`BaseLLMAdapter` so callers can swap providers
through configuration without touching call sites.
"""

from app.llm.base import BaseLLMAdapter, LLMMessage, LLMRequest, LLMResponse
from app.llm.openai_compatible import OpenAICompatibleAdapter
from app.llm.registry import ADAPTERS, get_adapter

__all__ = [
    "ADAPTERS",
    "BaseLLMAdapter",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "OpenAICompatibleAdapter",
    "get_adapter",
]
