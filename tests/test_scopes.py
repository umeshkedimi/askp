"""Tests for scope parsing and matching (askp.security.scopes), mirroring spec §5.2."""

import pytest

from askp.security.scopes import (
    InvalidScopeError,
    Operation,
    authorize,
    parse_scope,
    scope_authorizes,
)

OP = Operation(provider="openai", model="gpt-4o", capability="chat.completions")


@pytest.mark.parametrize(
    "granted",
    [
        "provider:openai:model:gpt-4o:chat.completions",  # exact
        "provider:openai:model:*:chat.completions",  # model wildcard
        "provider:openai:model:gpt-4o:*",  # capability wildcard
        "provider:openai:model:*:*",  # both wildcards
    ],
)
def test_granted_scope_authorizes(granted: str) -> None:
    assert scope_authorizes(granted, OP) is True


@pytest.mark.parametrize(
    "granted",
    [
        "provider:openai:model:gpt-4o-mini:chat.completions",  # model mismatch
        "provider:anthropic:model:*:*",  # provider mismatch
        "provider:openai:model:gpt-4o:embeddings",  # capability mismatch
        "provider:OpenAI:model:gpt-4o:chat.completions",  # case-sensitive provider
    ],
)
def test_granted_scope_denies(granted: str) -> None:
    assert scope_authorizes(granted, OP) is False


def test_authorize_is_default_deny_on_empty() -> None:
    assert authorize([], OP) is False


def test_authorize_any_match_wins() -> None:
    granted = [
        "provider:anthropic:model:*:messages",  # no
        "provider:openai:model:gpt-4o:chat.completions",  # yes
    ]
    assert authorize(granted, OP) is True


def test_malformed_granted_scope_fails_closed() -> None:
    # A bad entry must neither raise nor grant access.
    assert authorize(["not-a-scope", "provider:openai:model:gpt-4o"], OP) is False


def test_parse_scope_round_trips() -> None:
    assert parse_scope("provider:openai:model:gpt-4o:chat.completions") == (
        "openai",
        "gpt-4o",
        "chat.completions",
    )


@pytest.mark.parametrize(
    "bad",
    [
        "provider:*:model:gpt-4o:chat.completions",  # wildcard provider forbidden (§5.1)
        "provider:openai:model:gpt-4o",  # too few segments
        "openai:gpt-4o:chat.completions",  # missing literal markers
        "provider:openai:model::chat.completions",  # empty model segment
    ],
)
def test_parse_scope_rejects_invalid(bad: str) -> None:
    with pytest.raises(InvalidScopeError):
        parse_scope(bad)
