# Import the same encryption service from consumer
# In production, this should be a shared library
import sys
import os

# Add consumer path to import encryption service
consumer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'consumer')
if consumer_path not in sys.path:
    sys.path.append(consumer_path)

try:
    from encryption_service import encryption_service
    __all__ = ['encryption_service']
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import encryption service: {e}")
    
    # Create a dummy service that does nothing
    class DummyEncryptionService:
        def decrypt_prompt(self, data):
            return data
        def decrypt_response(self, data):
            return data
        def decrypt_headers(self, data):
            return data
        def is_encrypted(self, data):
            return False
        def get_encryption_status(self):
            return {'encryption_enabled': False, 'error': 'Import failed'}
    
    encryption_service = DummyEncryptionService()
    __all__ = ['encryption_service']