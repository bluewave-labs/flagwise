import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from collections import deque
import requests

from config import settings
from models import DatabaseRecord
from database import DatabaseManager

logger = logging.getLogger(__name__)

class RateLimiter:
    """Thread-safe rate limiter for alerts"""
    
    def __init__(self, max_alerts: int = 5, time_window_minutes: int = 1):
        self.max_alerts = max_alerts
        self.time_window = timedelta(minutes=time_window_minutes)
        self.alert_times = deque()
        self.lock = threading.Lock()
    
    def can_send_alert(self) -> bool:
        """Check if we can send an alert within rate limits"""
        with self.lock:
            now = datetime.now()
            
            # Remove old alerts outside the time window
            while self.alert_times and now - self.alert_times[0] > self.time_window:
                self.alert_times.popleft()
            
            # Check if we're under the limit
            if len(self.alert_times) < self.max_alerts:
                self.alert_times.append(now)
                return True
            
            return False
    
    def get_next_available_time(self) -> Optional[datetime]:
        """Get the next time when an alert can be sent"""
        with self.lock:
            if not self.alert_times:
                return datetime.now()
            
            # Next available time is when the oldest alert expires
            oldest_alert = self.alert_times[0]
            return oldest_alert + self.time_window

class SlackAlertService:
    """Service for sending Slack alerts about flagged requests"""
    
    def __init__(self):
        self.webhook_url = None
        self.rate_limiter = RateLimiter(max_alerts=5, time_window_minutes=1)
        self.db_manager = DatabaseManager()
        self.prompt_preview_length = 150
        self.dashboard_base_url = "http://localhost:3000"
        
        # Initialize webhook URL from settings
        self._load_webhook_config()
    
    def _load_webhook_config(self):
        """Load Slack webhook configuration"""
        webhook_url = getattr(settings, 'slack_webhook_url', None)
        if webhook_url and webhook_url != 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK':
            self.webhook_url = webhook_url
            logger.info("Slack webhook configured")
        else:
            logger.warning("Slack webhook URL not configured - alerts disabled")
    
    def should_send_alert(self, record: DatabaseRecord) -> bool:
        """Determine if a record should trigger an alert"""
        if not self.webhook_url:
            return False
        
        if not record.is_flagged:
            return False
        
        # Only alert on high-risk requests (configurable threshold)
        min_risk_threshold = getattr(settings, 'alert_min_risk_score', 50)
        if record.risk_score < min_risk_threshold:
            return False
        
        return True
    
    def send_alert(self, record: DatabaseRecord) -> bool:
        """Send a Slack alert for a flagged request"""
        if not self.should_send_alert(record):
            return False
        
        if not self.rate_limiter.can_send_alert():
            logger.warning("Alert rate limit exceeded - skipping alert")
            self._log_alert_to_database(record, "rate_limited")
            return False
        
        try:
            payload = self._build_slack_payload(record)
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent for request {record.id}")
                self._log_alert_to_database(record, "sent")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code} - {response.text}")
                self._log_alert_to_database(record, "failed", response.text)
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            self._log_alert_to_database(record, "failed", str(e))
            return False
    
    def _build_slack_payload(self, record: DatabaseRecord) -> Dict[str, Any]:
        """Build rich Slack message payload using blocks"""
        # Truncate prompt for preview
        prompt_preview = (record.prompt or "")[:self.prompt_preview_length]
        if len(record.prompt or "") > self.prompt_preview_length:
            prompt_preview += "..."
        
        # Risk level emoji and color
        risk_emoji, color = self._get_risk_display(record.risk_score)
        
        # Dashboard link
        dashboard_link = f"{self.dashboard_base_url}/requests/{record.id}" if record.id else self.dashboard_base_url
        
        # Build the payload
        payload = {
            "text": f"🚨 Shadow AI Alert: High-risk LLM request detected (Risk Score: {record.risk_score})",
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{risk_emoji} Shadow AI Security Alert",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Risk Score:* {record.risk_score}/100"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Source IP:* {record.src_ip}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Provider:* {record.provider}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Model:* {record.model}"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Triggered Rules:* {record.flag_reason or 'Unknown'}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Prompt Preview:*\n```{prompt_preview}```"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Timestamp:* {record.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View Details",
                                        "emoji": True
                                    },
                                    "url": dashboard_link,
                                    "style": "primary"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        return payload
    
    def _get_risk_display(self, risk_score: int) -> tuple[str, str]:
        """Get emoji and color for risk level"""
        if risk_score >= 80:
            return "🔴", "danger"
        elif risk_score >= 60:
            return "🟠", "warning"
        elif risk_score >= 40:
            return "🟡", "#ffcc00"
        else:
            return "🟢", "good"
    
    def _log_alert_to_database(self, record: DatabaseRecord, status: str, error_message: str = None):
        """Log alert attempt to database"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO alerts (request_id, alert_type, recipient, status, sent_at, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    str(record.id),
                    'slack',
                    'slack_webhook',
                    status,
                    datetime.now() if status == 'sent' else None,
                    error_message
                ))
                
                conn.commit()
                logger.debug(f"Alert logged to database: {record.id} - {status}")
                
        except Exception as e:
            logger.error(f"Failed to log alert to database: {e}")
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alerting statistics"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get alert counts by status for last 24 hours
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM alerts 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    AND alert_type = 'slack'
                    GROUP BY status
                """)
                
                status_counts = {}
                for row in cursor.fetchall():
                    status_counts[row[0]] = row[1]
                
                # Get rate limit info
                next_available = self.rate_limiter.get_next_available_time()
                can_send = self.rate_limiter.can_send_alert()
                
                return {
                    'webhook_configured': bool(self.webhook_url),
                    'alerts_last_24h': status_counts,
                    'rate_limit_available': can_send,
                    'next_alert_available': next_available.isoformat() if next_available else None,
                    'current_window_count': len(self.rate_limiter.alert_times)
                }
                
        except Exception as e:
            logger.error(f"Failed to get alert stats: {e}")
            return {
                'webhook_configured': bool(self.webhook_url),
                'error': str(e)
            }

# Global instance for use in consumer
slack_alert_service = SlackAlertService()