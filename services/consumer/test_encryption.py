#!/usr/bin/env python3
"""
Test script for encryption functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encryption_service import EncryptionService
from config import settings

def test_encryption_service():
    """Test encryption service functionality"""
    print("Testing Encryption Service...")
    print(f"Master key configured: {len(settings.encryption_key) >= 32}")
    
    # Initialize encryption service
    encryption_service = EncryptionService()
    status = encryption_service.get_encryption_status()
    
    print(f"\nEncryption Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    if not status['encryption_enabled']:
        print("\n⚠️  Encryption is not enabled. Check your ENCRYPTION_KEY configuration.")
        return
    
    # Test data
    test_cases = [
        {
            'field': 'prompt',
            'data': 'My password is secret123 and my email is user@company.com',
            'description': 'Sensitive prompt with password and email'
        },
        {
            'field': 'response',
            'data': 'I cannot help you with passwords or personal information.',
            'description': 'LLM response'
        },
        {
            'field': 'headers',
            'data': '{"Authorization": "Bearer sk-1234567890", "User-Agent": "MyApp/1.0"}',
            'description': 'HTTP headers with API key'
        }
    ]
    
    print(f"\n{'='*60}")
    print("ENCRYPTION TESTS")
    print(f"{'='*60}")
    
    for i, case in enumerate(test_cases, 1):
        field = case['field']
        original_data = case['data']
        description = case['description']
        
        print(f"\nTest {i}: {description}")
        print(f"Field: {field}")
        print(f"Original: {original_data[:100]}{'...' if len(original_data) > 100 else ''}")
        
        # Encrypt data
        encrypted = encryption_service.encrypt_field(field, original_data)
        print(f"Encrypted: {encrypted[:50] if encrypted else 'None'}...")
        print(f"Is encrypted: {encryption_service.is_encrypted(encrypted)}")
        
        # Decrypt data
        decrypted = encryption_service.decrypt_field(field, encrypted)
        print(f"Decrypted: {decrypted[:100] if decrypted else 'None'}{'...' if len(decrypted or '') > 100 else ''}")
        
        # Verify roundtrip
        success = original_data == decrypted
        print(f"Roundtrip success: {'✓' if success else '✗'}")
        
        if not success:
            print(f"ERROR: Decrypted data doesn't match original!")
            print(f"Expected: {original_data}")
            print(f"Got: {decrypted}")
        
        print("-" * 50)
    
    # Test convenience methods
    print(f"\n{'='*60}")
    print("CONVENIENCE METHOD TESTS")
    print(f"{'='*60}")
    
    test_prompt = "What is my API key abc-123-def?"
    test_response = "I cannot provide API keys."
    test_headers = '{"Content-Type": "application/json"}'
    
    print(f"\nTesting convenience methods...")
    
    # Test prompt methods
    encrypted_prompt = encryption_service.encrypt_prompt(test_prompt)
    decrypted_prompt = encryption_service.decrypt_prompt(encrypted_prompt)
    print(f"Prompt roundtrip: {'✓' if test_prompt == decrypted_prompt else '✗'}")
    
    # Test response methods
    encrypted_response = encryption_service.encrypt_response(test_response)
    decrypted_response = encryption_service.decrypt_response(encrypted_response)
    print(f"Response roundtrip: {'✓' if test_response == decrypted_response else '✗'}")
    
    # Test headers methods
    encrypted_headers = encryption_service.encrypt_headers(test_headers)
    decrypted_headers = encryption_service.decrypt_headers(encrypted_headers)
    print(f"Headers roundtrip: {'✓' if test_headers == decrypted_headers else '✗'}")
    
    # Test with None values
    print(f"\nTesting with None values...")
    print(f"encrypt_prompt(None): {encryption_service.encrypt_prompt(None)}")
    print(f"decrypt_prompt(None): {encryption_service.decrypt_prompt(None)}")
    print(f"encrypt_prompt(''): {encryption_service.encrypt_prompt('')}")
    
    # Test double encryption protection
    print(f"\nTesting double encryption protection...")
    double_encrypted = encryption_service.encrypt_prompt(encrypted_prompt)
    print(f"Double encrypt same as single: {'✓' if encrypted_prompt == double_encrypted else '✗'}")
    
    # Test lazy decryption (unencrypted data)
    print(f"\nTesting lazy decryption...")
    unencrypted_data = "This is plain text"
    lazy_decrypted = encryption_service.decrypt_prompt(unencrypted_data)
    print(f"Lazy decrypt unencrypted: {'✓' if unencrypted_data == lazy_decrypted else '✗'}")

def test_key_rotation():
    """Test key rotation functionality"""
    print(f"\n{'='*60}")
    print("KEY ROTATION TEST")
    print(f"{'='*60}")
    
    encryption_service = EncryptionService()
    
    if not encryption_service.encryption_enabled:
        print("Encryption not enabled - skipping key rotation test")
        return
    
    # Encrypt data with original key
    original_data = "Sensitive data for key rotation test"
    encrypted_original = encryption_service.encrypt_prompt(original_data)
    print(f"Original encryption: {encrypted_original[:50]}...")
    
    # Rotate keys
    new_key = "new-super-secret-key-for-rotation-test-32chars"
    rotation_success = encryption_service.rotate_keys(new_key)
    print(f"Key rotation success: {'✓' if rotation_success else '✗'}")
    
    if rotation_success:
        # Encrypt same data with new key
        encrypted_new = encryption_service.encrypt_prompt(original_data)
        print(f"New key encryption: {encrypted_new[:50]}...")
        
        # Verify they're different
        different = encrypted_original != encrypted_new
        print(f"Encrypted values differ: {'✓' if different else '✗'}")
        
        # Verify new encryption works
        decrypted_new = encryption_service.decrypt_prompt(encrypted_new)
        roundtrip_success = original_data == decrypted_new
        print(f"New key roundtrip: {'✓' if roundtrip_success else '✗'}")
    
    print("Note: Old encrypted data would need migration after key rotation in production")

if __name__ == "__main__":
    try:
        test_encryption_service()
        test_key_rotation()
        print(f"\n{'='*60}")
        print("ENCRYPTION TESTING COMPLETED!")
        print(f"{'='*60}")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()