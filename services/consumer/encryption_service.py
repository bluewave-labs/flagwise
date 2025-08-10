import os
import base64
import logging
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from config import settings

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting/decrypting sensitive data fields"""
    
    def __init__(self):
        self.master_key = None
        self.field_keys = {}
        self.encryption_enabled = False
        
        # Initialize encryption
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption with master key from settings"""
        try:
            encryption_key = getattr(settings, 'encryption_key', None)
            
            if not encryption_key or encryption_key == 'your-secret-key-here-32-chars-min':
                logger.warning("Encryption key not configured - data will be stored unencrypted")
                return
            
            if len(encryption_key) < 32:
                logger.error("Encryption key must be at least 32 characters")
                return
            
            self.master_key = encryption_key.encode('utf-8')
            self.encryption_enabled = True
            
            # Pre-generate field-specific keys
            self._generate_field_keys()
            
            logger.info("Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self.encryption_enabled = False
    
    def _generate_field_keys(self):
        """Generate field-specific encryption keys using PBKDF2"""
        if not self.master_key:
            return
        
        fields = ['prompt', 'response', 'headers']
        
        for field in fields:
            try:
                # Use field name as salt (in production, use random salts)
                salt = f"shadow_ai_{field}".encode('utf-8')
                
                # Derive key using PBKDF2
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                
                field_key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
                self.field_keys[field] = Fernet(field_key)
                
                logger.debug(f"Generated encryption key for field: {field}")
                
            except Exception as e:
                logger.error(f"Failed to generate key for field {field}: {e}")
    
    def is_encrypted(self, data: Optional[str]) -> bool:
        """Check if data appears to be encrypted (starts with encryption prefix)"""
        if not data:
            return False
        
        # Check for Fernet token format (base64 with specific structure)
        try:
            if data.startswith('gAAAAA'):  # Fernet tokens start with this prefix
                return True
        except:
            pass
        
        return False
    
    def encrypt_field(self, field_name: str, data: Optional[str]) -> Optional[str]:
        """Encrypt data for a specific field"""
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
            encrypted_data = fernet.encrypt(data.encode('utf-8'))
            return encrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to encrypt {field_name}: {e}")
            # Return original data if encryption fails
            return data
    
    def decrypt_field(self, field_name: str, data: Optional[str]) -> Optional[str]:
        """Decrypt data for a specific field"""
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
            fernet = self.field_keys[field_name]
            decrypted_data = fernet.decrypt(data.encode('utf-8'))
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to decrypt {field_name}: {e}")
            # Return original data if decryption fails
            return data
    
    def encrypt_prompt(self, prompt: Optional[str]) -> Optional[str]:
        """Encrypt prompt field"""
        return self.encrypt_field('prompt', prompt)
    
    def decrypt_prompt(self, encrypted_prompt: Optional[str]) -> Optional[str]:
        """Decrypt prompt field"""
        return self.decrypt_field('prompt', encrypted_prompt)
    
    def encrypt_response(self, response: Optional[str]) -> Optional[str]:
        """Encrypt response field"""
        return self.encrypt_field('response', response)
    
    def decrypt_response(self, encrypted_response: Optional[str]) -> Optional[str]:
        """Decrypt response field"""
        return self.decrypt_field('response', encrypted_response)
    
    def encrypt_headers(self, headers: Optional[str]) -> Optional[str]:
        """Encrypt headers field (JSON string)"""
        return self.encrypt_field('headers', headers)
    
    def decrypt_headers(self, encrypted_headers: Optional[str]) -> Optional[str]:
        """Decrypt headers field"""
        return self.decrypt_field('headers', encrypted_headers)
    
    def rotate_keys(self, new_master_key: str) -> bool:
        """Rotate encryption keys (for quarterly rotation)"""
        try:
            if len(new_master_key) < 32:
                logger.error("New encryption key must be at least 32 characters")
                return False
            
            # Store old keys for decryption
            old_field_keys = self.field_keys.copy()
            
            # Generate new keys
            self.master_key = new_master_key.encode('utf-8')
            self.field_keys = {}
            self._generate_field_keys()
            
            logger.info("Encryption keys rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate encryption keys: {e}")
            # Restore old keys
            self.field_keys = old_field_keys
            return False
    
    def get_encryption_status(self) -> dict:
        """Get encryption service status"""
        return {
            'encryption_enabled': self.encryption_enabled,
            'master_key_configured': bool(self.master_key),
            'field_keys_generated': len(self.field_keys),
            'supported_fields': list(self.field_keys.keys()) if self.field_keys else []
        }

# Global instance for use across services
encryption_service = EncryptionService()