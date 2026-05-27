"""
Configuration settings for Customer Support Autopilot.

Loads all environment variables using pydantic-settings.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Groq API settings
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Shopify settings
    shopify_store_url: str = ""
    shopify_access_token: str = ""

    # Stripe settings
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Vector database (Qdrant)
    qdrant_url: str = "http://qdrant:6333"
    pinecone_api_key: str = ""

    # Redis settings
    redis_url: str = "redis://redis:6379"

    # Admin API key for dashboard access
    admin_api_key: str = "admin-secret-change-me"

    # Email settings (SendGrid SMTP)
    email_smtp_host: str = "smtp.sendgrid.net"
    email_smtp_user: str = "apikey"
    email_smtp_pass: str = ""

    # Optional PostgreSQL for logs
    database_url: Optional[str] = None

    # Application settings
    log_level: str = "INFO"
    rate_limit_requests: int = 10
    rate_limit_window: int = 60  # seconds

    @property
    def use_groq(self) -> bool:
        """Check if Groq API is configured."""
        return bool(self.groq_api_key)

    @property
    def use_shopify(self) -> bool:
        """Check if Shopify integration is configured."""
        return bool(self.shopify_store_url) and bool(self.shopify_access_token)

    @property
    def use_stripe(self) -> bool:
        """Check if Stripe integration is configured."""
        return bool(self.stripe_secret_key)

    @property
    def use_qdrant(self) -> bool:
        """Check if Qdrant is configured."""
        return bool(self.qdrant_url)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
