import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Kafka Configuration
    kafka_bootstrap_servers: str = "kafka:29092"
    kafka_topic: str = "llm-traffic-logs"
    kafka_group_id: str = "shadow-ai-detection"
    kafka_auto_offset_reset: str = "latest"  # Start from latest messages
    
    # PostgreSQL Configuration
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "shadow_ai"
    postgres_user: str = "shadow_user"
    postgres_password: str = "shadow_pass"
    
    # Consumer Configuration
    max_poll_records: int = 500  # Process up to 500 messages per batch
    session_timeout_ms: int = 30000  # 30 seconds
    heartbeat_interval_ms: int = 3000  # 3 seconds
    
    # Dead Letter Queue
    dlq_topic: str = "llm-traffic-logs-dlq"
    
    # Logging
    log_level: str = "INFO"
    
    # Alerting Configuration
    slack_webhook_url: str = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    alert_min_risk_score: int = 50  # Minimum risk score to trigger alerts
    alert_rate_limit: int = 5  # Max alerts per minute
    
    # Encryption Configuration
    encryption_key: str = "your-secret-key-here-32-chars-min"  # Must be at least 32 characters
    
    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()