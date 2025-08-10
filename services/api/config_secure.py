import os
import secrets
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Configuration - MUST be set via environment variables
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB")
    postgres_user: str = os.getenv("POSTGRES_USER")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "FlagWise API"
    api_version: str = "1.0.0"
    
    # JWT Configuration - CRITICAL: Must be set securely
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Security - CRITICAL: Must be set securely
    cors_origins: list = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    prompt_truncate_length: int = 200
    encryption_key: str = os.getenv("ENCRYPTION_KEY")  # Must be 32+ chars, base64 encoded
    
    # Kafka Configuration
    kafka_enabled: Optional[str] = os.getenv("KAFKA_ENABLED")
    kafka_brokers: Optional[str] = os.getenv("KAFKA_BROKERS")
    kafka_topic: Optional[str] = os.getenv("KAFKA_TOPIC")
    kafka_group_id: Optional[str] = os.getenv("KAFKA_GROUP_ID")
    kafka_auth_type: Optional[str] = os.getenv("KAFKA_AUTH_TYPE")
    kafka_username: Optional[str] = os.getenv("KAFKA_USERNAME")
    kafka_password: Optional[str] = os.getenv("KAFKA_PASSWORD")
    
    # Pagination
    default_page_size: int = 50
    max_page_size: int = 1000
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Validate critical security settings
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable must be set")
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
            
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable must be set")
        if len(self.encryption_key) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters")
            
        if not self.postgres_user or not self.postgres_password or not self.postgres_db:
            raise ValueError("Database credentials (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB) must be set")
    
    class Config:
        env_file = ".env"
        # Don't allow field reassignment
        allow_mutation = False

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @staticmethod
    def generate_secure_key() -> str:
        """Generate a cryptographically secure key"""
        return secrets.token_urlsafe(32)

settings = Settings()