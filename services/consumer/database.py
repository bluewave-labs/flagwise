import psycopg2
import psycopg2.extras
from psycopg2 import sql
import json
import logging
from typing import Optional
from contextlib import contextmanager

from config import settings
from models import DatabaseRecord
from encryption_service import encryption_service

logger = logging.getLogger(__name__)

class DatabaseManager:
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
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def insert_llm_request(self, record: DatabaseRecord) -> bool:
        """Insert a single LLM request record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert headers to JSON string and encrypt sensitive fields
                headers_json = json.dumps(record.headers) if record.headers else None
                encrypted_headers = encryption_service.encrypt_headers(headers_json)
                encrypted_prompt = encryption_service.encrypt_prompt(record.prompt)
                encrypted_response = encryption_service.encrypt_response(record.response)
                
                insert_query = sql.SQL("""
                    INSERT INTO llm_requests (
                        id, timestamp, src_ip, provider, model, endpoint, method,
                        headers, prompt, response, duration_ms, status_code,
                        risk_score, is_flagged, flag_reason
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """)
                
                cursor.execute(insert_query, (
                    str(record.id),
                    record.timestamp,
                    record.src_ip,
                    record.provider,
                    record.model,
                    record.endpoint,
                    record.method,
                    encrypted_headers,
                    encrypted_prompt,
                    encrypted_response,
                    record.duration_ms,
                    record.status_code,
                    record.risk_score,
                    record.is_flagged,
                    record.flag_reason
                ))
                
                conn.commit()
                logger.debug(f"Inserted record {record.id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to insert record {record.id}: {e}")
            return False
    
    def bulk_insert_llm_requests(self, records: list[DatabaseRecord]) -> int:
        """Bulk insert multiple LLM request records"""
        if not records:
            return 0
            
        successful_inserts = 0
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare bulk insert data with encryption
                insert_data = []
                for record in records:
                    headers_json = json.dumps(record.headers) if record.headers else None
                    encrypted_headers = encryption_service.encrypt_headers(headers_json)
                    encrypted_prompt = encryption_service.encrypt_prompt(record.prompt)
                    encrypted_response = encryption_service.encrypt_response(record.response)
                    
                    insert_data.append((
                        str(record.id),
                        record.timestamp,
                        record.src_ip,
                        record.provider,
                        record.model,
                        record.endpoint,
                        record.method,
                        encrypted_headers,
                        encrypted_prompt,
                        encrypted_response,
                            record.duration_ms,
                        record.status_code,
                        record.risk_score,
                        record.is_flagged,
                        record.flag_reason
                    ))
                
                # Use execute_batch for better performance
                insert_query = """
                    INSERT INTO llm_requests (
                        id, timestamp, src_ip, provider, model, endpoint, method,
                        headers, prompt, response, duration_ms, status_code,
                        risk_score, is_flagged, flag_reason
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                psycopg2.extras.execute_batch(cursor, insert_query, insert_data)
                successful_inserts = len(insert_data)
                conn.commit()
                
                logger.info(f"Bulk inserted {successful_inserts} records")
                
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            
        return successful_inserts
    
    def get_record_count(self) -> int:
        """Get total number of records in llm_requests table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM llm_requests")
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            logger.error(f"Failed to get record count: {e}")
            return 0