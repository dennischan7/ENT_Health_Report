"""
Tests for encryption utilities.
"""

import pytest
from cryptography.fernet import Fernet

from app.core.encryption import (
    generate_encryption_key,
    encrypt,
    decrypt,
    encrypt_dict,
    decrypt_dict,
)


class TestGenerateEncryptionKey:
    """Tests for generate_encryption_key function."""

    def test_generate_key_returns_string(self):
        """Test that key generation returns a string."""
        key = generate_encryption_key()
        assert isinstance(key, str)

    def test_generate_key_is_valid_fernet_key(self):
        """Test that generated key is valid for Fernet."""
        key = generate_encryption_key()
        # Should not raise exception
        f = Fernet(key.encode("utf-8"))
        assert f is not None

    def test_generate_key_is_44_chars(self):
        """Test that generated key is 44 characters (base64 encoded 32 bytes)."""
        key = generate_encryption_key()
        assert len(key) == 44

    def test_generate_key_is_unique(self):
        """Test that each generated key is unique."""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        assert key1 != key2


class TestEncryptDecrypt:
    """Tests for encrypt and decrypt functions."""

    def test_encrypt_decrypt_simple_string(self):
        """Test basic encrypt/decrypt roundtrip."""
        key = generate_encryption_key()
        plaintext = "test-api-key"

        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)

        assert decrypted == plaintext

    def test_encrypt_decrypt_empty_string(self):
        """Test encrypt/decrypt with empty string."""
        key = generate_encryption_key()

        encrypted = encrypt("", key)
        decrypted = decrypt(encrypted, key)

        assert decrypted == ""

    def test_encrypt_decrypt_long_string(self):
        """Test encrypt/decrypt with long string."""
        key = generate_encryption_key()
        plaintext = "a" * 1000

        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)

        assert decrypted == plaintext

    def test_encrypt_decrypt_with_special_chars(self):
        """Test encrypt/decrypt with special characters."""
        key = generate_encryption_key()
        plaintext = "sk-test-123!@#$%^&*()_+-=[]{}|;':\",./<>?"

        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)

        assert decrypted == plaintext

    def test_encrypt_decrypt_with_unicode(self):
        """Test encrypt/decrypt with unicode characters."""
        key = generate_encryption_key()
        plaintext = "你好世界 🌍 مرحبا"

        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)

        assert decrypted == plaintext

    def test_encrypt_returns_different_ciphertext(self):
        """Test that encryption produces different ciphertext each time (due to IV)."""
        key = generate_encryption_key()
        plaintext = "same-plaintext"

        encrypted1 = encrypt(plaintext, key)
        encrypted2 = encrypt(plaintext, key)

        # Different ciphertext due to Fernet's random IV
        assert encrypted1 != encrypted2

        # But both decrypt to same plaintext
        assert decrypt(encrypted1, key) == plaintext
        assert decrypt(encrypted2, key) == plaintext

    def test_decrypt_with_wrong_key_raises_error(self):
        """Test that decryption with wrong key raises error."""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        plaintext = "secret-data"

        encrypted = encrypt(plaintext, key1)

        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(encrypted, key2)

    def test_decrypt_invalid_ciphertext_raises_error(self):
        """Test that decryption of invalid ciphertext raises error."""
        key = generate_encryption_key()

        with pytest.raises(ValueError):
            decrypt("invalid-ciphertext", key)


class TestEncryptDecryptDict:
    """Tests for encrypt_dict and decrypt_dict functions."""

    def test_encrypt_decrypt_dict_simple(self):
        """Test encrypt/decrypt dict with simple values."""
        key = generate_encryption_key()
        data = {
            "api_key": "sk-12345",
            "secret": "my-secret",
        }

        encrypted = encrypt_dict(data, key)
        decrypted = decrypt_dict(encrypted, key)

        assert decrypted == data

    def test_encrypt_decrypt_dict_with_empty_values(self):
        """Test encrypt/decrypt dict with empty values."""
        key = generate_encryption_key()
        data = {
            "api_key": "",
            "secret": None,
        }

        encrypted = encrypt_dict(data, key)
        decrypted = decrypt_dict(encrypted, key)

        assert decrypted["api_key"] == ""
        assert decrypted["secret"] is None

    def test_encrypt_dict_preserves_non_string_values(self):
        """Test that non-string values are preserved."""
        key = generate_encryption_key()
        data = {
            "api_key": "sk-12345",
            "port": 8080,
            "enabled": True,
            "ratio": 3.14,
        }

        encrypted = encrypt_dict(data, key)
        decrypted = decrypt_dict(encrypted, key)

        assert decrypted["api_key"] == "sk-12345"
        assert decrypted["port"] == 8080
        assert decrypted["enabled"] is True
        assert decrypted["ratio"] == 3.14


class TestGetFernetKey:
    """Tests for get_fernet_key function."""

    def test_get_fernet_key_with_valid_key(self):
        """Test getting Fernet key with valid key."""
        key = generate_encryption_key()
        from app.core.encryption import get_fernet_key

        key_bytes = get_fernet_key(key)
        assert isinstance(key_bytes, bytes)

    def test_get_fernet_key_with_invalid_key_raises_error(self):
        """Test that invalid key raises ValueError."""
        from app.core.encryption import get_fernet_key

        with pytest.raises(ValueError, match="Invalid encryption key"):
            get_fernet_key("invalid-key-not-44-chars")
