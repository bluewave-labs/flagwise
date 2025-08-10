import logging
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Types of security events to monitor"""
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DDOS_DETECTED = "ddos_detected"
    IP_BLOCKED = "ip_blocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    AUTHENTICATION_FAILURE = "auth_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    INJECTION_ATTEMPT = "injection_attempt"
    MALICIOUS_PAYLOAD = "malicious_payload"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: SecurityEventType
    timestamp: datetime
    source_ip: str
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    user_agent: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    severity: str = "medium"  # low, medium, high, critical
    details: Optional[str] = None
    session_id: Optional[str] = None
    geographic_location: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

class SecurityMonitor:
    """Real-time security monitoring and alerting system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.alert_thresholds = {
            SecurityEventType.RATE_LIMIT_EXCEEDED: {"count": 10, "window": 300},  # 10 in 5 min
            SecurityEventType.DDOS_DETECTED: {"count": 1, "window": 60},         # 1 in 1 min
            SecurityEventType.AUTHENTICATION_FAILURE: {"count": 5, "window": 300}, # 5 in 5 min
            SecurityEventType.INJECTION_ATTEMPT: {"count": 3, "window": 300},    # 3 in 5 min
        }
        
        # High-risk IP patterns and behaviors
        self.risk_indicators = {
            "multiple_user_agents": {"threshold": 5, "risk_score": 3},
            "rapid_endpoint_scanning": {"threshold": 20, "risk_score": 4},
            "geo_location_changes": {"threshold": 3, "risk_score": 2},
            "failed_auth_attempts": {"threshold": 10, "risk_score": 5},
            "suspicious_payloads": {"threshold": 1, "risk_score": 5}
        }
    
    async def log_security_event(self, event: SecurityEvent) -> bool:
        """Log a security event and trigger monitoring"""
        try:
            # Store event in Redis with expiration
            event_key = f"security:event:{int(time.time())}"
            event_data = event.to_dict()
            
            pipe = self.redis_client.pipeline()
            
            # Store the event
            pipe.setex(event_key, 86400, json.dumps(event_data))  # 24 hour retention
            
            # Add to time-series for monitoring
            series_key = f"security:series:{event.event_type.value}"
            pipe.zadd(series_key, {event_key: time.time()})
            pipe.expire(series_key, 86400)
            
            # Add to IP-specific tracking
            if event.source_ip:
                ip_key = f"security:ip:{event.source_ip}"
                pipe.zadd(ip_key, {event_key: time.time()})
                pipe.expire(ip_key, 86400)
            
            # Add to user-specific tracking if user is identified
            if event.user_id:
                user_key = f"security:user:{event.user_id}"
                pipe.zadd(user_key, {event_key: time.time()})
                pipe.expire(user_key, 86400)
            
            pipe.execute()
            
            # Check if this event triggers an alert
            await self._check_alert_thresholds(event)
            
            # Update risk scoring
            if event.source_ip:
                await self._update_ip_risk_score(event.source_ip, event)
            
            logger.info(f"Security event logged: {event.event_type.value} from {event.source_ip}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return False
    
    async def _check_alert_thresholds(self, event: SecurityEvent):
        """Check if event triggers security alerts"""
        try:
            if event.event_type not in self.alert_thresholds:
                return
            
            threshold_config = self.alert_thresholds[event.event_type]
            window_seconds = threshold_config["window"]
            count_threshold = threshold_config["count"]
            
            # Count recent events of this type
            series_key = f"security:series:{event.event_type.value}"
            cutoff_time = time.time() - window_seconds
            
            # Remove old events
            self.redis_client.zremrangebyscore(series_key, 0, cutoff_time)
            
            # Count recent events
            recent_count = self.redis_client.zcard(series_key)
            
            if recent_count >= count_threshold:
                await self._trigger_security_alert(event.event_type, recent_count, window_seconds)
                
        except Exception as e:
            logger.error(f"Error checking alert thresholds: {e}")
    
    async def _trigger_security_alert(self, event_type: SecurityEventType, count: int, window: int):
        """Trigger a security alert"""
        try:
            alert_data = {
                "alert_type": "security_threshold_exceeded",
                "event_type": event_type.value,
                "count": count,
                "window_seconds": window,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "high"
            }
            
            # Store alert
            alert_key = f"security:alert:{int(time.time())}"
            self.redis_client.setex(alert_key, 3600, json.dumps(alert_data))
            
            # Add to alerts series
            alerts_key = "security:alerts:active"
            self.redis_client.zadd(alerts_key, {alert_key: time.time()})
            self.redis_client.expire(alerts_key, 3600)
            
            # Log critical alert
            logger.critical(f"SECURITY ALERT: {event_type.value} threshold exceeded - {count} events in {window}s")
            
            # In production, send to SIEM, Slack, PagerDuty, etc.
            await self._send_alert_notification(alert_data)
            
        except Exception as e:
            logger.error(f"Failed to trigger security alert: {e}")
    
    async def _send_alert_notification(self, alert_data: Dict[str, Any]):
        """Send alert notification to external systems"""
        # This should be implemented based on your alerting infrastructure
        # Examples: Slack webhook, PagerDuty, email, SIEM integration
        
        logger.warning(f"ALERT NOTIFICATION: {json.dumps(alert_data, indent=2)}")
        
        # Example: Send to Slack (implement with actual webhook)
        # await self._send_slack_alert(alert_data)
        
        # Example: Send to SIEM (implement with actual SIEM API)
        # await self._send_siem_alert(alert_data)
    
    async def _update_ip_risk_score(self, ip: str, event: SecurityEvent):
        """Update risk score for an IP based on behavior patterns"""
        try:
            risk_key = f"security:risk:{ip}"
            
            # Get current risk data
            risk_data = self.redis_client.get(risk_key)
            if risk_data:
                risk_info = json.loads(risk_data)
            else:
                risk_info = {
                    "ip": ip,
                    "risk_score": 0,
                    "first_seen": datetime.utcnow().isoformat(),
                    "indicators": {},
                    "events_count": 0
                }
            
            # Update based on event type
            base_risk_increase = {
                SecurityEventType.DDOS_DETECTED: 10,
                SecurityEventType.INJECTION_ATTEMPT: 8,
                SecurityEventType.MALICIOUS_PAYLOAD: 7,
                SecurityEventType.AUTHENTICATION_FAILURE: 3,
                SecurityEventType.RATE_LIMIT_EXCEEDED: 2,
                SecurityEventType.SUSPICIOUS_ACTIVITY: 4
            }.get(event.event_type, 1)
            
            risk_info["risk_score"] += base_risk_increase
            risk_info["events_count"] += 1
            risk_info["last_seen"] = datetime.utcnow().isoformat()
            
            # Check for behavioral indicators
            await self._analyze_behavioral_indicators(ip, risk_info, event)
            
            # Cap risk score at 100
            risk_info["risk_score"] = min(100, risk_info["risk_score"])
            
            # Store updated risk info
            self.redis_client.setex(risk_key, 86400, json.dumps(risk_info))
            
            # If risk score is high, consider automated blocking
            if risk_info["risk_score"] > 80:
                await self._consider_automatic_blocking(ip, risk_info)
                
        except Exception as e:
            logger.error(f"Error updating IP risk score: {e}")
    
    async def _analyze_behavioral_indicators(self, ip: str, risk_info: Dict, event: SecurityEvent):
        """Analyze behavioral patterns for additional risk scoring"""
        try:
            # Check for multiple user agents from same IP
            if event.user_agent:
                user_agents_key = f"behavior:ua:{ip}"
                self.redis_client.sadd(user_agents_key, event.user_agent)
                self.redis_client.expire(user_agents_key, 3600)
                ua_count = self.redis_client.scard(user_agents_key)
                
                if ua_count >= self.risk_indicators["multiple_user_agents"]["threshold"]:
                    risk_info["indicators"]["multiple_user_agents"] = ua_count
                    risk_info["risk_score"] += self.risk_indicators["multiple_user_agents"]["risk_score"]
            
            # Check for rapid endpoint scanning
            if event.endpoint:
                endpoints_key = f"behavior:endpoints:{ip}"
                self.redis_client.sadd(endpoints_key, event.endpoint)
                self.redis_client.expire(endpoints_key, 300)  # 5 minute window
                endpoint_count = self.redis_client.scard(endpoints_key)
                
                if endpoint_count >= self.risk_indicators["rapid_endpoint_scanning"]["threshold"]:
                    risk_info["indicators"]["rapid_endpoint_scanning"] = endpoint_count
                    risk_info["risk_score"] += self.risk_indicators["rapid_endpoint_scanning"]["risk_score"]
            
        except Exception as e:
            logger.error(f"Error analyzing behavioral indicators: {e}")
    
    async def _consider_automatic_blocking(self, ip: str, risk_info: Dict):
        """Consider automatically blocking high-risk IPs"""
        try:
            # Only auto-block if risk score is very high and multiple indicators
            if (risk_info["risk_score"] > 90 and 
                len(risk_info.get("indicators", {})) >= 2):
                
                # Auto-block for 1 hour
                block_key = f"blocked:{ip}"
                block_data = {
                    "reason": "automatic_high_risk",
                    "risk_score": risk_info["risk_score"],
                    "indicators": risk_info["indicators"],
                    "blocked_at": datetime.utcnow().isoformat()
                }
                
                self.redis_client.setex(block_key, 3600, json.dumps(block_data))
                
                # Log the automatic blocking
                logger.critical(f"AUTOMATIC BLOCK: IP {ip} blocked due to high risk score ({risk_info['risk_score']})")
                
                # Create security event for the blocking
                block_event = SecurityEvent(
                    event_type=SecurityEventType.IP_BLOCKED,
                    timestamp=datetime.utcnow(),
                    source_ip=ip,
                    severity="critical",
                    details=f"Automatic block due to risk score {risk_info['risk_score']}",
                    payload={"risk_info": risk_info}
                )
                await self.log_security_event(block_event)
                
        except Exception as e:
            logger.error(f"Error considering automatic blocking: {e}")
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security monitoring dashboard data"""
        try:
            now = time.time()
            last_hour = now - 3600
            last_24h = now - 86400
            
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "events_last_hour": {},
                "events_last_24h": {},
                "active_alerts": 0,
                "blocked_ips": 0,
                "high_risk_ips": [],
                "top_event_types": {}
            }
            
            # Count events by type for different time windows
            for event_type in SecurityEventType:
                series_key = f"security:series:{event_type.value}"
                
                # Clean old data
                self.redis_client.zremrangebyscore(series_key, 0, last_24h)
                
                # Count for different windows
                hour_count = self.redis_client.zcount(series_key, last_hour, now)
                day_count = self.redis_client.zcount(series_key, last_24h, now)
                
                dashboard_data["events_last_hour"][event_type.value] = hour_count
                dashboard_data["events_last_24h"][event_type.value] = day_count
            
            # Count active alerts
            alerts_key = "security:alerts:active"
            self.redis_client.zremrangebyscore(alerts_key, 0, now - 3600)  # Clean old alerts
            dashboard_data["active_alerts"] = self.redis_client.zcard(alerts_key)
            
            # Count blocked IPs
            blocked_keys = self.redis_client.keys("blocked:*")
            dashboard_data["blocked_ips"] = len(blocked_keys)
            
            # Get high-risk IPs
            risk_keys = self.redis_client.keys("security:risk:*")
            high_risk_ips = []
            
            for risk_key in risk_keys[:50]:  # Limit to top 50
                risk_data = self.redis_client.get(risk_key)
                if risk_data:
                    risk_info = json.loads(risk_data)
                    if risk_info["risk_score"] > 50:  # High risk threshold
                        high_risk_ips.append({
                            "ip": risk_info["ip"],
                            "risk_score": risk_info["risk_score"],
                            "events_count": risk_info["events_count"],
                            "last_seen": risk_info["last_seen"]
                        })
            
            # Sort by risk score
            high_risk_ips.sort(key=lambda x: x["risk_score"], reverse=True)
            dashboard_data["high_risk_ips"] = high_risk_ips[:20]  # Top 20
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating security dashboard: {e}")
            return {"error": str(e)}
    
    async def get_ip_security_profile(self, ip: str) -> Dict[str, Any]:
        """Get detailed security profile for an IP"""
        try:
            # Get risk data
            risk_key = f"security:risk:{ip}"
            risk_data = self.redis_client.get(risk_key)
            
            if not risk_data:
                return {"ip": ip, "risk_score": 0, "events": [], "blocked": False}
            
            risk_info = json.loads(risk_data)
            
            # Get recent events
            ip_events_key = f"security:ip:{ip}"
            recent_events = []
            
            event_keys = self.redis_client.zrevrange(ip_events_key, 0, 50, withscores=True)
            for event_key, timestamp in event_keys:
                event_data = self.redis_client.get(event_key)
                if event_data:
                    event = json.loads(event_data)
                    recent_events.append(event)
            
            # Check if IP is currently blocked
            block_key = f"blocked:{ip}"
            block_info = self.redis_client.get(block_key)
            is_blocked = bool(block_info)
            
            return {
                "ip": ip,
                "risk_info": risk_info,
                "recent_events": recent_events,
                "blocked": is_blocked,
                "block_info": json.loads(block_info) if block_info else None
            }
            
        except Exception as e:
            logger.error(f"Error getting IP security profile: {e}")
            return {"error": str(e)}

# Global security monitor instance
security_monitor = SecurityMonitor()