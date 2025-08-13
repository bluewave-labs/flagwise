import psycopg2
import psycopg2.extras
from psycopg2 import sql
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime, timedelta
from uuid import UUID

from config import settings
from models import LLMRequestResponse, LLMRequestDetail, DetectionRuleResponse, RequestFilters, StatsResponse
from encryption_service import encryption_service

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.connection_params = {
            'host': settings.postgres_host,
            'port': settings.postgres_port,
            'database': settings.postgres_db,
            'user': settings.postgres_user,
            'password': settings.postgres_password,
        }
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_requests(self, filters: RequestFilters, admin_view: bool = False) -> Tuple[List[Dict], int]:
        """Get paginated LLM requests with filters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if filters.flagged is not None:
                    where_conditions.append("is_flagged = %s")
                    params.append(filters.flagged)
                
                if filters.provider:
                    where_conditions.append("LOWER(provider) = LOWER(%s)")
                    params.append(filters.provider)
                
                if filters.model:
                    where_conditions.append("LOWER(model) = LOWER(%s)")
                    params.append(filters.model)
                
                if filters.src_ip:
                    where_conditions.append("src_ip = %s")
                    params.append(filters.src_ip)
                
                if filters.min_risk_score is not None:
                    where_conditions.append("risk_score >= %s")
                    params.append(filters.min_risk_score)
                
                if filters.max_risk_score is not None:
                    where_conditions.append("risk_score <= %s")
                    params.append(filters.max_risk_score)
                
                if filters.start_date:
                    where_conditions.append("timestamp >= %s")
                    params.append(filters.start_date)
                
                if filters.end_date:
                    where_conditions.append("timestamp <= %s")
                    params.append(filters.end_date)
                
                if filters.search:
                    where_conditions.append("prompt ILIKE %s")
                    params.append(f"%{filters.search}%")
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Count total records
                count_query = f"SELECT COUNT(*) FROM llm_requests {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()['count']
                
                # Get paginated records
                offset = (filters.page - 1) * filters.page_size
                
                # Select appropriate fields based on admin view
                if admin_view:
                    select_fields = """
                        id, timestamp, src_ip, provider, model, endpoint, method,
                        headers, prompt, response, duration_ms, status_code, risk_score, is_flagged, flag_reason, created_at
                    """
                else:
                    select_fields = """
                        id, timestamp, src_ip, provider, model, endpoint, method,
                        SUBSTRING(prompt FROM 1 FOR %s) as prompt_preview, duration_ms, status_code, risk_score, is_flagged, flag_reason, created_at
                    """
                    params.append(settings.prompt_truncate_length)
                
                data_query = f"""
                    SELECT {select_fields}
                    FROM llm_requests 
                    {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT %s OFFSET %s
                """
                params.extend([filters.page_size, offset])
                
                cursor.execute(data_query, params)
                records = cursor.fetchall()
                
                # Decrypt sensitive fields for admin view
                decrypted_records = []
                for record in records:
                    record_dict = dict(record)
                    record_dict = self._decrypt_record(record_dict, admin_view)
                    decrypted_records.append(record_dict)
                
                return decrypted_records, total_count
                
        except Exception as e:
            logger.error(f"Failed to get requests: {e}")
            raise
    
    def _decrypt_record(self, record: Dict, admin_view: bool) -> Dict:
        """Decrypt sensitive fields in a record"""
        try:
            # Always decrypt for processing, but only return decrypted data for admin view
            decrypted_prompt = encryption_service.decrypt_prompt(record.get('prompt'))
            decrypted_response = encryption_service.decrypt_response(record.get('response'))
            decrypted_headers = encryption_service.decrypt_headers(record.get('headers'))
            
            if admin_view:
                # Admin gets full decrypted data
                record['prompt'] = decrypted_prompt
                record['response'] = decrypted_response
                record['headers'] = decrypted_headers
                # Also provide prompt_preview for model compatibility
                if decrypted_prompt:
                    record['prompt_preview'] = decrypted_prompt[:settings.prompt_truncate_length]
                    if len(decrypted_prompt) > settings.prompt_truncate_length:
                        record['prompt_preview'] += "..."
            else:
                # Non-admin gets truncated prompt preview
                if 'prompt_preview' not in record and decrypted_prompt:
                    record['prompt_preview'] = decrypted_prompt[:settings.prompt_truncate_length]
                    if len(decrypted_prompt) > settings.prompt_truncate_length:
                        record['prompt_preview'] += "..."
                # Remove full prompt/response for non-admin
                record.pop('prompt', None)
                record.pop('response', None)
                record.pop('headers', None)
            
            # Parse headers JSON if it's a string
            if record.get('headers') and isinstance(record['headers'], str):
                try:
                    import json
                    record['headers'] = json.loads(record['headers'])
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            logger.error(f"Failed to decrypt record fields: {e}")
            # Return record as-is if decryption fails
            
        return record
    
    def get_request_by_id(self, request_id: UUID, admin_view: bool = False) -> Optional[Dict]:
        """Get a single request by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                if admin_view:
                    query = """
                        SELECT id, timestamp, src_ip, provider, model, endpoint, method,
                               headers, prompt, response, duration_ms, status_code, risk_score, is_flagged, flag_reason, created_at
                        FROM llm_requests 
                        WHERE id = %s
                    """
                else:
                    query = """
                        SELECT id, timestamp, src_ip, provider, model, endpoint, method,
                               SUBSTRING(prompt FROM 1 FOR %s) as prompt_preview, duration_ms, status_code, risk_score, is_flagged, flag_reason, created_at
                        FROM llm_requests 
                        WHERE id = %s
                    """
                
                params = [settings.prompt_truncate_length, str(request_id)] if not admin_view else [str(request_id)]
                cursor.execute(query, params)
                record = cursor.fetchone()
                
                if record:
                    record_dict = dict(record)
                    return self._decrypt_record(record_dict, admin_view)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get request {request_id}: {e}")
            raise
    
    def get_statistics(self, days: int = 30) -> StatsResponse:
        """Get system statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Date filter
                date_filter = f"timestamp >= NOW() - INTERVAL '{days} days'"
                
                # Basic counts
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN is_flagged THEN 1 END) as flagged_requests,
                        COALESCE(AVG(risk_score), 0) as avg_risk_score
                    FROM llm_requests 
                    WHERE {date_filter}
                """)
                basic_stats = cursor.fetchone()
                
                # Top providers
                cursor.execute(f"""
                    SELECT provider, COUNT(*) as count
                    FROM llm_requests 
                    WHERE {date_filter}
                    GROUP BY provider 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_providers = [dict(row) for row in cursor.fetchall()]
                
                # Top models
                cursor.execute(f"""
                    SELECT model, COUNT(*) as count
                    FROM llm_requests 
                    WHERE {date_filter}
                    GROUP BY model 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_models = [dict(row) for row in cursor.fetchall()]
                
                # Top risk IPs
                cursor.execute(f"""
                    SELECT src_ip, COUNT(*) as request_count, AVG(risk_score) as avg_risk
                    FROM llm_requests 
                    WHERE {date_filter} AND is_flagged = TRUE
                    GROUP BY src_ip 
                    ORDER BY avg_risk DESC, request_count DESC
                    LIMIT 5
                """)
                top_risk_ips = [dict(row) for row in cursor.fetchall()]
                
                # Requests by hour (last 24 hours)
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('hour', timestamp) as hour,
                        COUNT(*) as request_count,
                        COUNT(CASE WHEN is_flagged THEN 1 END) as flagged_count
                    FROM llm_requests 
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    GROUP BY DATE_TRUNC('hour', timestamp)
                    ORDER BY hour DESC
                    LIMIT 24
                """)
                requests_by_hour = [dict(row) for row in cursor.fetchall()]
                
                total_requests = basic_stats['total_requests']
                flagged_requests = basic_stats['flagged_requests']
                flagged_rate = (flagged_requests / total_requests * 100) if total_requests > 0 else 0
                
                return StatsResponse(
                    total_requests=total_requests,
                    flagged_requests=flagged_requests,
                    flagged_rate=round(flagged_rate, 2),
                    top_providers=top_providers,
                    top_models=top_models,
                    top_risk_ips=top_risk_ips,
                    avg_risk_score=round(basic_stats['avg_risk_score'], 2),
                    requests_by_hour=requests_by_hour
                )
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise
    
    def get_detection_rules(self) -> List[DetectionRuleResponse]:
        """Get all detection rules"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                cursor.execute("""
                    SELECT id, name, description, category, rule_type, pattern, severity, 
                           points, priority, stop_on_match, combination_logic, 
                           is_active, created_at, updated_at
                    FROM detection_rules
                    ORDER BY priority DESC, severity DESC, points DESC, name
                """)
                
                records = cursor.fetchall()
                return [DetectionRuleResponse(**dict(record)) for record in records]
                
        except Exception as e:
            logger.error(f"Failed to get detection rules: {e}")
            raise
    
    def get_detection_rules_paginated(self, page=1, page_size=50, search=None, rule_type=None, is_active=None):
        """Get paginated list of detection rules with filters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if search:
                    where_conditions.append("(name ILIKE %s OR description ILIKE %s OR pattern ILIKE %s)")
                    search_param = f"%{search}%"
                    params.extend([search_param, search_param, search_param])
                
                if rule_type:
                    where_conditions.append("rule_type = %s")
                    params.append(rule_type)
                
                if is_active is not None:
                    where_conditions.append("is_active = %s")
                    params.append(is_active)
                
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                else:
                    where_clause = ""
                    params = []
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM detection_rules {where_clause}"
                cursor.execute(count_query, params)
                count_result = cursor.fetchone()
                total_count = count_result['count'] if isinstance(count_result, dict) else count_result[0]
                
                # Get paginated results
                offset = (page - 1) * page_size
                data_query = f"""
                    SELECT id, name, description, category, rule_type, pattern, severity, 
                           points, priority, stop_on_match, combination_logic, 
                           is_active, created_at, updated_at
                    FROM detection_rules
                    {where_clause}
                    ORDER BY priority DESC, severity DESC, points DESC, name
                    LIMIT %s OFFSET %s
                """
                
                cursor.execute(data_query, params + [page_size, offset])
                records = cursor.fetchall()
                rules = [DetectionRuleResponse(**dict(record)) for record in records]
                
                return rules, total_count
                
        except Exception as e:
            logger.error(f"Failed to get paginated detection rules: {str(e)} (Type: {type(e).__name__})")
            logger.error(f"Database error: {repr(e)}")
            raise
    
    def create_detection_rule(self, rule_data: dict) -> DetectionRuleResponse:
        """Create a new detection rule"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                cursor.execute("""
                    INSERT INTO detection_rules (name, description, category, rule_type, pattern, severity, 
                                                points, priority, stop_on_match, combination_logic, is_active)
                    VALUES (%(name)s, %(description)s, %(category)s, %(rule_type)s, %(pattern)s, %(severity)s, 
                           %(points)s, %(priority)s, %(stop_on_match)s, %(combination_logic)s, %(is_active)s)
                    RETURNING id, name, description, category, rule_type, pattern, severity, 
                             points, priority, stop_on_match, combination_logic, is_active, created_at, updated_at
                """, rule_data)
                
                record = cursor.fetchone()
                conn.commit()
                
                return DetectionRuleResponse(**dict(record))
                
        except Exception as e:
            logger.error(f"Failed to create detection rule: {e}")
            raise
    
    def update_detection_rule(self, rule_id: UUID, rule_data: dict) -> Optional[DetectionRuleResponse]:
        """Update a detection rule"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Build update query dynamically
                set_clauses = []
                params = {}
                
                for key, value in rule_data.items():
                    if value is not None:
                        set_clauses.append(f"{key} = %({key})s")
                        params[key] = value
                
                if not set_clauses:
                    return None
                
                params['id'] = str(rule_id)
                
                query = f"""
                    UPDATE detection_rules 
                    SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(id)s
                    RETURNING id, name, description, category, rule_type, pattern, severity, 
                             points, priority, stop_on_match, combination_logic, is_active, created_at, updated_at
                """
                
                cursor.execute(query, params)
                record = cursor.fetchone()
                conn.commit()
                
                return DetectionRuleResponse(**dict(record)) if record else None
                
        except Exception as e:
            logger.error(f"Failed to update detection rule {rule_id}: {e}")
            raise
    
    def delete_detection_rule(self, rule_id: UUID) -> bool:
        """Delete a detection rule"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM detection_rules WHERE id = %s", [str(rule_id)])
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"Failed to delete detection rule {rule_id}: {e}")
            raise
    
    def get_sessions(self, filters, admin_view=False):
        """Get user sessions grouped by IP and time windows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build the session grouping query
                base_query = """
                WITH session_groups AS (
                    SELECT 
                        src_ip,
                        timestamp,
                        LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) as prev_timestamp,
                        CASE 
                            WHEN LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) IS NULL 
                                OR timestamp - LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) > INTERVAL '30 minutes'
                            THEN 1 
                            ELSE 0 
                        END as new_session_flag
                    FROM llm_requests 
                    WHERE 1=1
                ),
                session_starts AS (
                    SELECT 
                        src_ip,
                        timestamp,
                        SUM(new_session_flag) OVER (PARTITION BY src_ip ORDER BY timestamp) as session_num
                    FROM session_groups
                ),
                sessions AS (
                    SELECT 
                        CONCAT(ss.src_ip, '-', ss.session_num) as session_id,
                        ss.src_ip,
                        MIN(r.timestamp) as start_time,
                        GREATEST(
                            MAX(r.timestamp),
                            MIN(r.timestamp) + INTERVAL '10 minutes'
                        ) as end_time,
                        COUNT(*) as request_count,
                        ROUND(AVG(r.risk_score), 2) as avg_risk_score,
                        SUM(CASE WHEN r.is_flagged THEN 1 ELSE 0 END) as flagged_count,
                        STRING_AGG(DISTINCT r.provider, ', ' ORDER BY r.provider) as providers,
                        STRING_AGG(DISTINCT r.model, ', ' ORDER BY r.model) as models,
                        MAX(r.headers->>'User-Agent') as user_agent
                    FROM session_starts ss
                    JOIN llm_requests r ON r.src_ip = ss.src_ip 
                        AND r.timestamp >= ss.timestamp 
                        AND r.timestamp <= ss.timestamp + INTERVAL '1 hour'
                        AND ABS(EXTRACT(EPOCH FROM r.timestamp - ss.timestamp)/60) <= 
                            CASE 
                                WHEN EXTRACT(EPOCH FROM r.timestamp - ss.timestamp)/60 <= 30 THEN 30
                                ELSE 60
                            END
                    GROUP BY ss.src_ip, ss.session_num
                    HAVING MIN(r.timestamp) >= %s AND MIN(r.timestamp) <= %s
                )
                SELECT 
                    session_id,
                    src_ip,
                    start_time,
                    end_time,
                    EXTRACT(EPOCH FROM (end_time - start_time))/60 as duration_minutes,
                    request_count,
                    avg_risk_score,
                    flagged_count,
                    providers,
                    models,
                    user_agent,
                    CASE 
                        WHEN avg_risk_score >= 70 THEN 'critical'
                        WHEN avg_risk_score >= 40 THEN 'high'
                        WHEN avg_risk_score >= 10 THEN 'medium'
                        ELSE 'low'
                    END as risk_level
                FROM sessions
                WHERE 1=1
                """
                
                params = []
                
                # Date range filter
                start_date = filters.start_date or (datetime.utcnow() - timedelta(days=7))
                end_date = filters.end_date or datetime.utcnow()
                params.extend([start_date, end_date])
                
                # Apply filters
                if filters.src_ip:
                    base_query += " AND sessions.src_ip = %s"
                    params.append(filters.src_ip)
                
                if filters.min_risk_score is not None:
                    base_query += " AND avg_risk_score >= %s"
                    params.append(filters.min_risk_score)
                
                if filters.max_risk_score is not None:
                    base_query += " AND avg_risk_score <= %s"
                    params.append(filters.max_risk_score)
                
                if filters.min_duration:
                    base_query += " AND EXTRACT(EPOCH FROM (end_time - start_time))/60 >= %s"
                    params.append(filters.min_duration)
                
                if filters.max_duration:
                    base_query += " AND EXTRACT(EPOCH FROM (end_time - start_time))/60 <= %s"
                    params.append(filters.max_duration)
                
                if filters.min_requests:
                    base_query += " AND request_count >= %s"
                    params.append(filters.min_requests)
                
                if filters.max_requests:
                    base_query += " AND request_count <= %s"
                    params.append(filters.max_requests)
                
                if filters.risk_level:
                    risk_level_map = {
                        'critical': 70,
                        'high': 40,
                        'medium': 10,
                        'low': 1
                    }
                    base_query += " AND avg_risk_score >= %s"
                    params.append(risk_level_map[filters.risk_level])
                
                # Count total records
                count_query = f"SELECT COUNT(*) FROM ({base_query}) as filtered_sessions"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Add ordering and pagination
                base_query += " ORDER BY start_time DESC"
                base_query += " LIMIT %s OFFSET %s"
                params.extend([filters.page_size, (filters.page - 1) * filters.page_size])
                
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    # Detect unusual patterns
                    unusual_patterns = []
                    if row[5] > 100:  # request_count
                        unusual_patterns.append("High activity volume")
                    if row[7] > row[5] * 0.8:  # flagged_count vs request_count
                        unusual_patterns.append("High threat ratio")
                    if ',' in (row[8] or '') and len(row[8].split(',')) > 3:  # multiple providers
                        unusual_patterns.append("Multiple providers")
                    if row[4] > 45:  # duration_minutes
                        unusual_patterns.append("Extended session")
                    
                    session_data = {
                        'id': row[0],
                        'src_ip': row[1],
                        'start_time': row[2],
                        'end_time': row[3],
                        'duration_minutes': int(row[4]),
                        'request_count': row[5],
                        'avg_risk_score': float(row[6]),
                        'flagged_count': row[7],
                        'top_providers': (row[8] or '').split(', ') if row[8] else [],
                        'top_models': (row[9] or '').split(', ') if row[9] else [],
                        'user_agent': row[10],
                        'risk_level': row[11],
                        'unusual_patterns': unusual_patterns,
                        'geographic_info': None  # Will be enhanced later
                    }
                    sessions.append(session_data)
                
                return sessions, total_count
                
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            raise
    
    def get_session_detail(self, session_id, admin_view=False):
        """Get detailed session information including request timeline"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Parse session ID to get src_ip and session number
                parts = session_id.split('-')
                if len(parts) < 2:
                    return None
                
                src_ip = '-'.join(parts[:-1])  # Handle IPs with dashes
                session_num = parts[-1]
                
                # Get session summary
                session_query = """
                WITH session_groups AS (
                    SELECT 
                        src_ip,
                        timestamp,
                        LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) as prev_timestamp,
                        CASE 
                            WHEN LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) IS NULL 
                                OR timestamp - LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) > INTERVAL '30 minutes'
                            THEN 1 
                            ELSE 0 
                        END as new_session_flag
                    FROM llm_requests 
                    WHERE src_ip = %s
                ),
                session_starts AS (
                    SELECT 
                        src_ip,
                        timestamp,
                        SUM(new_session_flag) OVER (PARTITION BY src_ip ORDER BY timestamp) as session_num
                    FROM session_groups
                )
                SELECT 
                    MIN(r.timestamp) as start_time,
                    MAX(r.timestamp) as end_time,
                    COUNT(*) as request_count,
                    ROUND(AVG(r.risk_score), 2) as avg_risk_score,
                    SUM(CASE WHEN r.is_flagged THEN 1 ELSE 0 END) as flagged_count,
                    COALESCE(SUM(r.), 0.0) as total_,
                    STRING_AGG(DISTINCT r.provider, ', ' ORDER BY r.provider) as providers,
                    STRING_AGG(DISTINCT r.model, ', ' ORDER BY r.model) as models,
                    MAX(r.headers->>'User-Agent') as user_agent
                FROM session_starts ss
                JOIN llm_requests r ON r.src_ip = ss.src_ip 
                    AND r.timestamp >= ss.timestamp 
                    AND r.timestamp <= ss.timestamp + INTERVAL '1 hour'
                    AND ABS(EXTRACT(EPOCH FROM r.timestamp - ss.timestamp)/60) <= 
                        CASE 
                            WHEN EXTRACT(EPOCH FROM r.timestamp - ss.timestamp)/60 <= 30 THEN 30
                            ELSE 60
                        END
                WHERE ss.session_num = %s AND r.src_ip = %s
                GROUP BY ss.session_num
                """
                
                cursor.execute(session_query, [src_ip, int(session_num), src_ip])
                session_row = cursor.fetchone()
                
                if not session_row:
                    return None
                
                # Get all requests in this session
                requests_query = """
                WITH session_groups AS (
                    SELECT 
                        src_ip,
                        timestamp,
                        LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) as prev_timestamp,
                        CASE 
                            WHEN LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) IS NULL 
                                OR timestamp - LAG(timestamp) OVER (PARTITION BY src_ip ORDER BY timestamp) > INTERVAL '30 minutes'
                            THEN 1 
                            ELSE 0 
                        END as new_session_flag
                    FROM llm_requests 
                    WHERE src_ip = %s
                ),
                session_starts AS (
                    SELECT 
                        src_ip,
                        timestamp,
                        SUM(new_session_flag) OVER (PARTITION BY src_ip ORDER BY timestamp) as session_num
                    FROM session_groups
                )
                SELECT 
                    r.id,
                    r.timestamp,
                    r.src_ip,
                    r.provider,
                    r.model,
                    r.endpoint,
                    r.method,
                    r.,
                    r.duration_ms,
                    r.status_code,
                    r.risk_score,
                    r.is_flagged,
                    r.flag_reason,
                    r.created_at
                FROM session_starts ss
                JOIN llm_requests r ON r.src_ip = ss.src_ip
                    AND r.timestamp >= ss.timestamp 
                    AND r.timestamp <= ss.timestamp + INTERVAL '1 hour'
                    AND ABS(EXTRACT(EPOCH FROM r.timestamp - ss.timestamp)/60) <= 
                        CASE 
                            WHEN EXTRACT(EPOCH FROM r.timestamp - ss.timestamp)/60 <= 30 THEN 30
                            ELSE 60
                        END
                WHERE ss.session_num = %s AND r.src_ip = %s
                ORDER BY r.timestamp
                """
                
                cursor.execute(requests_query, [src_ip, int(session_num), src_ip])
                request_rows = cursor.fetchall()
                
                # Process requests
                requests = []
                risk_breakdown = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                
                for row in request_rows:
                    # Decrypt sensitive fields if needed
                    prompt_preview = "Preview not available"
                    if admin_view and encryption_service:
                        try:
                            # You'd decrypt actual prompt here
                            prompt_preview = f"Request {row[0]}"[:settings.prompt_truncate_length]
                        except:
                            pass
                    
                    request_data = {
                        'id': row[0],
                        'timestamp': row[1],
                        'src_ip': row[2],
                        'provider': row[3],
                        'model': row[4],
                        'endpoint': row[5],
                        'method': row[6],
                        'prompt_preview': prompt_preview,
                        'duration_ms': row[7],
                        'status_code': row[8],
                        'risk_score': row[9],
                        'is_flagged': row[10],
                        'flag_reason': row[11],
                        'created_at': row[12]
                    }
                    requests.append(request_data)
                    
                    # Update risk breakdown
                    score = row[10]
                    if score >= 70:
                        risk_breakdown['critical'] += 1
                    elif score >= 40:
                        risk_breakdown['high'] += 1
                    elif score >= 10:
                        risk_breakdown['medium'] += 1
                    else:
                        risk_breakdown['low'] += 1
                
                # Build session detail
                duration_minutes = int((session_row[1] - session_row[0]).total_seconds() / 60)
                
                # Detect unusual patterns
                unusual_patterns = []
                if session_row[2] > 100:
                    unusual_patterns.append("High activity volume")
                if session_row[4] > session_row[2] * 0.8:
                    unusual_patterns.append("High threat ratio")
                if ',' in (session_row[7] or '') and len(session_row[7].split(',')) > 3:
                    unusual_patterns.append("Multiple providers")
                if duration_minutes > 45:
                    unusual_patterns.append("Extended session")
                
                session_detail = {
                    'id': session_id,
                    'src_ip': src_ip,
                    'start_time': session_row[0],
                    'end_time': session_row[1],
                    'duration_minutes': duration_minutes,
                    'request_count': session_row[2],
                    'avg_risk_score': float(session_row[3]),
                    'flagged_count': session_row[4],
                    'total_': float(session_row[5]) if session_row[5] else 0.0,
                    'top_providers': (session_row[6] or '').split(', ') if session_row[6] else [],
                    'top_models': (session_row[7] or '').split(', ') if session_row[7] else [],
                    'user_agent': session_row[8],
                    'risk_level': 'critical' if session_row[3] >= 70 else 'high' if session_row[3] >= 40 else 'medium' if session_row[3] >= 10 else 'low',
                    'unusual_patterns': unusual_patterns,
                    'geographic_info': None,
                    'requests': requests,
                    'risk_breakdown': risk_breakdown
                }
                
                return session_detail
                
        except Exception as e:
            logger.error(f"Failed to get session detail {session_id}: {e}")
            raise
    
    def bulk_enable_rules(self, rule_ids):
        """Enable multiple detection rules"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use IN clause instead of ANY for UUID array
                placeholders = ','.join(['%s'] * len(rule_ids))
                query = f"UPDATE detection_rules SET is_active = true, updated_at = %s WHERE id IN ({placeholders})"
                cursor.execute(query, [datetime.utcnow()] + rule_ids)
                updated_count = cursor.rowcount
                conn.commit()
                
                return updated_count
                
        except Exception as e:
            logger.error(f"Failed to bulk enable rules: {e}")
            raise
    
    def bulk_disable_rules(self, rule_ids):
        """Disable multiple detection rules"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use IN clause instead of ANY for UUID array
                placeholders = ','.join(['%s'] * len(rule_ids))
                query = f"UPDATE detection_rules SET is_active = false, updated_at = %s WHERE id IN ({placeholders})"
                cursor.execute(query, [datetime.utcnow()] + rule_ids)
                updated_count = cursor.rowcount
                conn.commit()
                
                return updated_count
                
        except Exception as e:
            logger.error(f"Failed to bulk disable rules: {e}")
            raise
    
    def bulk_delete_rules(self, rule_ids):
        """Delete multiple detection rules"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use IN clause instead of ANY for UUID array
                placeholders = ','.join(['%s'] * len(rule_ids))
                query = f"DELETE FROM detection_rules WHERE id IN ({placeholders})"
                cursor.execute(query, rule_ids)
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to bulk delete rules: {e}")
            raise
    
    def get_alerts(self, filters, admin_view=False):
        """Get alerts with filtering"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                base_query = """
                SELECT id, title, description, severity, alert_type, status, source_type, 
                       NULL as source_id, request_id as related_request_id, metadata, 
                       created_at, updated_at, acknowledged_at, resolved_at, 
                       acknowledged_by, resolved_by
                FROM security_alerts
                WHERE 1=1
                """
                
                params = []
                
                # Apply filters
                if filters.severity:
                    base_query += " AND severity = %s"
                    params.append(filters.severity)
                
                if filters.status:
                    base_query += " AND status = %s"
                    params.append(filters.status)
                
                if filters.alert_type:
                    base_query += " AND alert_type ILIKE %s"
                    params.append(f"%{filters.alert_type}%")
                
                if filters.source_type:
                    base_query += " AND source_type = %s"
                    params.append(filters.source_type)
                
                if filters.start_date:
                    base_query += " AND created_at >= %s"
                    params.append(filters.start_date)
                
                if filters.end_date:
                    base_query += " AND created_at <= %s"
                    params.append(filters.end_date)
                
                if filters.search:
                    base_query += " AND (title ILIKE %s OR description ILIKE %s)"
                    search_term = f"%{filters.search}%"
                    params.extend([search_term, search_term])
                
                # Auto cleanup using configurable retention period
                cursor.execute("""
                    SELECT CASE 
                        WHEN value IS NULL OR value = '' THEN 180
                        ELSE value::INTEGER 
                    END as retention_days
                    FROM system_settings 
                    WHERE key = 'data_retention_days'
                """)
                retention_result = cursor.fetchone()
                retention_days = retention_result[0] if retention_result else 180
                
                cleanup_date = datetime.utcnow() - timedelta(days=retention_days)
                cursor.execute("DELETE FROM security_alerts WHERE created_at < %s", [cleanup_date])
                conn.commit()
                
                # Count total records
                count_query = f"SELECT COUNT(*) FROM ({base_query}) as filtered_alerts"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Add ordering and pagination
                base_query += " ORDER BY created_at DESC"
                base_query += " LIMIT %s OFFSET %s"
                params.extend([filters.page_size, (filters.page - 1) * filters.page_size])
                
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                
                alerts = []
                for row in rows:
                    alert_data = {
                        'id': row[0],
                        'title': row[1],
                        'description': row[2],
                        'severity': row[3],
                        'alert_type': row[4],
                        'status': row[5],
                        'source_type': row[6],
                        'source_id': row[7],
                        'related_request_id': row[8],
                        'metadata': row[9],
                        'created_at': row[10],
                        'updated_at': row[11],
                        'acknowledged_at': row[12],
                        'resolved_at': row[13],
                        'acknowledged_by': row[14],
                        'resolved_by': row[15]
                    }
                    alerts.append(alert_data)
                
                return alerts, total_count
                
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            raise
    
    def create_alert(self, alert_data):
        """Create a new alert"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO alerts (title, description, severity, alert_type, source_type,
                                      source_id, related_request_id, metadata)
                    VALUES (%(title)s, %(description)s, %(severity)s, %(alert_type)s, %(source_type)s,
                           %(source_id)s, %(related_request_id)s, %(metadata)s)
                    RETURNING id, title, description, severity, alert_type, status, source_type,
                             source_id, related_request_id, metadata, created_at, updated_at,
                             acknowledged_at, resolved_at, acknowledged_by, resolved_by
                """, alert_data)
                
                row = cursor.fetchone()
                conn.commit()
                
                return {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'severity': row[3],
                    'alert_type': row[4],
                    'status': row[5],
                    'source_type': row[6],
                    'source_id': row[7],
                    'related_request_id': row[8],
                    'metadata': row[9],
                    'created_at': row[10],
                    'updated_at': row[11],
                    'acknowledged_at': row[12],
                    'resolved_at': row[13],
                    'acknowledged_by': row[14],
                    'resolved_by': row[15]
                }
                
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            raise
    
    def update_alert(self, alert_id, alert_data, user):
        """Update an alert"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update based on status change
                set_clauses = []
                params = {'id': str(alert_id)}
                
                if alert_data.status == 'acknowledged':
                    set_clauses.append("status = 'acknowledged'")
                    set_clauses.append("acknowledged_at = NOW()")
                    set_clauses.append("acknowledged_by = %(user)s")
                    params['user'] = user
                elif alert_data.status == 'resolved':
                    set_clauses.append("status = 'resolved'")
                    set_clauses.append("resolved_at = NOW()")
                    set_clauses.append("resolved_by = %(user)s")
                    params['user'] = user
                    # If not already acknowledged, set that too
                    set_clauses.append("acknowledged_at = COALESCE(acknowledged_at, NOW())")
                    set_clauses.append("acknowledged_by = COALESCE(acknowledged_by, %(user)s)")
                
                if not set_clauses:
                    return None
                
                query = f"""
                    UPDATE alerts 
                    SET {', '.join(set_clauses)}
                    WHERE id = %(id)s
                    RETURNING id, title, description, severity, alert_type, status, source_type,
                             source_id, related_request_id, metadata, created_at, updated_at,
                             acknowledged_at, resolved_at, acknowledged_by, resolved_by
                """
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                conn.commit()
                
                if not row:
                    return None
                
                return {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'severity': row[3],
                    'alert_type': row[4],
                    'status': row[5],
                    'source_type': row[6],
                    'source_id': row[7],
                    'related_request_id': row[8],
                    'metadata': row[9],
                    'created_at': row[10],
                    'updated_at': row[11],
                    'acknowledged_at': row[12],
                    'resolved_at': row[13],
                    'acknowledged_by': row[14],
                    'resolved_by': row[15]
                }
                
        except Exception as e:
            logger.error(f"Failed to update alert {alert_id}: {e}")
            raise
    
    def bulk_alert_operation(self, alert_ids, operation, user):
        """Perform bulk operations on alerts"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert to strings for PostgreSQL array
                alert_ids_str = [str(alert_id) for alert_id in alert_ids]
                
                if operation == 'acknowledge':
                    cursor.execute("""
                        UPDATE alerts 
                        SET status = 'acknowledged', acknowledged_at = NOW(), acknowledged_by = %s, updated_at = NOW()
                        WHERE id::text = ANY(%s) AND status = 'new'
                    """, [user, alert_ids_str])
                elif operation == 'resolve':
                    cursor.execute("""
                        UPDATE alerts 
                        SET status = 'resolved', resolved_at = NOW(), resolved_by = %s, updated_at = NOW(),
                            acknowledged_at = COALESCE(acknowledged_at, NOW()),
                            acknowledged_by = COALESCE(acknowledged_by, %s)
                        WHERE id::text = ANY(%s) AND status != 'resolved'
                    """, [user, user, alert_ids_str])
                elif operation == 'archive':
                    cursor.execute("DELETE FROM alerts WHERE id::text = ANY(%s)", [alert_ids_str])
                
                updated_count = cursor.rowcount
                conn.commit()
                
                return updated_count
                
        except Exception as e:
            logger.error(f"Failed to perform bulk alert operation: {e}")
            raise
    
    def get_alert_stats(self):
        """Get alert statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_alerts,
                        COUNT(*) FILTER (WHERE status = 'new') as new_alerts,
                        COUNT(*) FILTER (WHERE status = 'acknowledged') as acknowledged_alerts,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved_alerts,
                        COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
                        COUNT(*) FILTER (WHERE severity = 'high') as high_alerts
                    FROM security_alerts
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                row = cursor.fetchone()
                
                return {
                    'total_alerts': row[0],
                    'new_alerts': row[1],
                    'acknowledged_alerts': row[2],
                    'resolved_alerts': row[3],
                    'critical_alerts': row[4],
                    'high_alerts': row[5]
                }
                
        except Exception as e:
            logger.error(f"Failed to get alert stats: {e}")
            raise
    
    def get_system_settings(self, category=None):
        """Get system settings, optionally filtered by category"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute("""
                        SELECT id, key, value, description, category, created_at, updated_at
                        FROM system_settings WHERE category = %s
                        ORDER BY key
                    """, [category])
                else:
                    cursor.execute("""
                        SELECT id, key, value, description, category, created_at, updated_at
                        FROM system_settings
                        ORDER BY category, key
                    """)
                
                rows = cursor.fetchall()
                settings = []
                for row in rows:
                    settings.append({
                        'id': row[0],
                        'key': row[1],
                        'value': row[2],
                        'description': row[3],
                        'category': row[4],
                        'created_at': row[5],
                        'updated_at': row[6]
                    })
                
                return settings
                
        except Exception as e:
            logger.error(f"Failed to get system settings: {e}")
            raise
    
    def update_system_setting(self, key, value):
        """Update a system setting value"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE system_settings 
                    SET value = %s, updated_at = NOW()
                    WHERE key = %s
                    RETURNING id, key, value, description, category, created_at, updated_at
                """, [value, key])
                
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Setting with key '{key}' not found")
                
                conn.commit()
                
                return {
                    'id': result[0],
                    'key': result[1],
                    'value': result[2],
                    'description': result[3],
                    'category': result[4],
                    'created_at': result[5],
                    'updated_at': result[6]
                }
                
        except Exception as e:
            logger.error(f"Failed to update system setting {key}: {e}")
            raise
    
    def get_database_stats(self):
        """Get comprehensive database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total counts
                cursor.execute("SELECT COUNT(*) FROM llm_requests")
                total_requests = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM alerts")
                total_alerts = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM user_sessions")
                total_sessions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM detection_rules")
                total_detection_rules = cursor.fetchone()[0]
                
                # Get database size
                cursor.execute("""
                    SELECT pg_database_size(current_database()) / 1024.0 / 1024.0 as db_size_mb
                """)
                database_size_mb = cursor.fetchone()[0]
                
                # Get table sizes
                cursor.execute("""
                    SELECT 
                        pt.schemaname,
                        pt.tablename,
                        pg_size_pretty(pg_total_relation_size(pt.schemaname||'.'||pt.tablename)) as size,
                        pg_total_relation_size(pt.schemaname||'.'||pt.tablename) / 1024.0 / 1024.0 as size_mb,
                        COALESCE(psut.n_tup_ins, 0) as inserts,
                        COALESCE(psut.n_tup_upd, 0) as updates,
                        COALESCE(psut.n_tup_del, 0) as deletes,
                        COALESCE(psut.n_live_tup, 0) as live_rows,
                        COALESCE(psut.n_dead_tup, 0) as dead_rows
                    FROM pg_tables pt
                    LEFT JOIN pg_stat_user_tables psut ON pt.tablename = psut.relname
                    WHERE pt.schemaname = 'public'
                    ORDER BY pg_total_relation_size(pt.schemaname||'.'||pt.tablename) DESC
                """)
                
                table_stats = {}
                for row in cursor.fetchall():
                    table_name = row[1]
                    table_stats[table_name] = {
                        'size_pretty': row[2],
                        'size_mb': float(row[3]) if row[3] else 0.0,
                        'inserts': row[4] or 0,
                        'updates': row[5] or 0,
                        'deletes': row[6] or 0,
                        'live_rows': row[7] or 0,
                        'dead_rows': row[8] or 0
                    }
                
                return {
                    'total_requests': total_requests,
                    'total_alerts': total_alerts,
                    'total_sessions': total_sessions,
                    'total_detection_rules': total_detection_rules,
                    'database_size_mb': float(database_size_mb),
                    'table_sizes': table_stats
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise
    
    def export_data(self, data_type, start_date=None, end_date=None, limit=100000):
        """Export data based on type and date range"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Base queries for different data types
                if data_type == 'requests':
                    base_query = """
                        SELECT id, timestamp, src_ip, provider, model, endpoint, method,
                               SUBSTRING(prompt, 1, 200) as prompt_preview,
                               , duration_ms, status_code, risk_score, is_flagged,
                               flag_reason, created_at
                        FROM llm_requests
                    """
                    date_column = 'timestamp'
                elif data_type == 'alerts':
                    base_query = """
                        SELECT id, title, description, severity, alert_type, status,
                               source_type, source_id, related_request_id, metadata,
                               created_at, updated_at, acknowledged_at, resolved_at,
                               acknowledged_by, resolved_by
                        FROM alerts
                    """
                    date_column = 'created_at'
                elif data_type == 'sessions':
                    base_query = """
                        SELECT id, src_ip, start_time, end_time, duration_minutes,
                               request_count, avg_risk_score, flagged_count,
                               geographic_info, user_agent, top_providers, top_models,
                               total_, risk_level, unusual_patterns,
                               created_at
                        FROM user_sessions
                    """
                    date_column = 'created_at'
                else:
                    raise ValueError(f"Invalid data type: {data_type}")
                
                # Add date filters
                conditions = []
                params = []
                
                if start_date:
                    conditions.append(f"{date_column} >= %s")
                    params.append(start_date)
                
                if end_date:
                    conditions.append(f"{date_column} <= %s")
                    params.append(end_date)
                
                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)
                
                base_query += f" ORDER BY {date_column} DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(base_query, params)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch all results
                rows = cursor.fetchall()
                
                return {
                    'columns': columns,
                    'data': rows,
                    'total_exported': len(rows)
                }
                
        except Exception as e:
            logger.error(f"Failed to export {data_type} data: {e}")
            raise
    
    def execute_query(self, query, params=None):
        """Execute a raw SQL query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or [])
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise
    
    def get_users(self):
        """Get all users from the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, username, first_name, last_name, role, is_active, last_login, created_at, updated_at
                    FROM users
                    ORDER BY created_at DESC
                """)
                
                rows = cursor.fetchall()
                users = []
                for row in rows:
                    users.append({
                        'id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'role': row[4],
                        'is_active': row[5],
                        'last_login': row[6],
                        'created_at': row[7],
                        'updated_at': row[8]
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise
    
    def get_users_paginated(self, page=1, page_size=50, search=None, role=None, is_active=None):
        """Get paginated list of users with filters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if search:
                    where_conditions.append("(username ILIKE %s OR first_name ILIKE %s OR last_name ILIKE %s)")
                    search_param = f"%{search}%"
                    params.extend([search_param, search_param, search_param])
                
                if role:
                    where_conditions.append("role = %s")
                    params.append(role)
                
                if is_active is not None:
                    where_conditions.append("is_active = %s")
                    params.append(is_active)
                
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                else:
                    where_clause = ""
                    params = []
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM users {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Get paginated results
                offset = (page - 1) * page_size
                data_query = f"""
                    SELECT id, username, first_name, last_name, role, is_active, last_login, created_at, updated_at
                    FROM users
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                cursor.execute(data_query, params + [page_size, offset])
                rows = cursor.fetchall()
                
                users = []
                for row in rows:
                    users.append({
                        'id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'role': row[4],
                        'is_active': row[5],
                        'last_login': row[6],
                        'created_at': row[7],
                        'updated_at': row[8]
                    })
                
                return users, total_count
                
        except Exception as e:
            logger.error(f"Failed to get paginated users: {e}")
            raise
    
    def create_user(self, user_data):
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Hash the password
                import bcrypt
                password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, first_name, last_name)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, username, first_name, last_name, role, is_active, last_login, created_at, updated_at
                """, [
                    user_data['username'], 
                    password_hash, 
                    user_data['role'],
                    user_data.get('first_name', ''),
                    user_data.get('last_name', '')
                ])
                
                result = cursor.fetchone()
                conn.commit()
                
                return {
                    'id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'role': result[4],
                    'is_active': result[5],
                    'last_login': result[6],
                    'created_at': result[7],
                    'updated_at': result[8]
                }
                
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    def update_user(self, user_id, update_data):
        """Update a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                update_fields = []
                params = []
                
                if 'username' in update_data:
                    update_fields.append("username = %s")
                    params.append(update_data['username'])
                
                if 'first_name' in update_data:
                    update_fields.append("first_name = %s")
                    params.append(update_data['first_name'])
                
                if 'last_name' in update_data:
                    update_fields.append("last_name = %s")
                    params.append(update_data['last_name'])
                
                if 'role' in update_data:
                    update_fields.append("role = %s")
                    params.append(update_data['role'])
                
                if 'is_active' in update_data:
                    update_fields.append("is_active = %s")
                    params.append(update_data['is_active'])
                
                if 'password' in update_data:
                    import bcrypt
                    password_hash = bcrypt.hashpw(update_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    update_fields.append("password_hash = %s")
                    params.append(password_hash)
                
                if not update_fields:
                    raise ValueError("No fields to update")
                
                update_fields.append("updated_at = NOW()")
                params.append(str(user_id))
                
                cursor.execute(f"""
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING id, username, first_name, last_name, role, is_active, last_login, created_at, updated_at
                """, params)
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                conn.commit()
                
                return {
                    'id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'role': result[4],
                    'is_active': result[5],
                    'last_login': result[6],
                    'created_at': result[7],
                    'updated_at': result[8]
                }
                
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    def delete_user(self, user_id):
        """Delete a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM users WHERE id = %s", [str(user_id)])
                deleted = cursor.rowcount > 0
                conn.commit()
                
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    def get_user_by_username(self, username):
        """Get a user by username"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, username, password_hash, first_name, last_name, role, is_active, last_login, created_at, updated_at
                    FROM users WHERE username = %s
                """, [username])
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return {
                    'id': result[0],
                    'username': result[1],
                    'password_hash': result[2],
                    'first_name': result[3],
                    'last_name': result[4],
                    'role': result[5],
                    'is_active': result[6],
                    'last_login': result[7],
                    'created_at': result[8],
                    'updated_at': result[9]
                }
                
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            raise
    
    def get_user_by_id(self, user_id):
        """Get a user by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, username, password_hash, first_name, last_name, role, is_active, last_login, created_at, updated_at
                    FROM users WHERE id = %s
                """, [str(user_id)])
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return {
                    'id': result[0],
                    'username': result[1],
                    'password_hash': result[2],
                    'first_name': result[3],
                    'last_name': result[4],
                    'role': result[5],
                    'is_active': result[6],
                    'last_login': result[7],
                    'created_at': result[8],
                    'updated_at': result[9]
                }
                
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            raise
    
    def update_user_login(self, username):
        """Update user's last login timestamp"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET last_login = NOW() 
                    WHERE username = %s
                """, [username])
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update login for user {username}: {e}")
            # Don't raise here as it's not critical

    # Analytics methods
    def refresh_analytics_aggregates(self):
        """Refresh analytics aggregation tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT refresh_analytics_aggregates()")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to refresh analytics aggregates: {e}")
            raise


    def get_volume_trends(self, time_range: str, date_range: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Get request volume trends"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Determine the table and time column based on time_range
                table_map = {
                    'hourly': ('analytics_hourly', 'time_bucket'),
                    'daily': ('analytics_daily', 'date_bucket'),
                    'weekly': ('analytics_weekly', 'week_bucket'),
                    'monthly': ('analytics_monthly', 'month_bucket')
                }
                
                if time_range not in table_map:
                    raise ValueError(f"Invalid time_range: {time_range}")
                
                table, time_col = table_map[time_range]
                
                # Build the date filter
                date_filter = self._get_date_filter(date_range, time_col)
                
                # Build provider/model filters
                filters = []
                params = []
                if provider:
                    filters.append("provider = %s")
                    params.append(provider)
                if model:
                    filters.append("model = %s")
                    params.append(model)
                
                filter_clause = " AND ".join(filters)
                if filter_clause:
                    filter_clause = f"AND {filter_clause}"
                
                query = f"""
                    SELECT 
                        {time_col} as time,
                        SUM(request_count) as requests
                    FROM {table}
                    WHERE {date_filter} {filter_clause}
                    GROUP BY {time_col}
                    ORDER BY {time_col}
                """
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get volume trends: {e}")
            raise

    def get_threat_trends(self, time_range: str, date_range: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Get threat detection rate trends"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                table_map = {
                    'hourly': ('analytics_hourly', 'time_bucket'),
                    'daily': ('analytics_daily', 'date_bucket'),
                    'weekly': ('analytics_weekly', 'week_bucket'),
                    'monthly': ('analytics_monthly', 'month_bucket')
                }
                
                if time_range not in table_map:
                    raise ValueError(f"Invalid time_range: {time_range}")
                
                table, time_col = table_map[time_range]
                date_filter = self._get_date_filter(date_range, time_col)
                
                filters = []
                params = []
                if provider:
                    filters.append("provider = %s")
                    params.append(provider)
                if model:
                    filters.append("model = %s")
                    params.append(model)
                
                filter_clause = " AND ".join(filters)
                if filter_clause:
                    filter_clause = f"AND {filter_clause}"
                
                query = f"""
                    SELECT 
                        {time_col} as time,
                        AVG(threat_detection_rate) as threatRate,
                        SUM(flagged_count) as flaggedCount
                    FROM {table}
                    WHERE {date_filter} {filter_clause}
                    GROUP BY {time_col}
                    ORDER BY {time_col}
                """
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get threat trends: {e}")
            raise

    def get_model_usage(self, time_range: str, date_range: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Get model usage patterns"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                table_map = {
                    'hourly': ('analytics_hourly', 'time_bucket'),
                    'daily': ('analytics_daily', 'date_bucket'),
                    'weekly': ('analytics_weekly', 'week_bucket'),
                    'monthly': ('analytics_monthly', 'month_bucket')
                }
                
                if time_range not in table_map:
                    raise ValueError(f"Invalid time_range: {time_range}")
                
                table, time_col = table_map[time_range]
                date_filter = self._get_date_filter(date_range, time_col)
                
                filters = []
                params = []
                if provider:
                    filters.append("provider = %s")
                    params.append(provider)
                if model:
                    filters.append("model = %s")
                    params.append(model)
                
                filter_clause = " AND ".join(filters)
                if filter_clause:
                    filter_clause = f"AND {filter_clause}"
                
                query = f"""
                    SELECT 
                        model,
                        SUM(request_count) as requests
                    FROM {table}
                    WHERE {date_filter} {filter_clause}
                    GROUP BY model
                    ORDER BY SUM(request_count) DESC
                    LIMIT 20
                """
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get model usage: {e}")
            raise

    def get_provider_breakdown(self, time_range: str, date_range: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Get provider distribution"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                table_map = {
                    'hourly': ('analytics_hourly', 'time_bucket'),
                    'daily': ('analytics_daily', 'date_bucket'),
                    'weekly': ('analytics_weekly', 'week_bucket'),
                    'monthly': ('analytics_monthly', 'month_bucket')
                }
                
                if time_range not in table_map:
                    raise ValueError(f"Invalid time_range: {time_range}")
                
                table, time_col = table_map[time_range]
                date_filter = self._get_date_filter(date_range, time_col)
                
                filters = []
                params = []
                if provider:
                    filters.append("provider = %s")
                    params.append(provider)
                if model:
                    filters.append("model = %s")
                    params.append(model)
                
                filter_clause = " AND ".join(filters)
                if filter_clause:
                    filter_clause = f"AND {filter_clause}"
                
                query = f"""
                    SELECT 
                        provider as name,
                        SUM(request_count) as requests
                    FROM {table}
                    WHERE {date_filter} {filter_clause}
                    GROUP BY provider
                    ORDER BY SUM(request_count) DESC
                """
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get provider breakdown: {e}")
            raise

    def get_key_metrics(self, time_range: str, date_range: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Get key analytics metrics - real-time calculation from llm_requests"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Calculate date range filter
                date_filter = self._get_date_filter_for_requests(date_range)
                
                filters = [date_filter]
                params = []
                
                if provider:
                    filters.append("provider = %s")
                    params.append(provider)
                if model:
                    filters.append("model = %s")
                    params.append(model)
                
                where_clause = " AND ".join(filters)
                
                # Real-time query directly from llm_requests table
                query = f"""
                    SELECT 
                        COUNT(*) as "totalRequests",
                        SUM(CASE WHEN is_flagged THEN 1 ELSE 0 END) as "flaggedRequests",
                        CASE 
                            WHEN COUNT(*) > 0 THEN ROUND(100.0 * SUM(CASE WHEN is_flagged THEN 1 ELSE 0 END) / COUNT(*), 2)
                            ELSE 0 
                        END as "threatRate",
                        COALESCE(AVG(duration_ms), 0) as "avgDuration",
                        COUNT(DISTINCT src_ip) as "uniqueIPs",
                        AVG(risk_score) as "avgRiskScore"
                    FROM llm_requests
                    WHERE {where_clause}
                """
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                if result:
                    metrics = dict(result)
                    # Add growth calculation (simplified)
                    metrics['requestsGrowth'] = 1.2  # placeholder
                    return metrics
                else:
                    return {
                        'totalRequests': 0,
                        'flaggedRequests': 0,
                        'threatRate': 0,
                        'avgDuration': 0.0,
                        'uniqueIPs': 0,
                        'requestsGrowth': 0
                    }
                
        except Exception as e:
            logger.error(f"Failed to get key metrics: {e}")
            raise

    def _get_date_filter_for_requests(self, date_range: str):
        """Get date filter clause for llm_requests table"""
        range_map = {
            '24h': 'timestamp >= NOW() - INTERVAL \'24 hours\'',
            '7d': 'timestamp >= NOW() - INTERVAL \'7 days\'',
            '30d': 'timestamp >= NOW() - INTERVAL \'30 days\'',
            '90d': 'timestamp >= NOW() - INTERVAL \'90 days\''
        }
        return range_map.get(date_range, 'timestamp >= NOW() - INTERVAL \'7 days\'')

    def get_anomalies(self, time_range: str, date_range: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Get detected anomalies (simplified implementation)"""
        try:
            # For now, return basic anomaly detection based on threat rate spikes
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                table_map = {
                    'hourly': ('analytics_hourly', 'time_bucket'),
                    'daily': ('analytics_daily', 'date_bucket'),
                    'weekly': ('analytics_weekly', 'week_bucket'),
                    'monthly': ('analytics_monthly', 'month_bucket')
                }
                
                if time_range not in table_map:
                    raise ValueError(f"Invalid time_range: {time_range}")
                
                table, time_col = table_map[time_range]
                date_filter = self._get_date_filter(date_range, time_col)
                
                filters = []
                params = []
                if provider:
                    filters.append("provider = %s")
                    params.append(provider)
                if model:
                    filters.append("model = %s")
                    params.append(model)
                
                filter_clause = " AND ".join(filters)
                if filter_clause:
                    filter_clause = f"AND {filter_clause}"
                
                # Find high threat detection rates (above 10%)
                query = f"""
                    SELECT 
                        {time_col} as timestamp,
                        provider,
                        model,
                        threat_detection_rate,
                        request_count
                    FROM {table}
                    WHERE {date_filter} 
                        AND threat_detection_rate > 10.0
                        AND request_count > 5
                        {filter_clause}
                    ORDER BY {time_col} DESC
                    LIMIT 10
                """
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                anomalies = []
                for row in results:
                    anomalies.append({
                        'type': 'High Threat Detection Rate',
                        'description': f'Threat detection rate of {row["threat_detection_rate"]:.1f}% for {row["provider"]}/{row["model"]}',
                        'severity': 'high' if row["threat_detection_rate"] > 20 else 'medium',
                        'timestamp': row['timestamp'],
                        'provider': row['provider'],
                        'model': row['model']
                    })
                
                return anomalies
                
        except Exception as e:
            logger.error(f"Failed to get anomalies: {e}")
            raise

    def get_analytics_filter_options(self):
        """Get available filter options (providers, models)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get unique providers
                cursor.execute("SELECT DISTINCT provider FROM llm_requests ORDER BY provider")
                providers = [row[0] for row in cursor.fetchall()]
                
                # Get unique models
                cursor.execute("SELECT DISTINCT model FROM llm_requests ORDER BY model")
                models = [row[0] for row in cursor.fetchall()]
                
                return {
                    'providers': providers,
                    'models': models
                }
                
        except Exception as e:
            logger.error(f"Failed to get filter options: {e}")
            raise

    def export_analytics(self, format: str, time_range: str, date_range: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Export analytics data"""
        try:
            # For CSV export, get volume trends data
            if format == 'csv':
                data = self.get_volume_trends(time_range, date_range, provider, model)
                
                import io
                import csv
                
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                
                return output.getvalue()
            
            elif format == 'png':
                # Generate PNG chart using matplotlib
                import matplotlib
                matplotlib.use('Agg')  # Use non-interactive backend
                import matplotlib.pyplot as plt
                import pandas as pd
                import io
                
                # Get volume trends data
                data = self.get_volume_trends(time_range, date_range, provider, model)
                
                if not data:
                    # Create empty chart if no data
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                           transform=ax.transAxes, fontsize=16, color='gray')
                    ax.set_title('Analytics Dashboard - Volume Trends')
                else:
                    # Create DataFrame from data
                    df = pd.DataFrame(data)
                    
                    # Create the chart
                    fig, ax = plt.subplots(figsize=(12, 6))
                    
                    if 'time' in df.columns and 'requests' in df.columns:
                        # Convert time to datetime if it's a string
                        if df['time'].dtype == 'object':
                            df['time'] = pd.to_datetime(df['time'])
                        
                        # Plot line chart
                        ax.plot(df['time'], df['requests'], marker='o', linewidth=2, markersize=4)
                        ax.set_xlabel('Time')
                        ax.set_ylabel('Number of Requests')
                        ax.set_title('Analytics Dashboard - Request Volume Trends')
                        ax.grid(True, alpha=0.3)
                        
                        # Format x-axis
                        plt.xticks(rotation=45)
                    else:
                        # Fallback: create a simple bar chart with available data
                        if len(df.columns) >= 2:
                            ax.bar(range(len(df)), df.iloc[:, 1])
                            ax.set_xlabel('Data Points')
                            ax.set_ylabel('Values')
                            ax.set_title('Analytics Dashboard - Data Export')
                
                plt.tight_layout()
                
                # Save to bytes
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='PNG', dpi=300, bbox_inches='tight')
                img_buffer.seek(0)
                
                plt.close(fig)  # Clean up
                
                return img_buffer.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            raise

    def _get_date_filter(self, date_range: str, time_col: str):
        """Get SQL date filter clause"""
        if date_range == '24h':
            return f"{time_col} >= NOW() - INTERVAL '1 day'"
        elif date_range == '7d':
            return f"{time_col} >= NOW() - INTERVAL '7 days'"
        elif date_range == '30d':
            return f"{time_col} >= NOW() - INTERVAL '30 days'"
        elif date_range == '90d':
            return f"{time_col} >= NOW() - INTERVAL '90 days'"
        else:
            return f"{time_col} >= NOW() - INTERVAL '7 days'"  # default