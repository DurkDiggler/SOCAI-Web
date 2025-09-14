from __future__ import annotations

import ipaddress
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, ge=1, le=65535, env="APP_PORT")
    
    # Security
    max_request_size: int = Field(default=1048576, ge=1024, env="MAX_REQUEST_SIZE")  # 1MB
    rate_limit_requests: int = Field(default=100, ge=1, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, ge=1, env="RATE_LIMIT_WINDOW")  # 1 hour
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], env="CORS_ORIGINS")
    
    # Feature flags
    enable_email: bool = Field(default=True, env="ENABLE_EMAIL")
    enable_autotask: bool = Field(default=True, env="ENABLE_AUTOTASK")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")

    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, ge=1, le=65535, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    email_from: Optional[str] = Field(default=None, env="EMAIL_FROM")
    email_to: List[str] = Field(default_factory=list, env="EMAIL_TO")

    # Autotask
    at_base_url: Optional[str] = Field(default=None, env="AT_BASE_URL")
    at_api_integration_code: Optional[str] = Field(default=None, env="AT_API_INTEGRATION_CODE")
    at_username: Optional[str] = Field(default=None, env="AT_USERNAME")
    at_secret: Optional[str] = Field(default=None, env="AT_SECRET")
    at_account_id: Optional[int] = Field(default=None, env="AT_ACCOUNT_ID")
    at_queue_id: Optional[int] = Field(default=None, env="AT_QUEUE_ID")
    at_ticket_priority: int = Field(default=3, ge=1, le=5, env="AT_TICKET_PRIORITY")

    # Threat feeds
    otx_api_key: Optional[str] = Field(default=None, env="OTX_API_KEY")
    vt_api_key: Optional[str] = Field(default=None, env="VT_API_KEY")
    abuseipdb_api_key: Optional[str] = Field(default=None, env="ABUSEIPDB_API_KEY")

    # Scoring
    score_high: int = Field(default=70, ge=0, le=100, env="SCORE_HIGH")
    score_medium: int = Field(default=40, ge=0, le=100, env="SCORE_MEDIUM")

    # HTTP / Cache
    http_timeout: float = Field(default=8.0, ge=1.0, le=60.0, env="HTTP_TIMEOUT")
    ioc_cache_ttl: int = Field(default=1800, ge=60, env="IOC_CACHE_TTL")
    max_retries: int = Field(default=3, ge=0, le=10, env="MAX_RETRIES")
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0, env="RETRY_DELAY")

    # Webhook auth
    webhook_shared_secret: Optional[str] = Field(default=None, env="WEBHOOK_SHARED_SECRET")
    webhook_hmac_secret: Optional[str] = Field(default=None, env="WEBHOOK_HMAC_SECRET")
    webhook_hmac_header: str = Field(default="X-Signature", env="WEBHOOK_HMAC_HEADER")
    webhook_hmac_prefix: str = Field(default="sha256=", env="WEBHOOK_HMAC_PREFIX")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring
    metrics_port: int = Field(default=9090, ge=1, le=65535, env="METRICS_PORT")
    health_check_timeout: float = Field(default=5.0, ge=1.0, le=30.0, env="HEALTH_CHECK_TIMEOUT")
    
    # Database
    database_url: str = Field(default="sqlite:///./soc_agent.db", env="DATABASE_URL")
    postgres_host: Optional[str] = Field(default=None, env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, ge=1, le=65535, env="POSTGRES_PORT")
    postgres_user: Optional[str] = Field(default=None, env="POSTGRES_USER")
    postgres_password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    postgres_db: Optional[str] = Field(default=None, env="POSTGRES_DB")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("email_to", mode="before")
    @classmethod
    def parse_email_to(cls, v):
        if isinstance(v, str):
            return [email.strip() for email in v.split(",")]
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v):
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}")
        return v.lower()

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

SETTINGS = Settings()
