"""Common adapter interface shared by every LLM provider."""

from __future__ import annotations

import abc
from typing import Any, Mapping, Sequence

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    """One chat turn."""

    role: str
    content: str


class LLMRequest(BaseModel):
    """Provider-independent completion request."""

    messages: Sequence[LLMMessage]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class LLMResponse(BaseModel):
    """Provider-independent completion result."""

    text: str
    model: str
    provider: str
    finish_reason: str | None = None


def redact(text: str) -> str:
    """Strip anything that looks like a credential from an error string.

    Providers echo request payloads (including ``Authorization`` headers and
    ``api_key`` query parameters) in their error bodies. We never want those to
    reach logs or HTTP responses.
    """
    markers = (
        "api_key=",
        "api-key=",
        "apikey=",
        "access_token=",
        "token=",
        "key=",
        "authorization",
        "bearer ",
    )
    lowered = text.lower()
    for marker in markers:
        start = 0
        while True:
            idx = lowered.find(marker, start)
            if idx < 0:
                break
            end = idx + len(marker)
            while end < len(text) and text[end] not in " \t\r\n,;&\"')":
                end += 1
            text = text[:idx] + marker + "[redacted]" + text[end:]
            lowered = text.lower()
            start = idx + len(marker) + len("[redacted]")
    return text


class LLMError(RuntimeError):
    """Provider call failed; message is already redacted."""

    def __init__(self, provider: str, message: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {redact(message)}")


class BaseLLMAdapter(abc.ABC):
    """Contract every provider adapter implements."""

    #: Stable identifier used in configuration (``LLM_PROVIDER``).
    name: str = "base"

    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None):
        self.model = model
        self.base_url = base_url
        self._api_key = api_key

    @abc.abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Run one completion and return a normalized result.

        Implementations MUST raise :class:`LLMError` (never a raw provider
        exception) so credentials cannot leak through tracebacks.
        """

    def describe(self) -> dict[str, Any]:
        """Non-sensitive adapter metadata, safe to expose via an API."""
        return {
            "provider": self.name,
            "model": self.model,
            "base_url": self.base_url,
            "has_api_key": bool(self._api_key),
        }
