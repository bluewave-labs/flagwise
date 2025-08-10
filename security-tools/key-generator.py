#!/usr/bin/env python3
"""
Secure Key Generation Tool for Shadow AI
Generates cryptographically secure keys for production deployment
"""

import secrets
import base64
import os
from cryptography.fernet import Fernet

def generate_jwt_secret(length: int = 32) -> str:
    """Generate a secure JWT secret key"""
    return secrets.token_urlsafe(length)

def generate_encryption_key() -> str:
    """Generate a secure encryption master key"""
    key_bytes = secrets.token_bytes(32)  # 256-bit key
    return base64.b64encode(key_bytes).decode('utf-8')

def generate_database_password(length: int = 24) -> str:
    """Generate a secure database password"""
    # Use alphanumeric + special chars, but avoid ambiguous characters
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_all_keys():
    """Generate all required keys for production deployment"""
    print("=== Shadow AI Security Key Generation ===\n")
    
    print("🔐 JWT Secret Key:")
    jwt_secret = generate_jwt_secret()
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    
    print("🔐 Encryption Master Key:")
    encryption_key = generate_encryption_key()
    print(f"ENCRYPTION_KEY={encryption_key}")
    print()
    
    print("🔐 Database Password:")
    db_password = generate_database_password()
    print(f"POSTGRES_PASSWORD={db_password}")
    print()
    
    print("🔐 Redis Password:")
    redis_password = generate_database_password()
    print(f"REDIS_PASSWORD={redis_password}")
    print()
    
    print("🔐 Kafka Password:")
    kafka_password = generate_database_password()
    print(f"KAFKA_PASSWORD={kafka_password}")
    print()
    
    # Generate .env file
    env_content = f"""# Shadow AI Production Environment Variables
# Generated on {datetime.now().isoformat()}
# KEEP THESE KEYS SECURE - DO NOT COMMIT TO VERSION CONTROL

# JWT Security
JWT_SECRET_KEY={jwt_secret}
ENCRYPTION_KEY={encryption_key}

# Database Security
POSTGRES_USER=shadow_ai_prod
POSTGRES_PASSWORD={db_password}
POSTGRES_DB=shadow_ai_production

# Redis Security
REDIS_PASSWORD={redis_password}

# Kafka Security
KAFKA_USERNAME=shadow_ai_service
KAFKA_PASSWORD={kafka_password}
KAFKA_AUTH_TYPE=SASL_SSL

# Network Security
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
"""
    
    with open('.env.production', 'w') as f:
        f.write(env_content)
    
    # Set secure permissions
    os.chmod('.env.production', 0o600)
    
    print("✅ Generated .env.production file with secure permissions")
    print("\n⚠️  SECURITY REMINDER:")
    print("1. Store these keys in a secure password manager")
    print("2. Use environment-specific secret management (AWS Secrets Manager, HashiCorp Vault)")
    print("3. Never commit .env files to version control")
    print("4. Rotate keys regularly (quarterly)")
    print("5. Monitor for key exposure in logs/error messages")

if __name__ == "__main__":
    from datetime import datetime
    generate_all_keys()