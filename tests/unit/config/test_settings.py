from askp.config import Environment, LogFormat, Settings


def test_defaults_are_safe_for_local_development() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment is Environment.DEVELOPMENT
    assert settings.is_production is False


def test_auto_log_format_resolves_to_console_in_development() -> None:
    settings = Settings(
        _env_file=None, environment=Environment.DEVELOPMENT, log_format=LogFormat.AUTO
    )

    assert settings.resolved_log_format is LogFormat.CONSOLE


def test_auto_log_format_resolves_to_json_in_production() -> None:
    settings = Settings(
        _env_file=None, environment=Environment.PRODUCTION, log_format=LogFormat.AUTO
    )

    assert settings.resolved_log_format is LogFormat.JSON
