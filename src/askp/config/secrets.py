"""The one, consistent gate every production secret must pass through.

The retired Python reference implementation had two secret-bearing components
(the token signing key and the vault KEK) that were each supposed to refuse to
start in production without an explicit value configured. Only one of them
actually did — the other silently generated an ephemeral value instead, which
would have invalidated every token on every restart in production without any
error at all. `resolve_secret` exists so that guarantee is enforced in exactly
one place: any component that needs a production-grade secret calls this
function from its `from_settings()` constructor, and cannot forget the guard
because there is no other way to get the value.
"""

from collections.abc import Callable


class ProductionSecretMissingError(RuntimeError):
    """Raised when a required secret is unset while running in production."""

    def __init__(self, name: str) -> None:
        super().__init__(f"{name} is required when ASKP_ENVIRONMENT=production")
        self.name = name


def resolve_secret[T](
    *,
    value: str | None,
    name: str,
    is_production: bool,
    parse: Callable[[str], T],
    generate_ephemeral: Callable[[], T],
) -> T:
    """Resolve a configured secret, failing closed in production if it's unset.

    - `value` set -> parsed and returned, regardless of environment.
    - `value` unset, `is_production` -> raises `ProductionSecretMissingError`.
    - `value` unset, not production -> an ephemeral value is generated (dev/test only).
    """
    if value:
        return parse(value)
    if is_production:
        raise ProductionSecretMissingError(name)
    return generate_ephemeral()
