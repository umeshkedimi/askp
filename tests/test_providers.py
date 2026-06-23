"""Tests for the provider registry and operation resolution (askp.gateway.providers)."""

import pytest

from askp.gateway.providers import (
    UnknownProviderError,
    UnsupportedOperationError,
    get_provider,
    resolve_operation,
)


def test_resolve_openai_chat_completions() -> None:
    spec, op = resolve_operation("openai", "/v1/chat/completions", model="gpt-4o")
    assert spec.base_url == "https://api.openai.com"
    assert (op.provider, op.model, op.capability) == ("openai", "gpt-4o", "chat.completions")


def test_resolve_anthropic_messages() -> None:
    spec, op = resolve_operation("anthropic", "/v1/messages", model="claude-sonnet-4-6")
    assert op.capability == "messages"
    assert spec.auth("secret") == {"x-api-key": "secret"}


def test_openai_auth_is_bearer() -> None:
    assert get_provider("openai").auth("secret") == {"Authorization": "Bearer secret"}


def test_path_is_normalized() -> None:
    # Leading-slash differences must not change resolution.
    _, with_slash = resolve_operation("openai", "/v1/embeddings", model="text-embedding-3-small")
    _, without = resolve_operation("openai", "v1/embeddings", model="text-embedding-3-small")
    assert with_slash.capability == without.capability == "embeddings"


def test_unknown_provider_raises() -> None:
    with pytest.raises(UnknownProviderError):
        resolve_operation("cohere", "/v1/chat", model="x")


def test_unsupported_operation_raises() -> None:
    with pytest.raises(UnsupportedOperationError):
        resolve_operation("openai", "/v1/images/generations", model="x")
