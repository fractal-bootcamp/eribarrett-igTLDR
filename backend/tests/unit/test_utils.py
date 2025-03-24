"""
Unit tests for utilities module.
"""
import os
import pytest
from utils import encrypt_data, decrypt_data

class TestEncryption:
    """Tests for encryption and decryption utilities."""
    
    def test_encrypt_decrypt_cycle(self):
        """Test that data can be encrypted and then decrypted correctly."""
        # Original data
        original_data = {
            "username": "testuser",
            "sessionid": "test123",
            "csrftoken": "aabbcc"
        }
        
        # Encrypt the data
        encrypted = encrypt_data(original_data)
        
        # Ensure encrypted data is not equal to original
        assert encrypted != original_data
        assert isinstance(encrypted, str)
        
        # Decrypt the data
        decrypted = decrypt_data(encrypted)
        
        # Verify decrypted data matches original
        assert decrypted == original_data
    
    def test_encrypt_with_none(self):
        """Test encrypt_data with None returns None."""
        assert encrypt_data(None) is None
    
    def test_decrypt_with_none(self):
        """Test decrypt_data with None returns None."""
        assert decrypt_data(None) is None 