from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pydantic import BaseModel

from middleware.rate_limiter import SecurityRateLimiter
from security.monitoring import security_monitor, SecurityEvent, SecurityEventType
from config.security_config import get_security_config
from auth import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/security", tags=["security"])

# Pydantic models for request/response
class BlockIPRequest(BaseModel):
    ip: str
    reason: str = "manual_block"
    duration: int = 3600  # seconds

class UnblockIPRequest(BaseModel):
    ip: str

class SecurityDashboardResponse(BaseModel):
    timestamp: str
    events_last_hour: Dict[str, int]
    events_last_24h: Dict[str, int]
    active_alerts: int
    blocked_ips: int
    high_risk_ips: List[Dict[str, Any]]

class BlockedIPResponse(BaseModel):
    ip: str
    reason: str
    blocked_at: str
    expires_at: str
    events_count: int

class RateLimitStatusResponse(BaseModel):
    endpoint: str
    current_requests: int
    limit: int
    window: str
    status: str

# Initialize rate limiter (in production, use dependency injection)
rate_limiter = SecurityRateLimiter()
security_config = get_security_config()

@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    current_user = Depends(require_admin)
):
    """Get comprehensive security dashboard data"""
    try:
        dashboard_data = await security_monitor.get_security_dashboard()
        return SecurityDashboardResponse(**dashboard_data)
        
    except Exception as e:
        logger.error(f"Error fetching security dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch security dashboard")

@router.get("/blocked-ips", response_model=List[BlockedIPResponse])
async def get_blocked_ips(
    current_user = Depends(require_admin)
):
    """Get list of currently blocked IP addresses"""
    try:
        # Get blocked IPs from Redis
        blocked_ips = []
        blocked_keys = rate_limiter.redis_client.keys("blocked:*")
        
        for key in blocked_keys:
            ip = key.replace("blocked:", "")
            block_data = rate_limiter.redis_client.get(key)
            ttl = rate_limiter.redis_client.ttl(key)
            
            if block_data and ttl > 0:
                import json
                try:
                    block_info = json.loads(block_data)
                    blocked_ips.append(BlockedIPResponse(
                        ip=ip,
                        reason=block_info.get("reason", "unknown"),
                        blocked_at=block_info.get("blocked_at", datetime.utcnow().isoformat()),
                        expires_at=datetime.fromtimestamp(datetime.utcnow().timestamp() + ttl).isoformat(),
                        events_count=block_info.get("events_count", 0)
                    ))
                except json.JSONDecodeError:
                    # Handle legacy block format
                    blocked_ips.append(BlockedIPResponse(
                        ip=ip,
                        reason=block_data,
                        blocked_at=datetime.utcnow().isoformat(),
                        expires_at=datetime.fromtimestamp(datetime.utcnow().timestamp() + ttl).isoformat(),
                        events_count=0
                    ))
        
        return blocked_ips
        
    except Exception as e:
        logger.error(f"Error fetching blocked IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch blocked IPs")

@router.get("/rate-limits", response_model=List[RateLimitStatusResponse])
async def get_rate_limit_status(
    current_user = Depends(require_admin)
):
    """Get current rate limit status for all endpoints"""
    try:
        rate_limit_data = []
        
        # Get rate limits from configuration
        endpoint_limits = security_config.rate_limits.endpoint_limits
        
        for endpoint, limit in endpoint_limits.items():
            if endpoint == "default":
                continue
                
            try:
                # Count current requests for this endpoint
                # This is a simplified version - in production, you'd aggregate across all IPs
                rate_key_pattern = f"rate:*:{endpoint}"
                current_count = 0
                
                # Get sample of rate keys to estimate current usage
                sample_keys = rate_limiter.redis_client.keys(rate_key_pattern)[:10]
                for key in sample_keys:
                    current_count += rate_limiter.redis_client.zcard(key)
                
                # Determine status
                percentage = (current_count / limit) * 100 if limit > 0 else 0
                if percentage > 80:
                    status = "critical"
                elif percentage > 60:
                    status = "warning"
                else:
                    status = "normal"
                
                rate_limit_data.append(RateLimitStatusResponse(
                    endpoint=endpoint,
                    current_requests=current_count,
                    limit=limit,
                    window="per minute",
                    status=status
                ))
                
            except Exception as endpoint_error:
                logger.warning(f"Error getting rate limit for {endpoint}: {endpoint_error}")
                continue
        
        return rate_limit_data
        
    except Exception as e:
        logger.error(f"Error fetching rate limit status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch rate limit status")

@router.post("/block-ip")
async def block_ip(
    request: BlockIPRequest,
    current_user = Depends(require_admin)
):
    """Manually block an IP address"""
    try:
        success = rate_limiter.manual_block_ip(
            ip=request.ip,
            duration=request.duration,
            reason=request.reason
        )
        
        if success:
            # Log the blocking event
            security_event = SecurityEvent(
                event_type=SecurityEventType.IP_BLOCKED,
                timestamp=datetime.utcnow(),
                source_ip=request.ip,
                user_id=current_user.get('user_id'),
                severity="high",
                details=f"Manually blocked by admin: {request.reason}",
                payload={"duration": request.duration, "admin_user": current_user.get('username')}
            )
            await security_monitor.log_security_event(security_event)
            
            return {"success": True, "message": f"IP {request.ip} blocked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to block IP")
            
    except Exception as e:
        logger.error(f"Error blocking IP {request.ip}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to block IP: {str(e)}")

@router.post("/unblock-ip")
async def unblock_ip(
    request: UnblockIPRequest,
    current_user = Depends(require_admin)
):
    """Remove IP from blocklist"""
    try:
        success = rate_limiter.unblock_ip(request.ip)
        
        if success:
            # Log the unblocking event
            security_event = SecurityEvent(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,  # Using generic type for unblock
                timestamp=datetime.utcnow(),
                source_ip=request.ip,
                user_id=current_user.get('user_id'),
                severity="medium",
                details=f"Manually unblocked by admin",
                payload={"admin_user": current_user.get('username')}
            )
            await security_monitor.log_security_event(security_event)
            
            return {"success": True, "message": f"IP {request.ip} unblocked successfully"}
        else:
            return {"success": False, "message": f"IP {request.ip} was not blocked"}
            
    except Exception as e:
        logger.error(f"Error unblocking IP {request.ip}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unblock IP: {str(e)}")

@router.get("/ip-profile/{ip}")
async def get_ip_security_profile(
    ip: str,
    current_user = Depends(require_admin)
):
    """Get detailed security profile for a specific IP"""
    try:
        profile = await security_monitor.get_ip_security_profile(ip)
        return profile
        
    except Exception as e:
        logger.error(f"Error fetching IP profile for {ip}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch IP security profile")

@router.get("/alerts")
async def get_active_security_alerts(
    current_user = Depends(require_admin)
):
    """Get currently active security alerts"""
    try:
        # Get active alerts from Redis
        alerts_key = "security:alerts:active"
        alert_keys = rate_limiter.redis_client.zrevrange(alerts_key, 0, 50)  # Last 50 alerts
        
        alerts = []
        for alert_key in alert_keys:
            alert_data = rate_limiter.redis_client.get(alert_key)
            if alert_data:
                import json
                try:
                    alert = json.loads(alert_data)
                    alerts.append(alert)
                except json.JSONDecodeError:
                    continue
        
        return {"alerts": alerts, "count": len(alerts)}
        
    except Exception as e:
        logger.error(f"Error fetching security alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch security alerts")

@router.get("/config")
async def get_security_configuration(
    current_user = Depends(require_admin)
):
    """Get current security configuration (for debugging/monitoring)"""
    try:
        config_info = {
            "security_level": security_config.security_level.value,
            "rate_limits": {
                "endpoint_limits": security_config.rate_limits.endpoint_limits,
                "burst_limits": security_config.rate_limits.burst_limits,
                "ddos_threshold": security_config.rate_limits.ddos_threshold,
                "ddos_block_duration": security_config.rate_limits.ddos_block_duration,
                "whitelist_count": len(security_config.rate_limits.whitelist_ips)
            },
            "monitoring": security_config.monitoring_config,
            "features": {
                "real_time_alerts": security_config.monitoring_config.get("enable_real_time_alerts", False),
                "geographic_tracking": security_config.monitoring_config.get("enable_geographic_tracking", False),
                "behavioral_analysis": security_config.monitoring_config.get("enable_behavioral_analysis", False),
                "auto_block": security_config.monitoring_config.get("auto_block_high_risk", False)
            }
        }
        
        return config_info
        
    except Exception as e:
        logger.error(f"Error fetching security configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch security configuration")

@router.post("/test-alert")
async def test_security_alert(
    current_user = Depends(require_admin)
):
    """Test security alert system (admin only)"""
    try:
        # Create a test security event
        test_event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            timestamp=datetime.utcnow(),
            source_ip="127.0.0.1",
            user_id=current_user.get('user_id'),
            severity="medium",
            details="Test alert triggered by administrator",
            payload={"test": True, "admin_user": current_user.get('username')}
        )
        
        success = await security_monitor.log_security_event(test_event)
        
        if success:
            return {"success": True, "message": "Test alert sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test alert")
            
    except Exception as e:
        logger.error(f"Error sending test alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test alert: {str(e)}")

# Health check endpoint for security services
@router.get("/health")
async def security_health_check():
    """Health check for security services"""
    try:
        # Test Redis connection
        redis_status = "healthy"
        try:
            rate_limiter.redis_client.ping()
        except:
            redis_status = "unhealthy"
        
        # Test security monitor
        monitor_status = "healthy"
        try:
            await security_monitor.get_security_dashboard()
        except:
            monitor_status = "unhealthy"
        
        overall_status = "healthy" if redis_status == "healthy" and monitor_status == "healthy" else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "rate_limiter": redis_status,
                "security_monitor": monitor_status
            },
            "security_level": security_config.security_level.value
        }
        
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }