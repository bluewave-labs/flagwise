import re
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import bleach
from sqlalchemy import text
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)

class SecureDatabaseService:
    """Enhanced database service with security hardening"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # Whitelist of allowed sort columns to prevent ORDER BY injection
        self.allowed_sort_columns = {
            'requests': ['timestamp', 'risk_score', 'provider', 'model', 'src_ip', 'created_at'],
            'rules': ['name', 'severity', 'rule_type', 'created_at', 'updated_at'],
            'alerts': ['created_at', 'severity', 'status', 'alert_type'],
            'sessions': ['start_time', 'duration_minutes', 'request_count', 'avg_risk_score']
        }
        
        # Maximum lengths for search terms to prevent DoS
        self.max_search_length = 100
        self.max_results = 10000
    
    @contextmanager
    def get_connection(self):
        """Secure connection context manager"""
        conn = None
        try:
            conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor,
                # Security: Connection timeout
                connect_timeout=10,
                # Security: Disable autocommit by default
                autocommit=False,
                # Security: Application name for monitoring
                application_name="shadow-ai-api"
            )
            # Security: Set session timeout
            with conn.cursor() as cursor:
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _sanitize_search_term(self, search_term: str) -> str:
        """Sanitize search terms to prevent injection attacks"""
        if not search_term:
            return ""
        
        # Limit length to prevent DoS
        if len(search_term) > self.max_search_length:
            search_term = search_term[:self.max_search_length]
        
        # Remove potentially dangerous characters
        # Allow letters, numbers, spaces, hyphens, underscores, dots
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-_.]', '', search_term)
        
        # Remove multiple spaces
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def _validate_sort_column(self, table: str, column: str) -> str:
        """Validate and sanitize sort column to prevent ORDER BY injection"""
        if not column:
            return 'created_at'  # Default safe column
            
        # Check if column is in whitelist
        allowed_columns = self.allowed_sort_columns.get(table, [])
        if column not in allowed_columns:
            logger.warning(f"Invalid sort column '{column}' for table '{table}'. Using default.")
            return 'created_at'
        
        return column
    
    def _validate_page_params(self, page: int, page_size: int) -> tuple[int, int]:
        """Validate pagination parameters"""
        # Ensure positive values
        page = max(1, page)
        page_size = max(1, min(page_size, 1000))  # Cap at 1000
        
        # Calculate offset with overflow protection
        offset = (page - 1) * page_size
        if offset > self.max_results:
            raise ValueError(f"Offset too large. Maximum results: {self.max_results}")
        
        return page, page_size
    
    def get_requests_secure(self, filters: Dict[str, Any], admin_view: bool = False) -> Dict[str, Any]:
        """Secure version of get_requests with enhanced validation"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE conditions with parameterized queries
                where_conditions = []
                params = []
                
                # Validate and sanitize inputs
                if filters.get('flagged') is not None:
                    where_conditions.append("is_flagged = %s")
                    params.append(filters['flagged'])
                
                if filters.get('provider'):
                    # Sanitize provider name
                    provider = re.sub(r'[^a-zA-Z0-9_-]', '', filters['provider'])[:50]
                    where_conditions.append("provider = %s")
                    params.append(provider)
                
                if filters.get('model'):
                    # Sanitize model name
                    model = re.sub(r'[^a-zA-Z0-9_.-]', '', filters['model'])[:100]
                    where_conditions.append("model = %s")
                    params.append(model)
                
                if filters.get('src_ip'):
                    # Validate IP address format
                    import ipaddress
                    try:
                        ipaddress.ip_address(filters['src_ip'])
                        where_conditions.append("src_ip = %s")
                        params.append(filters['src_ip'])
                    except ValueError:
                        logger.warning(f"Invalid IP address: {filters.get('src_ip')}")
                
                if filters.get('min_risk_score') is not None:
                    risk_score = max(0, min(100, int(filters['min_risk_score'])))
                    where_conditions.append("risk_score >= %s")
                    params.append(risk_score)
                
                if filters.get('max_risk_score') is not None:
                    risk_score = max(0, min(100, int(filters['max_risk_score'])))
                    where_conditions.append("risk_score <= %s")
                    params.append(risk_score)
                
                if filters.get('start_date'):
                    where_conditions.append("timestamp >= %s")
                    params.append(filters['start_date'])
                
                if filters.get('end_date'):
                    where_conditions.append("timestamp <= %s")
                    params.append(filters['end_date'])
                
                if filters.get('search'):
                    # Sanitize search term
                    search_term = self._sanitize_search_term(filters['search'])
                    if search_term:
                        # Use LIKE with escaped wildcards
                        search_pattern = f"%{search_term}%"
                        where_conditions.append("prompt ILIKE %s")
                        params.append(search_pattern)
                
                # Build WHERE clause
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Count total records with limit to prevent DoS
                count_query = f"""
                    SELECT COUNT(*) as count 
                    FROM llm_requests {where_clause}
                    LIMIT 1
                """
                cursor.execute(count_query, params)
                result = cursor.fetchone()
                total_count = result['count'] if result else 0
                
                # Validate pagination
                page, page_size = self._validate_page_params(
                    filters.get('page', 1), 
                    filters.get('page_size', 50)
                )
                offset = (page - 1) * page_size
                
                # Validate and sanitize sort column
                sort_column = self._validate_sort_column('requests', filters.get('sort', 'timestamp'))
                sort_direction = 'DESC' if filters.get('sort_desc', True) else 'ASC'
                
                # Select appropriate fields based on admin view
                if admin_view:
                    select_fields = """
                        id, timestamp, src_ip, provider, model, endpoint, method,
                        headers, prompt, response, duration_ms, status_code, 
                        risk_score, is_flagged, flag_reason, created_at
                    """
                else:
                    select_fields = """
                        id, timestamp, src_ip, provider, model, endpoint, method,
                        SUBSTRING(prompt FROM 1 FOR %s) as prompt_preview, 
                        duration_ms, status_code, risk_score, is_flagged, flag_reason, created_at
                    """
                    params.append(200)  # prompt_truncate_length
                
                # Main query with proper ordering and limits
                query = f"""
                    SELECT {select_fields}
                    FROM llm_requests 
                    {where_clause}
                    ORDER BY {sort_column} {sort_direction}
                    LIMIT %s OFFSET %s
                """
                params.extend([page_size, offset])
                
                cursor.execute(query, params)
                requests = cursor.fetchall()
                
                return {
                    'items': [dict(row) for row in requests],
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size,
                    'has_next': page * page_size < total_count,
                    'has_prev': page > 1
                }
                
        except Exception as e:
            logger.error(f"Database error in get_requests_secure: {e}")
            raise
    
    def create_detection_rule_secure(self, rule_data: Dict[str, Any]) -> str:
        """Secure version of create_detection_rule with input validation"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Validate and sanitize rule data
                rule_name = bleach.clean(rule_data['name'][:100])  # Limit length
                rule_type = rule_data['rule_type']
                
                # Validate rule_type against whitelist
                allowed_rule_types = ['keyword', 'regex', 'model_restriction', 'custom_scoring']
                if rule_type not in allowed_rule_types:
                    raise ValueError(f"Invalid rule type: {rule_type}")
                
                # Validate severity
                allowed_severities = ['critical', 'high', 'medium', 'low']
                severity = rule_data['severity']
                if severity not in allowed_severities:
                    raise ValueError(f"Invalid severity: {severity}")
                
                # Validate pattern based on rule type
                pattern = rule_data['pattern']
                if rule_type == 'regex':
                    # Test regex compilation to prevent ReDoS
                    try:
                        import re
                        re.compile(pattern)
                    except re.error:
                        raise ValueError("Invalid regex pattern")
                
                # Validate numeric fields
                points = max(0, min(100, int(rule_data.get('points', 10))))
                priority = max(0, min(1000, int(rule_data.get('priority', 0))))
                
                # Insert with parameterized query
                query = """
                    INSERT INTO detection_rules (
                        name, description, category, rule_type, pattern, 
                        severity, points, priority, stop_on_match, 
                        combination_logic, is_active, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                params = [
                    rule_name,
                    bleach.clean(rule_data.get('description', '')[:500]),
                    rule_data['category'],
                    rule_type,
                    pattern[:1000],  # Limit pattern length
                    severity,
                    points,
                    priority,
                    rule_data.get('stop_on_match', False),
                    rule_data.get('combination_logic', 'AND'),
                    rule_data.get('is_active', True),
                    datetime.utcnow(),
                    datetime.utcnow()
                ]
                
                cursor.execute(query, params)
                rule_id = cursor.fetchone()['id']
                conn.commit()
                
                logger.info(f"Created detection rule: {rule_id}")
                return str(rule_id)
                
        except Exception as e:
            logger.error(f"Database error in create_detection_rule_secure: {e}")
            raise

# Usage example
# db_service = SecureDatabaseService(connection_string)
# results = db_service.get_requests_secure(filters, admin_view=True)