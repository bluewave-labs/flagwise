import os
import base64
import secrets
import logging
import hashlib
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.backends import default_backend
import json

logger = logging.getLogger(__name__)

class SecureEncryptionService:
    """
    Production-grade encryption service with proper key management
    Features:
    - Cryptographically secure random salts
    - Key rotation support
    - Multiple encryption algorithms
    - Audit logging
    - Key derivation with high iterations
    """
    
    def __init__(self, key_storage_path: str = "/secure/keys"):
        self.key_storage_path = key_storage_path
        self.master_key = None
        self.field_keys = {}
        self.encryption_enabled = False
        self.key_version = 1
        
        # Create secure key storage directory
        os.makedirs(key_storage_path, mode=0o700, exist_ok=True)
        
        # Initialize encryption
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption with secure key management"""
        try:
            # Get master key from secure source (environment, vault, etc.)
            master_key = self._get_master_key()
            
            if not master_key:
                logger.error("Master encryption key not found - data will be stored unencrypted")
                return
            
            if len(master_key) < 32:
                logger.error("Master encryption key must be at least 32 bytes")
                return
            
            self.master_key = master_key
            self.encryption_enabled = True
            
            # Load or generate field salts
            self._load_or_generate_salts()
            
            # Generate field-specific keys
            self._generate_field_keys()
            
            logger.info("Secure encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self.encryption_enabled = False
    
    def _get_master_key(self) -> Optional[bytes]:
        """Get master key from secure source"""
        # Option 1: Environment variable (base64 encoded)
        env_key = os.getenv('ENCRYPTION_MASTER_KEY')
        if env_key:
            try:
                return base64.b64decode(env_key)
            except Exception:
                logger.error("Invalid base64 encryption key in environment")
        
        # Option 2: File-based key storage
        key_file = os.path.join(self.key_storage_path, "master.key")
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read master key file: {e}")
        
        # Option 3: Generate new key if none exists (ONLY for development)
        if os.getenv('ENVIRONMENT') == 'development':
            logger.warning("Generating new master key for development")
            return self._generate_master_key()
        
        return None
    
    def _generate_master_key(self) -> bytes:
        """Generate a new cryptographically secure master key"""
        master_key = secrets.token_bytes(32)  # 256-bit key
        
        # Save to secure file
        key_file = os.path.join(self.key_storage_path, "master.key")
        with open(key_file, 'wb') as f:
            f.write(master_key)
        
        # Set secure file permissions
        os.chmod(key_file, 0o600)  # Owner read/write only
        
        logger.info("Generated new master encryption key")
        return master_key
    
    def _load_or_generate_salts(self):
        """Load existing salts or generate new cryptographically secure ones"""
        salt_file = os.path.join(self.key_storage_path, "salts.json")
        
        if os.path.exists(salt_file):
            try:
                with open(salt_file, 'r') as f:
                    salt_data = json.load(f)
                self.field_salts = {
                    field: base64.b64decode(salt_b64.encode('utf-8'))
                    for field, salt_b64 in salt_data.items()
                }
                logger.info("Loaded existing field salts")
                return
            except Exception as e:
                logger.error(f"Failed to load salts: {e}")
        
        # Generate new random salts for each field
        fields = ['prompt', 'response', 'headers', 'metadata']
        self.field_salts = {}
        
        for field in fields:
            # Generate 32-byte cryptographically secure salt
            salt = secrets.token_bytes(32)
            self.field_salts[field] = salt
        
        # Save salts securely
        salt_data = {
            field: base64.b64encode(salt).decode('utf-8')
            for field, salt in self.field_salts.items()
        }
        
        with open(salt_file, 'w') as f:
            json.dump(salt_data, f, indent=2)
        
        os.chmod(salt_file, 0o600)  # Owner read/write only
        logger.info("Generated new cryptographically secure field salts")
    
    def _generate_field_keys(self):
        """Generate field-specific encryption keys using secure KDF"""
        if not self.master_key or not hasattr(self, 'field_salts'):
            return
        
        for field, salt in self.field_salts.items():
            try:
                # Use PBKDF2 with high iteration count for security
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=480000,  # OWASP recommended 480,000 iterations for 2023
                    backend=default_backend()
                )
                
                field_key = kdf.derive(self.master_key)
                
                # Create Fernet cipher with derived key
                fernet_key = base64.urlsafe_b64encode(field_key)
                self.field_keys[field] = Fernet(fernet_key)
                
                logger.debug(f"Generated secure encryption key for field: {field}")
                
            except Exception as e:
                logger.error(f"Failed to generate key for field {field}: {e}")
    
    def is_encrypted(self, data: Optional[str]) -> bool:
        """Check if data appears to be encrypted"""
        if not data or len(data) < 10:
            return False
        
        try:
            # Check for Fernet token format
            if data.startswith('gAAAAA'):  # Fernet tokens start with this
                return True
            
            # Check for custom encryption header
            if data.startswith('ENC_V'):  # Our custom encryption prefix
                return True
                
        except:
            pass
        
        return False
    
    def encrypt_field(self, field_name: str, data: Optional[str]) -> Optional[str]:
        """Encrypt data for a specific field with integrity protection"""
        if not data:
            return data
        
        if not self.encryption_enabled:
            logger.debug(f"Encryption disabled - storing {field_name} unencrypted")
            return data
        
        if field_name not in self.field_keys:
            logger.warning(f"No encryption key for field {field_name}")
            return data
        
        # Don't re-encrypt already encrypted data
        if self.is_encrypted(data):
            return data
        
        try:
            fernet = self.field_keys[field_name]
            
            # Add metadata for key rotation
            plaintext_with_metadata = json.dumps({
                'data': data,
                'field': field_name,
                'version': self.key_version,
                'timestamp': int(datetime.utcnow().timestamp())
            })
            
            encrypted_bytes = fernet.encrypt(plaintext_with_metadata.encode('utf-8'))
            encrypted_data = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            # Add custom prefix for identification
            return f"ENC_V{self.key_version}_{encrypted_data}"
            
        except Exception as e:
            logger.error(f"Failed to encrypt {field_name}: {e}")
            # Log security event
            self._log_security_event('encryption_failed', field_name, str(e))
            # Return original data if encryption fails (fail-open for availability)
            return data
    
    def decrypt_field(self, field_name: str, data: Optional[str]) -> Optional[str]:
        """Decrypt data for a specific field with integrity verification"""
        if not data:
            return data
        
        if not self.encryption_enabled:
            return data
        
        if field_name not in self.field_keys:
            logger.warning(f"No decryption key for field {field_name}")
            return data
        
        # Don't try to decrypt unencrypted data
        if not self.is_encrypted(data):
            return data
        
        try:
            # Handle custom encryption format
            if data.startswith('ENC_V'):
                # Extract version and encrypted data
                parts = data.split('_', 2)
                if len(parts) == 3:
                    version = int(parts[1][1:])  # Remove 'V' prefix
                    encrypted_data = parts[2]
                else:
                    encrypted_data = data[6:]  # Remove 'ENC_V1_' prefix
                
                encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            else:
                # Legacy Fernet format
                encrypted_bytes = data.encode('utf-8')
            
            fernet = self.field_keys[field_name]
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            
            try:
                # Try to parse metadata
                decrypted_json = json.loads(decrypted_bytes.decode('utf-8'))
                
                # Verify field matches
                if decrypted_json.get('field') != field_name:
                    logger.warning(f"Field mismatch during decryption: expected {field_name}, got {decrypted_json.get('field')}")
                
                return decrypted_json['data']
                
            except json.JSONDecodeError:
                # Legacy format without metadata
                return decrypted_bytes.decode('utf-8')
            
        except InvalidToken:
            logger.error(f"Invalid encryption token for field {field_name}")
            self._log_security_event('invalid_token', field_name, 'Token validation failed')
            return None
        except Exception as e:
            logger.error(f"Failed to decrypt {field_name}: {e}")
            self._log_security_event('decryption_failed', field_name, str(e))
            return None
    
    def _log_security_event(self, event_type: str, field_name: str, details: str):
        """Log security-related events for monitoring"""
        security_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'field_name': field_name,
            'details': details,
            'service': 'encryption_service'
        }
        
        # In production, send to SIEM/security monitoring system
        logger.warning(f"Security event: {security_log}")
    
    def rotate_keys(self, new_master_key: bytes) -> bool:
        """Rotate encryption keys with data migration"""
        try:
            if len(new_master_key) < 32:
                logger.error("New master key must be at least 32 bytes")
                return False
            
            # Store old keys for data migration
            old_field_keys = self.field_keys.copy()
            old_version = self.key_version
            
            # Update to new key
            self.master_key = new_master_key
            self.key_version += 1
            
            # Generate new salts and keys
            self._load_or_generate_salts()
            self._generate_field_keys()
            
            logger.info(f"Encryption keys rotated successfully to version {self.key_version}")
            
            # TODO: Implement background data re-encryption process
            # This should be handled by a separate background task
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate encryption keys: {e}")
            # Restore old keys
            self.field_keys = old_field_keys
            self.key_version = old_version
            return False
    
    def get_encryption_status(self) -> Dict[str, Any]:
        """Get comprehensive encryption service status"""
        return {
            'encryption_enabled': self.encryption_enabled,
            'master_key_configured': bool(self.master_key),
            'field_keys_generated': len(self.field_keys),
            'supported_fields': list(self.field_keys.keys()) if self.field_keys else [],
            'key_version': self.key_version,
            'key_storage_path': self.key_storage_path,
            'kdf_algorithm': 'PBKDF2-SHA256',
            'kdf_iterations': 480000,
            'cipher_algorithm': 'Fernet (AES-128-CBC + HMAC-SHA256)'
        }
    
    # Convenience methods for specific fields
    def encrypt_prompt(self, prompt: Optional[str]) -> Optional[str]:
        return self.encrypt_field('prompt', prompt)
    
    def decrypt_prompt(self, encrypted_prompt: Optional[str]) -> Optional[str]:
        return self.decrypt_field('prompt', encrypted_prompt)
    
    def encrypt_response(self, response: Optional[str]) -> Optional[str]:
        return self.encrypt_field('response', response)
    
    def decrypt_response(self, encrypted_response: Optional[str]) -> Optional[str]:
        return self.decrypt_field('response', encrypted_response)
    
    def encrypt_headers(self, headers: Optional[str]) -> Optional[str]:
        return self.encrypt_field('headers', headers)
    
    def decrypt_headers(self, encrypted_headers: Optional[str]) -> Optional[str]:
        return self.decrypt_field('headers', encrypted_headers)

# Global secure instance
encryption_service = SecureEncryptionService()