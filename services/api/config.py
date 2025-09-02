import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "shadow_ai"
    postgres_user: str = "shadow_user"
    postgres_password: str = "shadow_pass"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "FlagWise API"
    api_version: str = "1.0.0"
    
    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Security
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3002", "http://127.0.0.1:3002"]
    prompt_truncate_length: int = 200  # Truncate prompts for security
    encryption_key: str = "your-secret-key-here-32-chars-min"  # Must be at least 32 characters
    
    # Kafka Configuration (optional fields to prevent validation errors)
    kafka_enabled: Optional[str] = None
    kafka_brokers: Optional[str] = None
    kafka_topic: Optional[str] = None
    kafka_group_id: Optional[str] = None
    kafka_auth_type: Optional[str] = None
    kafka_username: Optional[str] = None
    kafka_password: Optional[str] = None
    kafka_ssl_cert: Optional[str] = None
    kafka_ssl_key: Optional[str] = None
    kafka_ssl_ca: Optional[str] = None
    kafka_timeout_ms: Optional[str] = None
    kafka_retry_backoff_ms: Optional[str] = None
    kafka_message_schema: Optional[str] = None
    
    # Pagination
    default_page_size: int = 50
    max_page_size: int = 1000
    
    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()