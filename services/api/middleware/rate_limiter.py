import time
import redis
import json
import logging
from typing import Dict, Tuple, Optional, List
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import ipaddress
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class RateLimitConfig:
    """Configuration for rate limiting rules"""
    
    def __init__(self):
        # Rate limits per endpoint (requests per minute)
        self.endpoint_limits = {
            "/api/v1/chat/completions": 60,  # AI requests
            "/api/v1/requests": 120,         # Data retrieval
            "/api/v1/rules": 30,             # Rule management
            "/api/v1/alerts": 60,            # Alert queries
            "/api/v1/auth/login": 5,         # Auth attempts
            "/api/v1/auth/register": 3,      # Registration
            "default": 100                   # Default limit
        }
        
        # Burst limits (requests per 10 seconds)
        self.burst_limits = {
            "/api/v1/chat/completions": 10,
            "/api/v1/auth/login": 3,
            "/api/v1/auth/register": 2,
            "default": 20
        }
        
        # IP-based limits (requests per hour)
        self.ip_hourly_limits = {
            "default": 1000,
            "authenticated": 5000,
            "admin": 10000
        }
        
        # User role-based limits
        self.user_limits = {
            "guest": 50,        # requests per minute
            "user": 200,
            "premium": 500,
            "admin": 2000
        }
        
        # Whitelist of IPs exempt from rate limiting - expanded for development
        self.whitelist_ips = set([
            "127.0.0.1",
            "::1",
            "localhost",
            "0.0.0.0",
            "192.168.0.0/16",  # Private network range
            "10.0.0.0/8",      # Private network range
            "172.16.0.0/12"    # Private network range
        ])
        
        # DDoS detection thresholds
        self.ddos_detection = {
            "requests_per_second": 50,    # Trigger DDoS detection
            "unique_ips_threshold": 100,  # Minimum IPs for DDoS
            "block_duration": 3600,       # 1 hour block
            "monitoring_window": 300      # 5 minute window
        }

class SecurityRateLimiter:
    """Advanced rate limiter with DDoS protection and security features"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.blocked_ips = set()
        self.ddos_detection_active = False
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("Rate limiter connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP with proxy support"""
        # Check for real IP from reverse proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    def _is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        if ip in self.config.whitelist_ips:
            return True
        
        # Check network ranges and private IPs
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Check against network ranges in whitelist
            for whitelist_entry in self.config.whitelist_ips:
                try:
                    if '/' in whitelist_entry:  # Network range
                        network = ipaddress.ip_network(whitelist_entry, strict=False)
                        if ip_obj in network:
                            return True
                except ValueError:
                    continue
            
            # Always whitelist private IPs for development
            if ip_obj.is_private or ip_obj.is_loopback:
                return True
        except ValueError:
            pass
        
        return False
    
    def _get_user_role(self, request: Request) -> str:
        """Extract user role from request (implement based on your auth system)"""
        # This should be implemented based on your authentication system
        # For now, return default role
        user = getattr(request.state, 'user', None)
        if user:
            return getattr(user, 'role', 'user')
        return 'guest'
    
    async def _check_endpoint_limit(self, key: str, limit: int, window: int = 60) -> Tuple[bool, int, int]:
        """Check rate limit for specific endpoint"""
        try:
            pipe = self.redis_client.pipeline()
            
            # Sliding window rate limiting using Redis
            now = time.time()
            window_start = now - window
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_requests = results[1]
            
            remaining = max(0, limit - current_requests - 1)  # -1 for current request
            reset_time = int(now + window)
            
            return current_requests < limit, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow request if Redis is down
            return True, limit, int(time.time() + window)
    
    async def _detect_ddos(self, ip: str) -> bool:
        """Detect potential DDoS attacks"""
        try:
            now = time.time()
            window = self.config.ddos_detection["monitoring_window"]
            threshold = self.config.ddos_detection["requests_per_second"]
            
            # Track requests per IP for DDoS detection
            ddos_key = f"ddos:detection:{int(now // window)}"
            
            # Count requests from this IP in current window
            ip_requests_key = f"ddos:ip:{ip}:{int(now // window)}"
            current_requests = self.redis_client.incr(ip_requests_key)
            self.redis_client.expire(ip_requests_key, window)
            
            # If single IP exceeds threshold
            if current_requests > threshold * window:
                logger.warning(f"DDoS detected from IP {ip}: {current_requests} requests in {window}s")
                
                # Add to DDoS tracking
                self.redis_client.sadd(ddos_key, ip)
                self.redis_client.expire(ddos_key, window)
                
                # Block IP temporarily
                block_duration = self.config.ddos_detection["block_duration"]
                self.redis_client.setex(f"blocked:{ip}", block_duration, "ddos_detected")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"DDoS detection error: {e}")
            return False
    
    async def _is_blocked(self, ip: str) -> Tuple[bool, str]:
        """Check if IP is currently blocked"""
        try:
            block_reason = self.redis_client.get(f"blocked:{ip}")
            return bool(block_reason), block_reason or ""
        except Exception as e:
            logger.error(f"Error checking blocked IP: {e}")
            return False, ""
    
    async def check_rate_limit(self, request: Request) -> Dict:
        """Main rate limiting check"""
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        user_role = self._get_user_role(request)
        
        # Skip rate limiting for whitelisted IPs
        if self._is_whitelisted(client_ip):
            return {
                "allowed": True,
                "reason": "whitelisted",
                "remaining": 999999,
                "reset_time": int(time.time() + 3600)
            }
        
        # Check if IP is blocked
        is_blocked, block_reason = await self._is_blocked(client_ip)
        if is_blocked:
            logger.warning(f"Blocked IP {client_ip} attempted access: {block_reason}")
            return {
                "allowed": False,
                "reason": f"ip_blocked:{block_reason}",
                "remaining": 0,
                "reset_time": 0
            }
        
        # DDoS detection
        if await self._detect_ddos(client_ip):
            return {
                "allowed": False,
                "reason": "ddos_detected",
                "remaining": 0,
                "reset_time": int(time.time() + self.config.ddos_detection["block_duration"])
            }
        
        # Get appropriate limits
        endpoint_limit = self.config.endpoint_limits.get(endpoint, self.config.endpoint_limits["default"])
        burst_limit = self.config.burst_limits.get(endpoint, self.config.burst_limits["default"])
        user_limit = self.config.user_limits.get(user_role, self.config.user_limits["guest"])
        
        # Use the most restrictive limit
        effective_limit = min(endpoint_limit, user_limit)
        
        # Check burst limit (10-second window)
        burst_key = f"burst:{client_ip}:{endpoint}"
        burst_allowed, burst_remaining, burst_reset = await self._check_endpoint_limit(
            burst_key, burst_limit, 10
        )
        
        if not burst_allowed:
            logger.warning(f"Burst limit exceeded for {client_ip} on {endpoint}")
            return {
                "allowed": False,
                "reason": "burst_limit_exceeded",
                "remaining": burst_remaining,
                "reset_time": burst_reset
            }
        
        # Check main rate limit (60-second window)
        rate_key = f"rate:{client_ip}:{endpoint}"
        rate_allowed, rate_remaining, rate_reset = await self._check_endpoint_limit(
            rate_key, effective_limit, 60
        )
        
        if not rate_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "remaining": rate_remaining,
                "reset_time": rate_reset
            }
        
        # Check hourly IP limit
        hourly_key = f"hourly:{client_ip}"
        hourly_limit = self.config.ip_hourly_limits.get(user_role, self.config.ip_hourly_limits["default"])
        hourly_allowed, hourly_remaining, hourly_reset = await self._check_endpoint_limit(
            hourly_key, hourly_limit, 3600
        )
        
        if not hourly_allowed:
            logger.warning(f"Hourly limit exceeded for {client_ip}")
            return {
                "allowed": False,
                "reason": "hourly_limit_exceeded",
                "remaining": hourly_remaining,
                "reset_time": hourly_reset
            }
        
        # All checks passed
        return {
            "allowed": True,
            "reason": "within_limits",
            "remaining": min(rate_remaining, burst_remaining, hourly_remaining),
            "reset_time": max(rate_reset, burst_reset, hourly_reset)
        }
    
    async def get_rate_limit_status(self, ip: str, endpoint: str) -> Dict:
        """Get current rate limit status for monitoring"""
        try:
            now = time.time()
            
            # Get current counts
            rate_key = f"rate:{ip}:{endpoint}"
            burst_key = f"burst:{ip}:{endpoint}"
            hourly_key = f"hourly:{ip}"
            
            rate_count = self.redis_client.zcard(rate_key)
            burst_count = self.redis_client.zcard(burst_key)
            hourly_count = self.redis_client.zcard(hourly_key)
            
            # Check if blocked
            is_blocked, block_reason = await self._is_blocked(ip)
            
            return {
                "ip": ip,
                "endpoint": endpoint,
                "rate_limit_count": rate_count,
                "burst_limit_count": burst_count,
                "hourly_count": hourly_count,
                "is_blocked": is_blocked,
                "block_reason": block_reason,
                "timestamp": now
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {"error": str(e)}
    
    def manual_block_ip(self, ip: str, duration: int, reason: str) -> bool:
        """Manually block an IP address"""
        try:
            self.redis_client.setex(f"blocked:{ip}", duration, f"manual:{reason}")
            logger.info(f"Manually blocked IP {ip} for {duration}s: {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to manually block IP {ip}: {e}")
            return False
    
    def unblock_ip(self, ip: str) -> bool:
        """Remove IP from blocklist"""
        try:
            result = self.redis_client.delete(f"blocked:{ip}")
            if result:
                logger.info(f"Unblocked IP {ip}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip}: {e}")
            return False


# Middleware function for FastAPI
async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    
    # Initialize rate limiter (in production, use dependency injection)
    rate_limiter = SecurityRateLimiter()
    
    try:
        # Check rate limit
        limit_result = await rate_limiter.check_rate_limit(request)
        
        if not limit_result["allowed"]:
            # Rate limit exceeded
            headers = {
                "X-RateLimit-Remaining": str(limit_result["remaining"]),
                "X-RateLimit-Reset": str(limit_result["reset_time"]),
                "Retry-After": str(max(60, limit_result["reset_time"] - int(time.time())))
            }
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {limit_result['reason']}",
                    "retry_after": headers["Retry-After"]
                },
                headers=headers
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(limit_result["reset_time"])
        
        return response
        
    except Exception as e:
        logger.error(f"Rate limiting middleware error: {e}")
        # Fail open - allow request if rate limiter fails
        return await call_next(request)


# Example usage in FastAPI app
"""
from fastapi import FastAPI
from middleware.rate_limiter import rate_limit_middleware

app = FastAPI()
app.middleware("http")(rate_limit_middleware)
"""