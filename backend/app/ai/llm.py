"""
LLM factory — centralised model instantiation.

Usage:
    llm = get_llm()                    # default provider from settings
    llm = get_llm(provider="openai")   # explicit override
"""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings

_PROVIDER_CONFIGS: dict[str, dict] = {
    "deepseek": {
        "model": settings.deepseek_model,
        "base_url": settings.deepseek_base_url,
        "api_key": settings.deepseek_api_key,
    },
    "openai": {
        "model": settings.openai_model,
        "api_key": settings.openai_api_key,
    },
    "qwen": {
        "model": "qwen-max",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": settings.openai_api_key,
    },
}


def get_llm(
    provider: str | None = None,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> BaseChatModel:
    """Return a ChatOpenAI instance for the requested provider."""
    provider = provider or settings.llm_provider
    cfg = _PROVIDER_CONFIGS.get(provider)
    if cfg is None:
        supported = list(_PROVIDER_CONFIGS)
        raise ValueError(f"Unknown LLM provider: {provider!r}. Choose from {supported}")

    return ChatOpenAI(
        **cfg,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        max_tokens=max_tokens if max_tokens is not None else settings.llm_max_tokens,
    )
