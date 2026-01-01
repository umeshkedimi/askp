import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    ENV: str = "dev"
    SERVICE_NAME: str = "askp"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "askp"
    POSTGRES_PASSWORD: str = "askp"
    POSTGRES_DB: str = "askp"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    JWT_SECRET: str = "change_this"
    JWT_ALGO: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
