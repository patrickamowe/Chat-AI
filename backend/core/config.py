from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic automatically casts these to the correct types

    DATABASE_URL: str = "sqlite:///./sql_app.db"

    JWT_ACCESS_SECRET: str = "super-secret-access-key-fallback"
    JWT_REFRESH_SECRET: str = "another-super-secret-refresh-key-fallback"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: float = 15.0
    REFRESH_TOKEN_EXPIRE_MINUTES: float= 10080.0  # 7 days

    # Tells Pydantic to read from a .env file automatically
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Single instance to import across your application
settings = Settings()