import os
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class SecurityLevel(Enum):
    """Security enforcement levels"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_SECURITY = "high_security"

@dataclass
class RateLimitRules:
    """Rate limiting configuration"""
    # Per-endpoint limits (requests per minute)
    endpoint_limits: Dict[str, int]
    
    # Burst protection (requests per 10 seconds)
    burst_limits: Dict[str, int]
    
    # IP-based hourly limits
    ip_hourly_limits: Dict[str, int]
    
    # User role-based limits
    user_role_limits: Dict[str, int]
    
    # DDoS detection thresholds
    ddos_threshold: int = 50  # requests per second
    ddos_block_duration: int = 3600  # 1 hour
    
    # Whitelist of exempt IPs
    whitelist_ips: Set[str] = None
    
    def __post_init__(self):
        if self.whitelist_ips is None:
            self.whitelist_ips = {"127.0.0.1", "::1"}

class SecurityConfiguration:
    """Centralized security configuration management"""
    
    def __init__(self, security_level: SecurityLevel = None):
        self.security_level = security_level or self._detect_security_level()
        self.rate_limits = self._get_rate_limit_config()
        self.monitoring_config = self._get_monitoring_config()
        self.encryption_config = self._get_encryption_config()
        self.authentication_config = self._get_auth_config()
        
    def _detect_security_level(self) -> SecurityLevel:
        """Auto-detect security level based on environment"""
        env = os.getenv('ENVIRONMENT', 'development').lower()
        
        if env in ['prod', 'production']:
            return SecurityLevel.PRODUCTION
        elif env in ['staging', 'stage']:
            return SecurityLevel.STAGING
        elif env == 'high_security':
            return SecurityLevel.HIGH_SECURITY
        else:
            return SecurityLevel.DEVELOPMENT
    
    def _get_rate_limit_config(self) -> RateLimitRules:
        """Get rate limiting configuration based on security level"""
        
        if self.security_level == SecurityLevel.DEVELOPMENT:
            return RateLimitRules(
                endpoint_limits={
                    "/api/v1/chat/completions": 200,
                    "/api/v1/requests": 300,
                    "/api/v1/rules": 100,
                    "/api/v1/alerts": 150,
                    "/api/v1/auth/login": 20,
                    "/api/v1/auth/register": 10,
                    "default": 250
                },
                burst_limits={
                    "/api/v1/chat/completions": 30,
                    "/api/v1/auth/login": 10,
                    "/api/v1/auth/register": 5,
                    "default": 50
                },
                ip_hourly_limits={
                    "default": 5000,
                    "authenticated": 10000,
                    "admin": 20000
                },
                user_role_limits={
                    "guest": 100,
                    "user": 500,
                    "premium": 1000,
                    "admin": 5000
                },
                ddos_threshold=100,  # More lenient in dev
                ddos_block_duration=300,  # 5 minutes
                whitelist_ips={"127.0.0.1", "::1", "localhost"}
            )
        
        elif self.security_level == SecurityLevel.STAGING:
            return RateLimitRules(
                endpoint_limits={
                    "/api/v1/chat/completions": 100,
                    "/api/v1/requests": 200,
                    "/api/v1/rules": 50,
                    "/api/v1/alerts": 100,
                    "/api/v1/auth/login": 10,
                    "/api/v1/auth/register": 5,
                    "default": 150
                },
                burst_limits={
                    "/api/v1/chat/completions": 20,
                    "/api/v1/auth/login": 5,
                    "/api/v1/auth/register": 3,
                    "default": 30
                },
                ip_hourly_limits={
                    "default": 2000,
                    "authenticated": 8000,
                    "admin": 15000
                },
                user_role_limits={
                    "guest": 50,
                    "user": 300,
                    "premium": 800,
                    "admin": 3000
                },
                ddos_threshold=75,
                ddos_block_duration=1800,  # 30 minutes
            )
        
        elif self.security_level == SecurityLevel.PRODUCTION:
            return RateLimitRules(
                endpoint_limits={
                    "/api/v1/chat/completions": 60,
                    "/api/v1/requests": 120,
                    "/api/v1/rules": 30,
                    "/api/v1/alerts": 60,
                    "/api/v1/auth/login": 5,
                    "/api/v1/auth/register": 3,
                    "default": 100
                },
                burst_limits={
                    "/api/v1/chat/completions": 10,
                    "/api/v1/auth/login": 3,
                    "/api/v1/auth/register": 2,
                    "default": 20
                },
                ip_hourly_limits={
                    "default": 1000,
                    "authenticated": 5000,
                    "admin": 10000
                },
                user_role_limits={
                    "guest": 50,
                    "user": 200,
                    "premium": 500,
                    "admin": 2000
                },
                ddos_threshold=50,
                ddos_block_duration=3600,  # 1 hour
            )
        
        else:  # HIGH_SECURITY
            return RateLimitRules(
                endpoint_limits={
                    "/api/v1/chat/completions": 30,
                    "/api/v1/requests": 60,
                    "/api/v1/rules": 15,
                    "/api/v1/alerts": 30,
                    "/api/v1/auth/login": 3,
                    "/api/v1/auth/register": 2,
                    "default": 50
                },
                burst_limits={
                    "/api/v1/chat/completions": 5,
                    "/api/v1/auth/login": 2,
                    "/api/v1/auth/register": 1,
                    "default": 10
                },
                ip_hourly_limits={
                    "default": 500,
                    "authenticated": 2000,
                    "admin": 5000
                },
                user_role_limits={
                    "guest": 25,
                    "user": 100,
                    "premium": 250,
                    "admin": 1000
                },
                ddos_threshold=25,
                ddos_block_duration=7200,  # 2 hours
            )
    
    def _get_monitoring_config(self) -> Dict:
        """Get security monitoring configuration"""
        base_config = {
            "event_retention_days": 30,
            "alert_retention_hours": 24,
            "risk_score_retention_hours": 24,
            "dashboard_refresh_seconds": 30,
        }
        
        if self.security_level in [SecurityLevel.PRODUCTION, SecurityLevel.HIGH_SECURITY]:
            base_config.update({
                "event_retention_days": 90,
                "alert_retention_hours": 168,  # 1 week
                "risk_score_retention_hours": 168,
                "enable_real_time_alerts": True,
                "enable_geographic_tracking": True,
                "enable_behavioral_analysis": True,
                "auto_block_high_risk": True,
                "auto_block_threshold": 85 if self.security_level == SecurityLevel.HIGH_SECURITY else 90
            })
        else:
            base_config.update({
                "enable_real_time_alerts": False,
                "enable_geographic_tracking": False,
                "enable_behavioral_analysis": False,
                "auto_block_high_risk": False
            })
        
        return base_config
    
    def _get_encryption_config(self) -> Dict:
        """Get encryption configuration"""
        base_config = {
            "algorithm": "Fernet",  # AES-128-CBC + HMAC-SHA256
            "key_rotation_days": 90,
            "enable_field_encryption": True,
        }
        
        if self.security_level == SecurityLevel.DEVELOPMENT:
            base_config.update({
                "kdf_iterations": 100000,  # Lower for dev performance
                "enable_encryption_caching": True
            })
        elif self.security_level in [SecurityLevel.PRODUCTION, SecurityLevel.HIGH_SECURITY]:
            base_config.update({
                "kdf_iterations": 600000,  # OWASP 2024 recommendation
                "enable_encryption_caching": False,  # No caching for security
                "require_secure_key_storage": True,
                "enable_key_audit_logging": True
            })
            
            if self.security_level == SecurityLevel.HIGH_SECURITY:
                base_config.update({
                    "algorithm": "ChaCha20Poly1305",  # More secure for high-security
                    "kdf_iterations": 1000000,
                    "key_rotation_days": 30,  # More frequent rotation
                    "enable_double_encryption": True
                })
        else:  # STAGING
            base_config.update({
                "kdf_iterations": 480000,
                "enable_encryption_caching": False
            })
        
        return base_config
    
    def _get_auth_config(self) -> Dict:
        """Get authentication configuration"""
        base_config = {
            "jwt_expiration_minutes": 60,
            "refresh_token_days": 7,
            "password_min_length": 8,
            "require_2fa": False,
        }
        
        if self.security_level == SecurityLevel.DEVELOPMENT:
            base_config.update({
                "jwt_expiration_minutes": 480,  # 8 hours for dev convenience
                "refresh_token_days": 30,
                "password_min_length": 6,
                "enable_test_users": True
            })
        elif self.security_level in [SecurityLevel.PRODUCTION, SecurityLevel.HIGH_SECURITY]:
            base_config.update({
                "jwt_expiration_minutes": 30,
                "refresh_token_days": 3,
                "password_min_length": 12,
                "require_strong_passwords": True,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 30,
                "enable_session_monitoring": True
            })
            
            if self.security_level == SecurityLevel.HIGH_SECURITY:
                base_config.update({
                    "jwt_expiration_minutes": 15,
                    "refresh_token_days": 1,
                    "require_2fa": True,
                    "password_min_length": 16,
                    "max_login_attempts": 3,
                    "lockout_duration_minutes": 60
                })
        else:  # STAGING
            base_config.update({
                "jwt_expiration_minutes": 45,
                "refresh_token_days": 5,
                "password_min_length": 10,
                "max_login_attempts": 8,
                "lockout_duration_minutes": 15
            })
        
        return base_config
    
    def get_cors_config(self) -> Dict:
        """Get CORS configuration based on security level"""
        if self.security_level == SecurityLevel.DEVELOPMENT:
            return {
                "allow_origins": ["*"],
                "allow_methods": ["*"],
                "allow_headers": ["*"],
                "allow_credentials": True
            }
        elif self.security_level == SecurityLevel.STAGING:
            return {
                "allow_origins": [
                    "https://staging.shadowai.com",
                    "https://dev.shadowai.com"
                ],
                "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
                "allow_credentials": True
            }
        else:  # PRODUCTION or HIGH_SECURITY
            return {
                "allow_origins": [
                    "https://shadowai.com",
                    "https://app.shadowai.com"
                ],
                "allow_methods": ["GET", "POST", "PUT", "PATCH"],
                "allow_headers": ["Content-Type", "Authorization"],
                "allow_credentials": True
            }
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers configuration"""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        if self.security_level in [SecurityLevel.PRODUCTION, SecurityLevel.HIGH_SECURITY]:
            headers.update({
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
            })
            
            if self.security_level == SecurityLevel.HIGH_SECURITY:
                headers.update({
                    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:",
                    "Expect-CT": "max-age=86400, enforce"
                })
        
        return headers
    
    def should_enable_feature(self, feature: str) -> bool:
        """Check if a security feature should be enabled"""
        feature_config = {
            "request_logging": True,
            "error_detail_exposure": self.security_level == SecurityLevel.DEVELOPMENT,
            "debug_endpoints": self.security_level == SecurityLevel.DEVELOPMENT,
            "metrics_endpoint": True,
            "health_check_details": self.security_level != SecurityLevel.HIGH_SECURITY,
            "swagger_ui": self.security_level in [SecurityLevel.DEVELOPMENT, SecurityLevel.STAGING],
            "admin_interface": True,
            "bulk_operations": self.security_level != SecurityLevel.HIGH_SECURITY,
            "file_uploads": self.security_level != SecurityLevel.HIGH_SECURITY,
        }
        
        return feature_config.get(feature, False)
    
    def get_logging_config(self) -> Dict:
        """Get logging configuration for security"""
        config = {
            "level": "INFO",
            "enable_audit_log": False,
            "log_requests": True,
            "log_responses": False,
            "mask_sensitive_fields": True
        }
        
        if self.security_level in [SecurityLevel.PRODUCTION, SecurityLevel.HIGH_SECURITY]:
            config.update({
                "level": "WARNING",
                "enable_audit_log": True,
                "log_security_events": True,
                "enable_structured_logging": True,
                "enable_log_forwarding": True
            })
            
            if self.security_level == SecurityLevel.HIGH_SECURITY:
                config.update({
                    "level": "ERROR",
                    "log_all_requests": True,
                    "log_all_responses": True,
                    "enable_forensic_logging": True
                })
        
        return config

# Global security configuration instance
def get_security_config() -> SecurityConfiguration:
    """Get the global security configuration"""
    return SecurityConfiguration()

# Example usage patterns
"""
# In your FastAPI app
from config.security_config import get_security_config

security_config = get_security_config()

# Apply rate limiting
rate_limits = security_config.rate_limits

# Apply CORS
cors_config = security_config.get_cors_config()

# Apply security headers
security_headers = security_config.get_security_headers()

# Check features
if security_config.should_enable_feature('debug_endpoints'):
    app.include_router(debug_router)
"""