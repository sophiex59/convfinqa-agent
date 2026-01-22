"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    google_api_key: str = ""

    # Model Configuration
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.0

    # Paths
    data_path: str = "data/convfinqa_dataset.json"

    # Logging
    log_level: str = "INFO"


settings = Settings()
