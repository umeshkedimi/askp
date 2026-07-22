import pytest

from askp.config.secrets import ProductionSecretMissingError, resolve_secret


def test_configured_value_is_parsed_regardless_of_environment() -> None:
    result = resolve_secret(
        value="configured",
        name="test_secret",
        is_production=True,
        parse=lambda v: v.upper(),
        generate_ephemeral=lambda: "SHOULD_NOT_BE_CALLED",
    )

    assert result == "CONFIGURED"


def test_missing_value_generates_ephemeral_outside_production() -> None:
    result = resolve_secret(
        value=None,
        name="test_secret",
        is_production=False,
        parse=lambda v: v.upper(),
        generate_ephemeral=lambda: "ephemeral",
    )

    assert result == "ephemeral"


def test_missing_value_raises_in_production() -> None:
    with pytest.raises(ProductionSecretMissingError, match="test_secret"):
        resolve_secret(
            value=None,
            name="test_secret",
            is_production=True,
            parse=lambda v: v.upper(),
            generate_ephemeral=lambda: "SHOULD_NOT_BE_CALLED",
        )
