"""Scope grammar and matching (spec §5).

A Scope is a colon-delimited string describing what a token may do:

    provider:<name>:model:<model>:<capability>

e.g. ``provider:openai:model:gpt-4o:chat.completions``. A request is described by a triple
``(provider, model, capability)`` (an :class:`Operation`). Authorization is **default-deny**: a
request is allowed only if at least one granted Scope matches it segment-by-segment, where a
granted ``model``/``capability`` of ``*`` matches anything — but ``provider`` is never a wildcard
in v1 (§5.1), so a token is always bound to explicit providers.

This module is pure logic: no I/O, no state. That makes the wildcard rules exhaustively testable
and lets the Gateway authorize with a single function call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A segment token (§5.1): one or more ALPHA / DIGIT / "-" / "_" / ".". Note "*" is NOT in this
# class, so the provider slot below — which uses only this — can never be a wildcard.
_TOKEN = r"[A-Za-z0-9._-]+"

# The full scope grammar. provider must be a concrete token; model and capability may also be "*".
_SCOPE_RE = re.compile(
    rf"^provider:(?P<provider>{_TOKEN}):model:(?P<model>{_TOKEN}|\*):(?P<capability>{_TOKEN}|\*)$"
)

_WILDCARD = "*"


class InvalidScopeError(ValueError):
    """Raised when a string is not a syntactically valid Scope (§5.1)."""


@dataclass(frozen=True)
class Operation:
    """The operation a request wants to perform, derived from path + body by the Gateway."""

    provider: str
    model: str
    capability: str


def parse_scope(scope: str) -> tuple[str, str, str]:
    """Parse a Scope string into ``(provider, model, capability)``.

    Raises :class:`InvalidScopeError` on anything that doesn't match the grammar — including a
    wildcard provider, which §5.1 forbids.
    """

    match = _SCOPE_RE.match(scope)
    if match is None:
        raise InvalidScopeError(scope)
    return match["provider"], match["model"], match["capability"]


def scope_authorizes(granted: str, op: Operation) -> bool:
    """Return True if a single granted Scope authorizes ``op`` (§5.2).

    Comparison is case-sensitive and exact per segment, except a granted ``*`` for
    model/capability matches any value. A malformed granted scope authorizes nothing (fail
    closed) rather than raising — one bad entry must never grant or break access.
    """

    try:
        g_provider, g_model, g_capability = parse_scope(granted)
    except InvalidScopeError:
        return False

    if g_provider != op.provider:
        return False
    if g_model != _WILDCARD and g_model != op.model:
        return False
    if g_capability != _WILDCARD and g_capability != op.capability:
        return False
    return True


def authorize(granted_scopes: list[str], op: Operation) -> bool:
    """Return True if **any** granted Scope authorizes ``op`` (§5.2, §5.3 default-deny).

    An empty ``granted_scopes`` therefore denies: absence of permission is denial.
    """

    return any(scope_authorizes(scope, op) for scope in granted_scopes)
