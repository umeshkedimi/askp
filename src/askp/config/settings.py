from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogFormat(StrEnum):
    JSON = "json"
    CONSOLE = "console"
    AUTO = "auto"


class Settings(BaseSettings):
    """Process configuration, sourced from `ASKP_`-prefixed environment variables.

    Every field a future increment adds that must be treated as a production secret
    (signing keys, the vault KEK, admin keys, ...) is resolved through
    `askp.config.secrets.resolve_secret`, never read directly here as a bare default.
    """

    model_config = SettingsConfigDict(env_prefix="ASKP_", env_file=".env", extra="ignore")

    app_name: str = "askp"
    environment: Environment = Environment.DEVELOPMENT

    host: str = "127.0.0.1"
    port: int = 8000

    log_level: str = "info"
    log_format: LogFormat = LogFormat.AUTO

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION

    @property
    def resolved_log_format(self) -> LogFormat:
        if self.log_format is not LogFormat.AUTO:
            return self.log_format
        return LogFormat.CONSOLE if self.environment is Environment.DEVELOPMENT else LogFormat.JSON


@lru_cache
def get_settings() -> Settings:
    return Settings()
