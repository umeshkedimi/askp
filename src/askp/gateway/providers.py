"""Provider registry and operation resolution (spec §5.4, §6.1, §6.4 step 4).

To authorize a request the Gateway must turn an incoming URL like

    /v1/providers/openai/v1/chat/completions   (body: {"model": "gpt-4o", ...})

into the operation triple ``(provider, model, capability)`` that scope matching understands
(§5.2). Two pieces of per-provider knowledge make that possible, and both live here so adding a
provider is a one-entry change:

1. **Capability map** — which native path corresponds to which ASKP capability (§5.4 table).
2. **Transport facts** — the upstream base URL and how the provider expects its credential
   (OpenAI uses ``Authorization: Bearer``; Anthropic uses ``x-api-key``).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from askp.security.scopes import Operation


class UnknownProviderError(ValueError):
    """The requested provider is not in the registry."""


class UnsupportedOperationError(ValueError):
    """The provider is known but the native path maps to no v1 capability."""


@dataclass(frozen=True)
class ProviderSpec:
    """Everything the Gateway needs to authorize and proxy to one Provider."""

    name: str
    base_url: str
    # Builds the upstream auth headers from a resolved credential. A function (not a fixed header
    # name) because providers differ: Bearer token vs. x-api-key vs. query param.
    auth: Callable[[str], dict[str, str]]
    # Native request path -> ASKP capability token (§5.4).
    capabilities: dict[str, str]

    def capability_for(self, native_path: str) -> str:
        """Map a provider-native path to its capability, or raise UnsupportedOperationError."""
        capability = self.capabilities.get(_normalize_path(native_path))
        if capability is None:
            raise UnsupportedOperationError(f"{self.name}:{native_path}")
        return capability


def _bearer(credential: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {credential}"}


def _x_api_key(credential: str) -> dict[str, str]:
    return {"x-api-key": credential}


def _normalize_path(native_path: str) -> str:
    """Ensure a single leading slash so '/v1/x' and 'v1/x' resolve identically."""
    return "/" + native_path.strip("/")


# The v1 registry. Capability values mirror spec §5.4 exactly.
_REGISTRY: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(
        name="openai",
        base_url="https://api.openai.com",
        auth=_bearer,
        capabilities={
            "/v1/chat/completions": "chat.completions",
            "/v1/embeddings": "embeddings",
            "/v1/responses": "responses",
        },
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        base_url="https://api.anthropic.com",
        auth=_x_api_key,
        capabilities={
            "/v1/messages": "messages",
        },
    ),
}


def get_provider(name: str) -> ProviderSpec:
    """Look up a provider, raising UnknownProviderError if it is not registered."""
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise UnknownProviderError(name) from exc


def resolve_operation(
    provider_name: str, native_path: str, model: str
) -> tuple[ProviderSpec, Operation]:
    """Resolve ``(provider, native_path, model)`` into the matched spec and Operation triple.

    Raises UnknownProviderError / UnsupportedOperationError for unmapped requests. The ``model``
    comes from the request body and is supplied by the caller (the route), which owns body parsing.
    """

    spec = get_provider(provider_name)
    capability = spec.capability_for(native_path)
    return spec, Operation(provider=provider_name, model=model, capability=capability)
