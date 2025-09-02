from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
import logging

from config import settings
from models import (
    LoginRequest, Token, User, UserRole, LLMRequestResponse, LLMRequestDetail, 
    DetectionRuleResponse, DetectionRuleCreate, DetectionRuleUpdate,
    PaginatedResponse, RequestFilters, StatsResponse, HealthResponse,
    SessionResponse, SessionDetail, SessionFilters, BulkRuleOperation, RuleTemplate,
    AlertResponse, AlertCreate, AlertUpdate, AlertFilters, BulkAlertOperation,
    SystemSettingResponse, SystemSettingUpdate, DatabaseStatsResponse, ExportRequest,
    UserResponse, UserCreate, UserUpdate, PasswordChangeRequest, AdminPasswordResetRequest
)
from auth import (
    authenticate_user, create_token_response, get_current_user, get_admin_user, update_admin_password
)
from database import DatabaseService
# from routes.security import router as security_router
# from middleware.rate_limiter import rate_limit_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="REST API for FlagWise",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware - temporarily disabled
# app.middleware("http")(rate_limit_middleware)

# Include security routes - temporarily disabled
# app.include_router(security_router)

# Initialize services
db_service = DatabaseService()

# Health Check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_connected = db_service.test_connection()
    
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        timestamp=datetime.utcnow(),
        version=settings.api_version,
        database_connected=db_connected
    )

# Authentication
@app.post("/auth/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return create_token_response(user)

@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# Requests Endpoints
@app.get("/requests", response_model=PaginatedResponse)
async def get_requests(
    flagged: Optional[bool] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    src_ip: Optional[str] = None,
    min_risk_score: Optional[int] = None,
    max_risk_score: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of LLM requests with filters"""
    if page_size > settings.max_page_size:
        page_size = settings.max_page_size
    
    filters = RequestFilters(
        flagged=flagged,
        provider=provider,
        model=model,
        src_ip=src_ip,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        page_size=page_size
    )
    
    try:
        admin_view = current_user.role == UserRole.ADMIN
        records, total_count = db_service.get_requests(filters, admin_view)
        
        # Convert to appropriate response models
        if admin_view:
            items = [LLMRequestDetail(**record) for record in records]
        else:
            items = [LLMRequestResponse(**record) for record in records]
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to get requests: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/requests/{request_id}")
async def get_request_by_id(
    request_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get a single request by ID"""
    try:
        admin_view = current_user.role == UserRole.ADMIN
        record = db_service.get_request_by_id(request_id, admin_view)
        
        if not record:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if admin_view:
            return LLMRequestDetail(**record)
        else:
            return LLMRequestResponse(**record)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get request {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Statistics Endpoints
@app.get("/stats/totals", response_model=StatsResponse)
async def get_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get system statistics"""
    try:
        stats = db_service.get_statistics(days)
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Detection Rules Endpoints (Admin only)
@app.get("/rules", response_model=PaginatedResponse)
async def get_detection_rules(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    rule_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin_user: User = Depends(get_admin_user)
):
    """Get paginated list of detection rules with filters (Admin only)"""
    if page_size > settings.max_page_size:
        page_size = settings.max_page_size
    
    try:
        rules, total_count = db_service.get_detection_rules_paginated(
            page=page,
            page_size=page_size,
            search=search,
            rule_type=rule_type,
            is_active=is_active
        )
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=rules,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    except Exception as e:
        logger.error(f"Failed to get detection rules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/rules", response_model=DetectionRuleResponse)
async def create_detection_rule(
    rule: DetectionRuleCreate,
    admin_user: User = Depends(get_admin_user)
):
    """Create a new detection rule (Admin only)"""
    try:
        created_rule = db_service.create_detection_rule(rule.dict())
        return created_rule
    except Exception as e:
        logger.error(f"Failed to create detection rule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/rules/{rule_id}", response_model=DetectionRuleResponse)
async def update_detection_rule(
    rule_id: UUID,
    rule_update: DetectionRuleUpdate,
    admin_user: User = Depends(get_admin_user)
):
    """Update a detection rule (Admin only)"""
    try:
        # Only include non-None fields in update
        update_data = {k: v for k, v in rule_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_rule = db_service.update_detection_rule(rule_id, update_data)
        
        if not updated_rule:
            raise HTTPException(status_code=404, detail="Detection rule not found")
        
        return updated_rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update detection rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/rules/{rule_id}")
async def delete_detection_rule(
    rule_id: UUID,
    admin_user: User = Depends(get_admin_user)
):
    """Delete a detection rule (Admin only)"""
    try:
        deleted = db_service.delete_detection_rule(rule_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Detection rule not found")
        
        return {"message": "Detection rule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete detection rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/rules/bulk")
async def bulk_rule_operation(
    operation: BulkRuleOperation,
    admin_user: User = Depends(get_admin_user)
):
    """Perform bulk operations on detection rules (Admin only)"""
    try:
        if operation.operation == "enable":
            updated_count = db_service.bulk_enable_rules(operation.rule_ids)
        elif operation.operation == "disable":
            updated_count = db_service.bulk_disable_rules(operation.rule_ids)
        elif operation.operation == "delete":
            updated_count = db_service.bulk_delete_rules(operation.rule_ids)
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")
        
        return {"message": f"Successfully {operation.operation}d {updated_count} rules"}
    except Exception as e:
        logger.error(f"Failed to perform bulk operation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/rules/templates", response_model=List[RuleTemplate])
async def get_rule_templates(admin_user: User = Depends(get_admin_user)):
    """Get built-in rule templates (Admin only)"""
    templates = [
        # Data Privacy Templates
        RuleTemplate(
            name="Credit Card Numbers (PCI-DSS)",
            description="Detects credit card numbers in prompts",
            category="data_privacy",
            rule_type="regex",
            pattern=r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            severity="critical",
            points=80,
            examples=["4532-1234-5678-9012", "5555 1234 5678 9012"]
        ),
        RuleTemplate(
            name="Social Security Numbers",
            description="Detects US Social Security Numbers",
            category="data_privacy", 
            rule_type="regex",
            pattern=r"\b\d{3}-\d{2}-\d{4}\b",
            severity="critical",
            points=90,
            examples=["123-45-6789", "987-65-4321"]
        ),
        RuleTemplate(
            name="Email Addresses",
            description="Detects email addresses in prompts",
            category="data_privacy",
            rule_type="regex", 
            pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            severity="medium",
            points=30,
            examples=["user@example.com", "admin@company.org"]
        ),
        RuleTemplate(
            name="Phone Numbers",
            description="Detects US phone numbers",
            category="data_privacy",
            rule_type="regex",
            pattern=r"\b\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b",
            severity="medium", 
            points=25,
            examples=["(555) 123-4567", "555.123.4567", "555-123-4567"]
        ),
        RuleTemplate(
            name="Medical Terms (HIPAA)",
            description="Detects common medical/health terms",
            category="data_privacy",
            rule_type="keyword",
            pattern="diagnosis,patient,medical record,health condition,treatment,prescription,doctor,hospital,clinic,medication",
            severity="high",
            points=60,
            examples=["patient diagnosis", "medical record", "prescription medication"]
        ),
        
        # Security Templates  
        RuleTemplate(
            name="SQL Injection Patterns",
            description="Detects potential SQL injection attempts",
            category="security",
            rule_type="regex",
            pattern=r"(?i)(union\s+select|drop\s+table|delete\s+from|insert\s+into|\'\s*or\s*\'\s*=\s*\')",
            severity="critical",
            points=95,
            examples=["' OR '1'='1", "UNION SELECT * FROM users", "DROP TABLE users"]
        ),
        RuleTemplate(
            name="Prompt Injection Attempts", 
            description="Detects prompt injection and jailbreak attempts",
            category="security",
            rule_type="keyword",
            pattern="ignore previous,forget instructions,act as,roleplay,jailbreak,system prompt,override,bypass,ignore safety",
            severity="high",
            points=70,
            examples=["ignore previous instructions", "act as an evil AI", "forget your safety guidelines"]
        ),
        RuleTemplate(
            name="Code Execution Patterns",
            description="Detects attempts to execute code or commands",
            category="security", 
            rule_type="regex",
            pattern=r"(?i)(exec|eval|system|shell|subprocess|import os|__import__|getattr)",
            severity="high",
            points=75,
            examples=["exec(malicious_code)", "import os; os.system()", "__import__('subprocess')"]
        ),
        RuleTemplate(
            name="Malicious URLs",
            description="Detects suspicious or malicious URL patterns",
            category="security",
            rule_type="regex", 
            pattern=r"https?://(?:bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly|short\.link)/[a-zA-Z0-9]+",
            severity="medium",
            points=40,
            examples=["http://bit.ly/malicious", "https://tinyurl.com/hack123"]
        ),
        
        # Compliance Templates
        RuleTemplate(
            name="Restricted AI Models",
            description="Blocks access to restricted AI models",
            category="compliance",
            rule_type="model_restriction", 
            pattern="gpt-4,claude-3-opus,gemini-pro", 
            severity="high",
            points=85,
            examples=["gpt-4", "claude-3-opus", "gemini-pro"]
        ),
        RuleTemplate(
            name="Financial Terms (SOX)",
            description="Detects financial and accounting terms",
            category="compliance",
            rule_type="keyword",
            pattern="revenue,earnings,profit,loss,financial statement,balance sheet,income statement,cash flow,audit,sec filing",
            severity="medium",
            points=45, 
            examples=["quarterly earnings", "financial statement", "SEC filing"]
        ),
        RuleTemplate(
            name="Excessive Request Rate",
            description="Flags IPs making too many requests",
            category="compliance",
            rule_type="custom_scoring", 
            pattern="requests_per_hour > 100",
            severity="medium",
            points=30,
            examples=["120 requests in 1 hour", "Rapid-fire API calls"]
        )
    ]
    
    return templates

# Sessions Endpoints
@app.get("/sessions", response_model=PaginatedResponse)
async def get_sessions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    src_ip: Optional[str] = None,
    min_risk_score: Optional[int] = None,
    max_risk_score: Optional[int] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    min_requests: Optional[int] = None,
    max_requests: Optional[int] = None,
    risk_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of user sessions with filters"""
    if page_size > settings.max_page_size:
        page_size = settings.max_page_size
    
    filters = SessionFilters(
        start_date=start_date,
        end_date=end_date,
        src_ip=src_ip,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        min_duration=min_duration,
        max_duration=max_duration,
        min_requests=min_requests,
        max_requests=max_requests,
        risk_level=risk_level,
        page=page,
        page_size=page_size
    )
    
    try:
        admin_view = current_user.role == UserRole.ADMIN
        sessions, total_count = db_service.get_sessions(filters, admin_view)
        
        # Convert to response models
        items = [SessionResponse(**session) for session in sessions]
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_by_id(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed session information by ID"""
    try:
        admin_view = current_user.role == UserRole.ADMIN
        session_detail = db_service.get_session_detail(session_id, admin_view)
        
        if not session_detail:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionDetail(**session_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Alerts Endpoints
@app.get("/alerts", response_model=PaginatedResponse)
async def get_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    alert_type: Optional[str] = None,
    source_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of alerts with filters"""
    if page_size > settings.max_page_size:
        page_size = settings.max_page_size
    
    filters = AlertFilters(
        severity=severity,
        status=status,
        alert_type=alert_type,
        source_type=source_type,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        page_size=page_size
    )
    
    try:
        admin_view = current_user.role == UserRole.ADMIN
        alerts, total_count = db_service.get_alerts(filters, admin_view)
        
        # Convert to response models
        items = [AlertResponse(**alert) for alert in alerts]
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new alert"""
    try:
        alert_data = db_service.create_alert(alert.dict())
        return AlertResponse(**alert_data)
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    alert_update: AlertUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an alert (acknowledge/resolve)"""
    try:
        updated_alert = db_service.update_alert(alert_id, alert_update, current_user.username)
        
        if not updated_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return AlertResponse(**updated_alert)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/alerts/bulk")
async def bulk_alert_operation(
    operation: BulkAlertOperation,
    current_user: User = Depends(get_current_user)
):
    """Perform bulk operations on alerts"""
    try:
        updated_count = db_service.bulk_alert_operation(
            operation.alert_ids, 
            operation.operation, 
            current_user.username
        )
        
        return {"message": f"Successfully {operation.operation}d {updated_count} alerts"}
    except Exception as e:
        logger.error(f"Failed to perform bulk alert operation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/alerts/stats")
async def get_alert_stats(current_user: User = Depends(get_current_user)):
    """Get alert statistics"""
    try:
        stats = db_service.get_alert_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get alert stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Settings Endpoints (Admin only)
@app.get("/settings", response_model=List[SystemSettingResponse])
async def get_system_settings(
    category: Optional[str] = None,
    admin_user: User = Depends(get_admin_user)
):
    """Get system settings, optionally filtered by category"""
    try:
        settings_list = db_service.get_system_settings(category)
        return [SystemSettingResponse(**setting) for setting in settings_list]
    except Exception as e:
        logger.error(f"Failed to get system settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/settings/{setting_key}", response_model=SystemSettingResponse)
async def update_system_setting(
    setting_key: str,
    setting_update: SystemSettingUpdate,
    admin_user: User = Depends(get_admin_user)
):
    """Update a system setting value"""
    try:
        updated_setting = db_service.update_system_setting(setting_key, setting_update.value)
        return SystemSettingResponse(**updated_setting)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update system setting {setting_key}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/settings/database/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(admin_user: User = Depends(get_admin_user)):
    """Get comprehensive database statistics"""
    try:
        stats = db_service.get_database_stats()
        return DatabaseStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/settings/database/cleanup")
async def manual_cleanup(admin_user: User = Depends(get_admin_user)):
    """Manually trigger database cleanup"""
    try:
        import psycopg2.extras
        with db_service.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT cleanup_old_data() as result")
            result = cursor.fetchone()
            cleanup_data = result['result']
            
        return {
            "message": "Database cleanup completed successfully",
            "cleanup_stats": cleanup_data
        }
    except Exception as e:
        logger.error(f"Failed to perform manual cleanup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/settings/database/purge")
async def purge_all_data(admin_user: User = Depends(get_admin_user)):
    """Purge all collected data from the database"""
    try:
        import psycopg2.extras
        with db_service.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT purge_all_data() as result")
            result = cursor.fetchone()
            purge_data = result['result']
            conn.commit()
            
        return {
            "message": "All data purged successfully",
            "purge_stats": purge_data
        }
    except Exception as e:
        logger.error(f"Failed to purge all data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/export")
async def export_data(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Export data with date range filtering"""
    try:
        # Get max export limit from settings
        max_limit_result = db_service.get_system_settings()
        max_limit = 100000  # default
        for setting in max_limit_result:
            if setting['key'] == 'max_export_records':
                max_limit = int(setting['value'])
                break
        
        # Export data
        export_result = db_service.export_data(
            export_request.data_type,
            export_request.start_date,
            export_request.end_date,
            max_limit
        )
        
        # Format response based on requested format
        if export_request.format == 'csv':
            # Convert to CSV format
            import io
            import csv
            from datetime import datetime
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(export_result['columns'])
            
            # Write data rows, converting non-string types
            for row in export_result['data']:
                csv_row = []
                for item in row:
                    if isinstance(item, datetime):
                        csv_row.append(item.isoformat())
                    elif isinstance(item, (dict, list)):
                        import json
                        csv_row.append(json.dumps(item))
                    else:
                        csv_row.append(str(item) if item is not None else '')
                writer.writerow(csv_row)
            
            csv_content = output.getvalue()
            output.close()
            
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename="{export_request.data_type}_export.csv"'}
            )
        
        else:  # JSON format
            import json
            from datetime import datetime
            
            # Convert datetime and decimal objects for JSON serialization
            def serialize_objects(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif hasattr(obj, '__float__'):  # Handle Decimal objects
                    return float(obj)
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            # Format as JSON
            json_data = {
                'export_info': {
                    'data_type': export_request.data_type,
                    'format': export_request.format,
                    'start_date': export_request.start_date.isoformat() if export_request.start_date else None,
                    'end_date': export_request.end_date.isoformat() if export_request.end_date else None,
                    'total_records': export_result['total_exported'],
                    'exported_at': datetime.utcnow().isoformat()
                },
                'columns': export_result['columns'],
                'data': []
            }
            
            # Convert rows to dictionaries
            for row in export_result['data']:
                row_dict = {}
                for i, column in enumerate(export_result['columns']):
                    value = row[i]
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    elif hasattr(value, '__float__'):  # Handle Decimal objects
                        value = float(value)
                    row_dict[column] = value
                json_data['data'].append(row_dict)
            
            json_content = json.dumps(json_data, indent=2, default=serialize_objects)
            
            from fastapi.responses import Response
            return Response(
                content=json_content,
                media_type='application/json',
                headers={'Content-Disposition': f'attachment; filename="{export_request.data_type}_export.json"'}
            )
    
    except Exception as e:
        logger.error(f"Failed to export {export_request.data_type} data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# User Management Endpoints (Admin only)
@app.get("/users", response_model=PaginatedResponse)
async def get_users(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin_user: User = Depends(get_admin_user)
):
    """Get paginated list of users with filters (Admin only)"""
    if page_size > settings.max_page_size:
        page_size = settings.max_page_size
    
    try:
        users, total_count = db_service.get_users_paginated(
            page=page,
            page_size=page_size,
            search=search,
            role=role,
            is_active=is_active
        )
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=[UserResponse(**user) for user in users],
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    admin_user: User = Depends(get_admin_user)
):
    """Create a new user (Admin only)"""
    try:
        created_user = db_service.create_user(user.dict())
        return UserResponse(**created_user)
    except Exception as e:
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=409, detail="Username already exists")
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    admin_user: User = Depends(get_admin_user)
):
    """Update a user (Admin only)"""
    try:
        # Only include non-None fields in update
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_user = db_service.update_user(user_id, update_data)
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(**updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    admin_user: User = Depends(get_admin_user)
):
    """Delete a user (Admin only)"""
    try:
        deleted = db_service.delete_user(user_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/users/change-password")
async def change_password(
    password_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user)
):
    """Change current user's password"""
    try:
        # Special handling for hardcoded admin
        if current_user.username == "admin":
            # Verify current password
            from auth import verify_password, _admin_password_hash
            if not verify_password(password_request.current_password, _admin_password_hash):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            
            # Update admin password
            update_admin_password(password_request.new_password)
            return {"message": "Admin password changed successfully"}
        
        # For database users
        db_user = db_service.get_user_by_username(current_user.username)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        from auth import verify_password
        if not verify_password(password_request.current_password, db_user['password_hash']):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password
        db_service.update_user(db_user['id'], {'password': password_request.new_password})
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change password for user {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: UUID,
    password_request: AdminPasswordResetRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Reset password for any user (Admin only)"""
    try:
        # Get the target user
        target_user = db_service.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password
        updated = db_service.update_user(user_id, {'password': password_request.new_password})
        
        if not updated:
            raise HTTPException(status_code=404, detail="Failed to change password")
        
        return {"message": f"Password changed successfully for user {target_user['username']}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change password for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/users/profile/name")
async def update_profile_name(
    name_request: dict,
    current_user: User = Depends(get_current_user)
):
    """Update current user's first and last name"""
    try:
        first_name = name_request.get('first_name', '').strip()
        last_name = name_request.get('last_name', '').strip()
        
        # Get current user from database
        db_user = db_service.get_user_by_username(current_user.username)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update name fields
        updated_user = db_service.update_user(db_user['id'], {
            'first_name': first_name,
            'last_name': last_name
        })
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="Failed to update name")
        
        return {
            "message": "Name updated successfully", 
            "first_name": first_name,
            "last_name": last_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update name for user {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/users/profile/username")
async def update_profile_username(
    username_request: dict,
    current_user: User = Depends(get_current_user)
):
    """Update current user's username"""
    try:
        # Can't update hardcoded admin username
        if current_user.username == "admin":
            raise HTTPException(status_code=400, detail="Cannot change username for system admin account")
        
        new_username = username_request.get('username')
        if not new_username:
            raise HTTPException(status_code=400, detail="Username is required")
        
        if len(new_username.strip()) == 0:
            raise HTTPException(status_code=400, detail="Username cannot be empty")
        
        # Check if username already exists
        existing_user = db_service.get_user_by_username(new_username)
        if existing_user and existing_user['username'] != current_user.username:
            raise HTTPException(status_code=409, detail="Username already exists")
        
        # Get current user from database
        db_user = db_service.get_user_by_username(current_user.username)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update username
        updated_user = db_service.update_user(db_user['id'], {'username': new_username})
        if not updated_user:
            raise HTTPException(status_code=404, detail="Failed to update username")
        
        return {"message": "Username updated successfully", "username": new_username}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update username for user {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Kafka Data Sources Endpoints (Admin only)
@app.post("/kafka/test-connection")
async def test_kafka_connection(
    kafka_config: dict,
    admin_user: User = Depends(get_admin_user)
):
    """Test Kafka connection with provided configuration"""
    try:
        from confluent_kafka import Consumer, KafkaError
        import json
        
        # Build Kafka configuration
        config = {
            'bootstrap.servers': kafka_config.get('kafka_brokers', 'localhost:9092'),
            'group.id': kafka_config.get('kafka_group_id', 'flagwise-test'),
            'auto.offset.reset': 'latest'
        }
        
        # Add authentication if specified
        auth_type = kafka_config.get('kafka_auth_type', 'none')
        if auth_type == 'sasl_plain':
            config.update({
                'security.protocol': 'SASL_PLAINTEXT',
                'sasl.mechanism': 'PLAIN',
                'sasl.username': kafka_config.get('kafka_username', ''),
                'sasl.password': kafka_config.get('kafka_password', '')
            })
        elif auth_type == 'sasl_ssl':
            config.update({
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'PLAIN',
                'sasl.username': kafka_config.get('kafka_username', ''),
                'sasl.password': kafka_config.get('kafka_password', ''),
                'ssl.ca.location': '/tmp/kafka_ca.pem' if kafka_config.get('kafka_ssl_ca') else None
            })
        elif auth_type == 'ssl':
            config.update({
                'security.protocol': 'SSL',
                'ssl.ca.location': '/tmp/kafka_ca.pem' if kafka_config.get('kafka_ssl_ca') else None,
                'ssl.certificate.location': '/tmp/kafka_cert.pem' if kafka_config.get('kafka_ssl_cert') else None,
                'ssl.key.location': '/tmp/kafka_key.pem' if kafka_config.get('kafka_ssl_key') else None
            })
        
        # Test connection
        consumer = Consumer(config)
        
        # Try to get metadata (this tests connectivity)
        metadata = consumer.list_topics(timeout=10)
        
        topic = kafka_config.get('kafka_topic', 'llm-traffic-logs')
        topic_exists = topic in metadata.topics
        
        consumer.close()
        
        return {
            "status": "success",
            "message": "Successfully connected to Kafka",
            "broker_count": len(metadata.brokers),
            "topic_exists": topic_exists,
            "available_topics": list(metadata.topics.keys())[:10]  # First 10 topics
        }
        
    except Exception as e:
        logger.error(f"Kafka connection test failed: {e}")
        return {
            "status": "error", 
            "message": f"Connection failed: {str(e)}"
        }

@app.post("/kafka/save-configuration")
async def save_kafka_configuration(
    kafka_config: dict,
    admin_user: User = Depends(get_admin_user)
):
    """Save Kafka configuration and restart consumer service"""
    try:
        import os
        
        # Update each Kafka setting in the database
        kafka_settings_map = {
            'kafka_enabled': str(kafka_config.get('kafka_enabled', False)).lower(),
            'kafka_brokers': kafka_config.get('kafka_brokers', 'localhost:9092'),
            'kafka_topic': kafka_config.get('kafka_topic', 'llm-traffic-logs'),
            'kafka_group_id': kafka_config.get('kafka_group_id', 'flagwise-consumer'),
            'kafka_auth_type': kafka_config.get('kafka_auth_type', 'none'),
            'kafka_username': kafka_config.get('kafka_username', ''),
            'kafka_password': kafka_config.get('kafka_password', ''),  # TODO: Encrypt this
            'kafka_ssl_cert': kafka_config.get('kafka_ssl_cert', ''),
            'kafka_ssl_key': kafka_config.get('kafka_ssl_key', ''),
            'kafka_ssl_ca': kafka_config.get('kafka_ssl_ca', ''),
            'kafka_timeout_ms': kafka_config.get('kafka_timeout_ms', '30000'),
            'kafka_retry_backoff_ms': kafka_config.get('kafka_retry_backoff_ms', '1000'),
            'kafka_message_schema': kafka_config.get('kafka_message_schema', '{}')
        }
        
        # Save to database
        for key, value in kafka_settings_map.items():
            db_service.update_system_setting(key, value)
        
        # Update .env file
        env_updates = {
            'KAFKA_ENABLED': kafka_settings_map['kafka_enabled'],
            'KAFKA_BROKERS': kafka_settings_map['kafka_brokers'],
            'KAFKA_TOPIC': kafka_settings_map['kafka_topic'],
            'KAFKA_GROUP_ID': kafka_settings_map['kafka_group_id'],
            'KAFKA_AUTH_TYPE': kafka_settings_map['kafka_auth_type'],
            'KAFKA_USERNAME': kafka_settings_map['kafka_username'],
            'KAFKA_PASSWORD': kafka_settings_map['kafka_password'],
            'KAFKA_TIMEOUT_MS': kafka_settings_map['kafka_timeout_ms'],
            'KAFKA_RETRY_BACKOFF_MS': kafka_settings_map['kafka_retry_backoff_ms']
        }
        
        # Read current .env file
        env_path = '/app/.env'  # Path inside container
        env_content = {}
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_content[key] = value
        
        # Update with new values
        env_content.update(env_updates)
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        # Restart consumer service using docker command
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'restart', 'flagwise-consumer'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                restart_message = "Consumer service restarted successfully"
            else:
                restart_message = f"Consumer restart warning: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            restart_message = "Consumer restart timed out, but configuration was saved"
        except Exception as restart_error:
            restart_message = f"Could not restart consumer: {str(restart_error)}"
        
        return {
            "message": "Kafka configuration saved successfully",
            "restart_status": restart_message
        }
        
    except Exception as e:
        logger.error(f"Failed to save Kafka configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/kafka/demo-data/toggle")
async def toggle_demo_data(
    action: dict,  # {"enabled": true/false}
    admin_user: User = Depends(get_admin_user)
):
    """Toggle demo data generation and optionally clear existing data"""
    try:
        enabled = action.get('enabled', False)
        clear_data = action.get('clear_existing_data', False)
        
        # Update demo_data_enabled setting
        db_service.update_system_setting('demo_data_enabled', str(enabled).lower())
        
        messages = []
        
        if not enabled and clear_data:
            # Clear demo data from database
            # Delete LLM requests that don't have real source IPs (demo data typically uses fake IPs)
            deleted_count = db_service.execute_query("""
                DELETE FROM llm_requests 
                WHERE src_ip LIKE '192.168.%' OR src_ip LIKE '10.%' OR src_ip LIKE '172.%'
                RETURNING COUNT(*)
            """)
            messages.append(f"Cleared {deleted_count} demo records from database")
        
        # Control data generator container
        try:
            import subprocess
            
            if enabled:
                # Start data generator
                result = subprocess.run(
                    ['docker', 'start', 'shadow-ai-data-generator'],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if result.returncode == 0:
                    messages.append("Demo data generator started")
                else:
                    messages.append(f"Failed to start demo data generator: {result.stderr}")
            else:
                # Stop data generator
                result = subprocess.run(
                    ['docker', 'stop', 'shadow-ai-data-generator'],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if result.returncode == 0:
                    messages.append("Demo data generator stopped")
                else:
                    messages.append(f"Failed to stop demo data generator: {result.stderr}")
                    
        except Exception as container_error:
            messages.append(f"Container control error: {str(container_error)}")
        
        return {
            "message": "Demo data settings updated",
            "enabled": enabled,
            "details": messages
        }
        
    except Exception as e:
        logger.error(f"Failed to toggle demo data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/kafka/status")
async def get_kafka_status(admin_user: User = Depends(get_admin_user)):
    """Get current Kafka connection and consumer status"""
    try:
        # Get Kafka settings from database
        kafka_settings = {}
        settings = db_service.get_system_settings('data_sources')
        for setting in settings:
            if setting['key'].startswith('kafka_') or setting['key'] == 'demo_data_enabled':
                kafka_settings[setting['key']] = setting['value']
        
        # TODO: Check actual consumer service health
        # For now, return based on kafka_enabled setting
        is_enabled = kafka_settings.get('kafka_enabled', 'false') == 'true'
        
        return {
            "kafka_enabled": is_enabled,
            "demo_data_enabled": kafka_settings.get('demo_data_enabled', 'false') == 'true',
            "connection_status": "connected" if is_enabled else "disconnected",
            "last_message_time": None,  # TODO: Implement actual message tracking
            "consumer_health": "unknown"  # TODO: Implement health check
        }
        
    except Exception as e:
        logger.error(f"Failed to get Kafka status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Demo data endpoints
@app.get("/demo/status")
async def get_demo_status(admin_user: User = Depends(get_admin_user)):
    """Get current demo data status"""
    try:
        settings = db_service.get_system_settings('data_sources')
        demo_enabled = False
        for setting in settings:
            if setting['key'] == 'demo_data_enabled':
                demo_enabled = setting['value'].lower() == 'true'
                break
        
        return {
            "enabled": demo_enabled,
            "status": "running" if demo_enabled else "stopped"
        }
        
    except Exception as e:
        logger.error(f"Failed to get demo status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/demo/toggle")
async def toggle_demo(
    request: dict,  # {"enabled": true/false}
    admin_user: User = Depends(get_admin_user)
):
    """Toggle demo data generation on/off (admin only)"""
    try:
        enabled = request.get('enabled', False)
        
        # Update demo_data_enabled setting
        db_service.update_system_setting('demo_data_enabled', str(enabled).lower())
        
        # Control data generator container
        messages = []
        try:
            import subprocess
            
            if enabled:
                # Start data generator container
                result = subprocess.run(
                    ['docker', 'start', 'shadow-ai-data-generator'],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if result.returncode == 0:
                    messages.append("Demo data generator started")
                else:
                    messages.append(f"Failed to start demo data generator: {result.stderr}")
            else:
                # Stop data generator container
                result = subprocess.run(
                    ['docker', 'stop', 'shadow-ai-data-generator'],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if result.returncode == 0:
                    messages.append("Demo data generator stopped")
                else:
                    messages.append(f"Failed to stop demo data generator: {result.stderr}")
                    
        except Exception as container_error:
            messages.append(f"Container control warning: {str(container_error)}")
        
        return {
            "success": True,
            "enabled": enabled,
            "message": f"Demo data {'enabled' if enabled else 'disabled'} successfully",
            "details": messages
        }
        
    except Exception as e:
        logger.error(f"Failed to toggle demo data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics endpoints
@app.get("/analytics/volume-trends")
async def get_volume_trends(
    time_range: str = "daily",  # hourly, daily, weekly, monthly
    date_range: str = "7d",     # 24h, 7d, 30d, 90d
    provider: Optional[str] = None,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get request volume trends for analytics"""
    try:
        return db_service.get_volume_trends(time_range, date_range, provider, model)
    except Exception as e:
        logger.error(f"Failed to get volume trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/threat-trends")
async def get_threat_trends(
    time_range: str = "daily",
    date_range: str = "7d", 
    provider: Optional[str] = None,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get threat detection rate trends"""
    try:
        return db_service.get_threat_trends(time_range, date_range, provider, model)
    except Exception as e:
        logger.error(f"Failed to get threat trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/model-usage")
async def get_model_usage(
    time_range: str = "daily",
    date_range: str = "7d",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get model usage patterns"""
    try:
        return db_service.get_model_usage(time_range, date_range, provider, model)
    except Exception as e:
        logger.error(f"Failed to get model usage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/provider-breakdown")
async def get_provider_breakdown(
    time_range: str = "daily",
    date_range: str = "7d",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get provider distribution"""
    try:
        return db_service.get_provider_breakdown(time_range, date_range, provider, model)
    except Exception as e:
        logger.error(f"Failed to get provider breakdown: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/key-metrics")
async def get_key_metrics(
    time_range: str = "daily",
    date_range: str = "7d",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get key analytics metrics"""
    try:
        return db_service.get_key_metrics(time_range, date_range, provider, model)
    except Exception as e:
        logger.error(f"Failed to get key metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/anomalies")
async def get_anomalies(
    time_range: str = "daily",
    date_range: str = "7d",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get detected anomalies in trends"""
    try:
        return db_service.get_anomalies(time_range, date_range, provider, model)
    except Exception as e:
        logger.error(f"Failed to get anomalies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/filter-options")
async def get_filter_options(current_user: User = Depends(get_current_user)):
    """Get available filter options (providers, models)"""
    try:
        return db_service.get_analytics_filter_options()
    except Exception as e:
        logger.error(f"Failed to get filter options: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/export/{format}")
async def export_analytics(
    format: str,  # csv, png
    time_range: str = "daily",
    date_range: str = "7d",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export analytics data in specified format"""
    try:
        if format not in ["csv", "png"]:
            raise HTTPException(status_code=400, detail="Invalid export format")
        
        data = db_service.export_analytics(format, time_range, date_range, provider, model)
        
        if format == "csv":
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                content=data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=analytics_{date_range}.csv"}
            )
        elif format == "png":
            from fastapi.responses import Response
            return Response(
                content=data,
                media_type="image/png",
                headers={"Content-Disposition": f"attachment; filename=analytics_{date_range}.png"}
            )
            
    except Exception as e:
        logger.error(f"Failed to export analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/analytics/refresh-aggregates")
async def refresh_analytics_aggregates(admin_user: User = Depends(get_admin_user)):
    """Refresh analytics aggregation tables"""
    try:
        db_service.refresh_analytics_aggregates()
        return {"message": "Analytics aggregates refreshed successfully"}
    except Exception as e:
        logger.error(f"Failed to refresh analytics aggregates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )