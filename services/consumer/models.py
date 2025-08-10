from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4

class LLMRequest(BaseModel):
    """Model for incoming LLM request messages from Kafka"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    timestamp: datetime
    src_ip: str
    provider: str  # openai, anthropic, etc.
    model: str     # gpt-4, claude-3, etc.
    endpoint: Optional[str] = None
    method: str = "POST"
    headers: Optional[Dict[str, Any]] = None
    prompt: str
    duration_ms: Optional[int] = None
    status_code: Optional[int] = None
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            # Handle common timestamp formats
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Try other common formats
                from datetime import datetime as dt
                for fmt in [
                    '%Y-%m-%dT%H:%M:%S.%fZ',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S',
                ]:
                    try:
                        return dt.strptime(v, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Unable to parse timestamp: {v}")
        return v
    
    @validator('provider')
    def validate_provider(cls, v):
        return v.lower().strip()
    
    @validator('model')
    def validate_model(cls, v):
        return v.lower().strip()
    
    @validator('headers', pre=True)
    def parse_headers(cls, v):
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v
    
    @validator('src_ip')
    def validate_ip(cls, v):
        # Basic IP validation
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            # Could be hostname or other identifier
            return v

class DatabaseRecord(BaseModel):
    """Model for database insertion"""
    id: UUID
    timestamp: datetime
    src_ip: str
    provider: str
    model: str
    endpoint: Optional[str] = None
    method: str = "POST"
    headers: Optional[Dict[str, Any]] = None
    prompt: str
    response: Optional[str] = None  # Will be None for now
    duration_ms: Optional[int] = None
    status_code: Optional[int] = None
    risk_score: int = 0
    is_flagged: bool = False
    flag_reason: Optional[str] = None

    @classmethod
    def from_llm_request(cls, request: LLMRequest) -> "DatabaseRecord":
        """Convert LLMRequest to DatabaseRecord"""
        return cls(
            id=request.id,
            timestamp=request.timestamp,
            src_ip=request.src_ip,
            provider=request.provider,
            model=request.model,
            endpoint=request.endpoint,
            method=request.method,
            headers=request.headers,
            prompt=request.prompt,
            duration_ms=request.duration_ms,
            status_code=request.status_code,
        )