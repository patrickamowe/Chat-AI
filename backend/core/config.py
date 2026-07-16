from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./sql_app.db"

    JWT_ACCESS_SECRET: str = "super-secret-access-key-fallback"
    JWT_REFRESH_SECRET: str = "another-super-secret-refresh-key-fallback"
    JWT_ALGORITHM: str = "HS256"

    GEMINI_API_KEY: str = "super-secret-key-fallback"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _reject_fallback_secrets_in_production(self):
        if self.ENVIRONMENT == "production":
            fallback_pairs = {
                "JWT_ACCESS_SECRET": "super-secret-access-key-fallback",
                "JWT_REFRESH_SECRET": "another-super-secret-refresh-key-fallback",
                "GEMINI_API_KEY": "super-secret-key-fallback",
            }
            leaked = [
                name for name, fallback in fallback_pairs.items()
                if getattr(self, name) == fallback
            ]
            if leaked:
                raise RuntimeError(
                    f"Refusing to start in production with fallback values for: {', '.join(leaked)}. "
                    "Set these as real Heroku config vars."
                )
        return self


settings = Settings()