import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "HandoverOS"

    APP_VERSION: str = "1.0.0"

    DEBUG: bool = True

    SECRET_KEY: str = "change-this-secret-before-deployment"

    DATABASE_URL: str = "sqlite:///./handoveros.db"

    API_PREFIX: str = "/api"

    CORS_ORIGINS: str = "http://localhost:3000"

    OPENAI_API_KEY: str | None = None

    GITHUB_TOKEN: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def allowed_origins(self) -> list[str]:

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()