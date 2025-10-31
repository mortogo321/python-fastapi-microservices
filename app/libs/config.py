from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_decode_responses: bool = True

    # Service Configuration
    api_host: str = "http://localhost:8000"
    payment_host: str = "http://localhost:8001"

    # Application Configuration
    app_name: str = "FastAPI Microservices"
    debug: bool = False
    log_level: str = "INFO"


# Global settings instance
settings = Settings()
