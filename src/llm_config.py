"""
LLM provider configuration — OpenAI-compatible APIs.

Set LLM_PROVIDER in .env to switch: deepseek | kimi | minimax
Override per command with --llm-provider (resume.py build / cover-letter).
"""

from __future__ import annotations

import os
import sys
from typing import Any

# MiniMax M2.x wraps answers in `` … `` blocks.
_t = chr(116) + chr(104) + chr(105) + chr(110) + chr(107)  # "think"
_THINKING_OPEN = (f"<{_t}>", "<thinking>")
_THINKING_CLOSE = (f"</{_t}>", "</thinking>")


def strip_thinking_blocks(content: str) -> str:
    """Remove leading chain-of-thought wrapper; keep text after the last close tag."""
    stripped = content.lstrip()
    for open_tag, close_tag in zip(_THINKING_OPEN, _THINKING_CLOSE):
        if stripped.startswith(open_tag):
            end = stripped.rfind(close_tag)
            if end != -1:
                return stripped[end + len(close_tag):].strip()
            return ""
    return content.strip()

PROVIDERS: dict[str, dict[str, Any]] = {
    "deepseek": {
        "label": "DeepSeek",
        "api_key_var": "DEEPSEEK_API_KEY",
        "base_url_var": "DEEPSEEK_BASE_URL",
        "model_var": "DEEPSEEK_MODEL",
        "default_base_url": "https://api.deepseek.com",
        "default_model": "deepseek-v4-flash",
        "models": ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner"],
    },
    "kimi": {
        "label": "Kimi (Moonshot)",
        "api_key_var": "KIMI_API_KEY",
        "base_url_var": "KIMI_BASE_URL",
        "model_var": "KIMI_MODEL",
        # China inland — use api.moonshot.ai/v1 for international
        "default_base_url": "https://api.moonshot.cn/v1",
        "default_model": "kimi-k2.5",
        "models": [
            "kimi-k2.5",
            "kimi-k2-0905-preview",
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
        ],
    },
    "minimax": {
        "label": "MiniMax",
        "api_key_var": "MINIMAX_API_KEY",
        "base_url_var": "MINIMAX_BASE_URL",
        "model_var": "MINIMAX_MODEL",
        # China inland — use https://api.minimax.io/v1 for international
        "default_base_url": "https://api.minimaxi.com/v1",
        "default_model": "MiniMax-M2.5",
        "models": [
            "MiniMax-M2.5",
            "MiniMax-M2.5-highspeed",
            "MiniMax-M2.7",
            "MiniMax-M2.7-highspeed",
            "MiniMax-M3",
        ],
    },
}


class LLMNotConfiguredError(Exception):
    """Raised when the selected provider has no API key."""


def resolve_llm_config(provider: str | None = None) -> dict[str, str]:
    """Resolve active provider, API key, base URL, and model from environment."""
    name = (provider or os.environ.get("LLM_PROVIDER", "deepseek")).strip().lower()
    if name not in PROVIDERS:
        valid = ", ".join(PROVIDERS)
        raise ValueError(f"Unknown LLM provider '{name}'. Choose from: {valid}")

    spec = PROVIDERS[name]
    api_key = os.environ.get(spec["api_key_var"], "").strip()
    base_url = os.environ.get(spec["base_url_var"], spec["default_base_url"]).strip()
    model = os.environ.get(spec["model_var"], spec["default_model"]).strip()

    return {
        "provider": name,
        "label": spec["label"],
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }


def extract_llm_text(message, *, finish_reason: str | None = None) -> str:
    """
    Normalize text from an OpenAI-compatible chat completion message.

    Reasoning models (DeepSeek, Kimi) may leave ``content`` empty when
    ``max_tokens`` is consumed by internal reasoning — use generous budgets.
    MiniMax embeds ``<think>`` blocks in ``content``.
    """
    content = message.content or ""
    content = strip_thinking_blocks(content)
    if content:
        return content

    if finish_reason == "length":
        print(
            "LLM hit token limit before producing output; increase max_tokens",
            file=sys.stderr,
        )
    return ""


def llm_chat_completion(
    client,
    model: str,
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 1024,
    **kwargs,
) -> str:
    """Run a chat completion and return cleaned assistant text."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        **kwargs,
    )
    choice = response.choices[0]
    text = extract_llm_text(choice.message, finish_reason=choice.finish_reason)
    if choice.finish_reason == "length" and not text:
        print(f"LLM returned empty (max_tokens={max_tokens})", file=sys.stderr)
    return text


def get_llm_client(provider: str | None = None):
    """
    Return (OpenAI client, model name) for the configured provider.
    Raises LLMNotConfiguredError if API key is missing.
    """
    from openai import OpenAI

    cfg = resolve_llm_config(provider)
    if not cfg["api_key"]:
        raise LLMNotConfiguredError(
            f"{cfg['label']} API key not set ({PROVIDERS[cfg['provider']]['api_key_var']})"
        )
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    return client, cfg["model"], cfg


def list_providers() -> list[dict[str, Any]]:
    """Return provider metadata for CLI / docs."""
    out = []
    for name, spec in PROVIDERS.items():
        out.append({
            "id": name,
            "label": spec["label"],
            "default_base_url": spec["default_base_url"],
            "default_model": spec["default_model"],
            "models": spec["models"],
            "api_key_var": spec["api_key_var"],
        })
    return out
