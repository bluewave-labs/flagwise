from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from uuid import UUID
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    READ_ONLY = "read_only"

class User(BaseModel):
    username: str
    role: UserRole
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    
class UserInDB(User):
    hashed_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    role: UserRole

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None

# Request/Response Models
class LLMRequestResponse(BaseModel):
    """Response model for LLM requests with security considerations"""
    id: UUID
    timestamp: datetime
    src_ip: str
    provider: str
    model: str
    endpoint: Optional[str] = None
    method: str = "POST"
    prompt_preview: str  # Truncated prompt for security
    duration_ms: Optional[int] = None
    status_code: Optional[int] = None
    risk_score: int
    is_flagged: bool
    flag_reason: Optional[str] = None
    created_at: datetime

class LLMRequestDetail(LLMRequestResponse):
    """Detailed response model with full prompt (Admin only)"""
    prompt: str
    response: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None

class DetectionRuleResponse(BaseModel):
    """Response model for detection rules"""
    id: UUID
    name: str
    description: Optional[str] = None
    category: str
    rule_type: str
    pattern: str
    severity: str
    points: int
    priority: int
    stop_on_match: bool
    combination_logic: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DetectionRuleCreate(BaseModel):
    """Create model for detection rules"""
    name: str
    description: Optional[str] = None
    category: str = Field(..., pattern="^(data_privacy|security|compliance)$")
    rule_type: str = Field(..., pattern="^(keyword|regex|model_restriction|custom_scoring)$")
    pattern: str
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    points: int = Field(..., ge=0, le=100)
    priority: int = Field(default=0, ge=0, le=1000)
    stop_on_match: bool = Field(default=False)
    combination_logic: str = Field(default="AND", pattern="^(AND|OR)$")
    is_active: bool = True

class DetectionRuleUpdate(BaseModel):
    """Update model for detection rules"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = Field(None, pattern="^(data_privacy|security|compliance)$")
    rule_type: Optional[str] = Field(None, pattern="^(keyword|regex|model_restriction|custom_scoring)$")
    pattern: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    points: Optional[int] = Field(None, ge=0, le=100)
    priority: Optional[int] = Field(None, ge=0, le=1000)
    stop_on_match: Optional[bool] = None
    combination_logic: Optional[str] = Field(None, pattern="^(AND|OR)$")
    is_active: Optional[bool] = None

class BulkRuleOperation(BaseModel):
    """Bulk operations on detection rules"""
    rule_ids: List[str]
    operation: str = Field(..., pattern="^(enable|disable|delete)$")

class RuleTemplate(BaseModel):
    """Built-in rule template"""
    name: str
    description: str
    category: str
    rule_type: str
    pattern: str
    severity: str
    points: int
    examples: List[str] = []

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class RequestFilters(BaseModel):
    """Query filters for request endpoints"""
    flagged: Optional[bool] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    src_ip: Optional[str] = None
    min_risk_score: Optional[int] = Field(None, ge=0, le=100)
    max_risk_score: Optional[int] = Field(None, ge=0, le=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None  # Search in prompt preview
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)

class StatsResponse(BaseModel):
    """Statistics response model"""
    total_requests: int
    flagged_requests: int
    flagged_rate: float
    top_providers: List[Dict[str, Any]]
    top_models: List[Dict[str, Any]]
    top_risk_ips: List[Dict[str, Any]]
    avg_risk_score: float
    requests_by_hour: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    database_connected: bool

class SessionResponse(BaseModel):
    """Response model for user sessions"""
    id: str  # Generated from src_ip + start_time
    src_ip: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    request_count: int
    avg_risk_score: float
    flagged_count: int
    geographic_info: Optional[str] = None
    user_agent: Optional[str] = None
    top_providers: List[str]
    top_models: List[str]
    risk_level: str  # "critical", "high", "medium", "low"
    unusual_patterns: List[str] = []

class SessionDetail(SessionResponse):
    """Detailed session with request timeline"""
    requests: List[LLMRequestResponse]
    risk_breakdown: Dict[str, int]  # {"critical": 2, "high": 5, "medium": 3, "low": 10}

class SessionFilters(BaseModel):
    """Query filters for session endpoints"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    src_ip: Optional[str] = None
    min_risk_score: Optional[int] = Field(None, ge=0, le=100)
    max_risk_score: Optional[int] = Field(None, ge=0, le=100)
    min_duration: Optional[int] = None  # minutes
    max_duration: Optional[int] = None  # minutes
    min_requests: Optional[int] = Field(None, ge=1)
    max_requests: Optional[int] = Field(None, ge=1)
    risk_level: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)

class AlertResponse(BaseModel):
    """Response model for alerts"""
    id: UUID
    title: str
    description: Optional[str] = None
    severity: str
    alert_type: str
    status: str
    source_type: str
    source_id: Optional[UUID] = None
    related_request_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None

class AlertCreate(BaseModel):
    """Create model for alerts"""
    title: str
    description: Optional[str] = None
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    alert_type: str
    source_type: str = Field(..., pattern="^(detection_rule|threshold|system)$")
    source_id: Optional[UUID] = None
    related_request_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None

class AlertUpdate(BaseModel):
    """Update model for alerts"""
    status: Optional[str] = Field(None, pattern="^(new|acknowledged|resolved)$")
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None

class AlertRuleResponse(BaseModel):
    """Response model for alert rules"""
    id: UUID
    name: str
    description: Optional[str] = None
    rule_type: str
    is_active: bool
    severity: str
    threshold_config: Optional[Dict[str, Any]] = None
    detection_rule_ids: Optional[List[UUID]] = None
    notifications: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class AlertRuleCreate(BaseModel):
    """Create model for alert rules"""
    name: str
    description: Optional[str] = None
    rule_type: str = Field(..., pattern="^(threshold|detection_rule)$")
    is_active: bool = True
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    threshold_config: Optional[Dict[str, Any]] = None
    detection_rule_ids: Optional[List[str]] = None  # String UUIDs from frontend
    notifications: Optional[Dict[str, Any]] = None

class AlertRuleUpdate(BaseModel):
    """Update model for alert rules"""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, pattern="^(threshold|detection_rule)$")
    is_active: Optional[bool] = None
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    threshold_config: Optional[Dict[str, Any]] = None
    detection_rule_ids: Optional[List[str]] = None
    notifications: Optional[Dict[str, Any]] = None

class AlertFilters(BaseModel):
    """Query filters for alert endpoints"""
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    status: Optional[str] = Field(None, pattern="^(new|acknowledged|resolved)$")
    alert_type: Optional[str] = None
    source_type: Optional[str] = Field(None, pattern="^(detection_rule|threshold|system)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)

class BulkAlertOperation(BaseModel):
    """Bulk operations on alerts"""
    alert_ids: List[str]
    operation: str = Field(..., pattern="^(acknowledge|resolve|archive)$")
    user: Optional[str] = None

class SystemSettingResponse(BaseModel):
    """Response model for system settings"""
    id: UUID
    key: str
    value: str
    description: Optional[str] = None
    category: str
    created_at: datetime
    updated_at: datetime

class SystemSettingUpdate(BaseModel):
    """Update model for system settings"""
    value: str

class DatabaseStatsResponse(BaseModel):
    """Response model for database statistics"""
    total_requests: int
    total_alerts: int
    total_sessions: int
    total_detection_rules: int
    database_size_mb: float
    table_sizes: Dict[str, Dict[str, Any]]  # {"table_name": {"size_mb": 1.2, "rows": 1000}}

class ExportRequest(BaseModel):
    """Request model for data export"""
    data_type: str = Field(..., pattern="^(requests|alerts|sessions)$")
    format: str = Field(..., pattern="^(csv|json)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_encrypted: bool = False  # Reserved for future use

class UserResponse(BaseModel):
    """Response model for users"""
    id: UUID
    username: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    role: UserRole
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    """Create model for users"""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        pattern="^[a-zA-Z0-9_-]+$",
        description="Username must be 3-50 characters, using only letters, numbers, hyphens, and underscores"
    )
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    role: UserRole = UserRole.READ_ONLY
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""

class UserUpdate(BaseModel):
    """Update model for users"""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    current_password: str
    new_password: str = Field(..., min_length=6, description="New password must be at least 6 characters")

class AdminPasswordResetRequest(BaseModel):
    """Admin password reset request model"""
    new_password: str = Field(..., min_length=6, description="New password must be at least 6 characters")