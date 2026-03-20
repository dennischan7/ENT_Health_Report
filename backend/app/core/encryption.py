"""
Encryption utilities using Fernet symmetric encryption.

Provides functions for encrypting and decrypting sensitive data like API keys.
"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        str: Base64-encoded Fernet key suitable for storage in environment variables.

    Example:
        >>> key = generate_encryption_key()
        >>> # Store this key securely in your environment
        >>> # ENCRYPTION_KEY=your-generated-key
    """
    return Fernet.generate_key().decode("utf-8")


def get_fernet_key(key: Optional[str] = None) -> bytes:
    """
    Get a valid Fernet key from the provided key or settings.

    Args:
        key: Optional key string. If not provided, uses settings.ENCRYPTION_KEY.

    Returns:
        bytes: Valid Fernet key as bytes.

    Raises:
        ValueError: If the key is not a valid Fernet key.
    """
    key_str = key or settings.ENCRYPTION_KEY

    # Ensure key is properly padded for base64
    # Fernet keys are 32-byte base64-encoded strings
    try:
        # Try to use the key directly
        key_bytes = key_str.encode("utf-8")
        # Validate by creating a Fernet instance
        Fernet(key_bytes)
        return key_bytes
    except Exception as e:
        raise ValueError(
            f"Invalid encryption key. Generate a valid key using generate_encryption_key(). "
            f"Error: {e}"
        )


def encrypt(plaintext: str, key: Optional[str] = None) -> str:
    """
    Encrypt a plaintext string using Fernet symmetric encryption.

    Args:
        plaintext: The string to encrypt.
        key: Optional encryption key. If not provided, uses settings.ENCRYPTION_KEY.

    Returns:
        str: Base64-encoded encrypted string.

    Raises:
        ValueError: If the key is invalid.

    Example:
        >>> encrypted = encrypt("my-api-key")
        >>> # encrypted = "gAAAAABl..."
    """
    if not plaintext:
        return ""

    key_bytes = get_fernet_key(key)
    f = Fernet(key_bytes)
    encrypted_bytes = f.encrypt(plaintext.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt(ciphertext: str, key: Optional[str] = None) -> str:
    """
    Decrypt a ciphertext string using Fernet symmetric encryption.

    Args:
        ciphertext: The encrypted string to decrypt.
        key: Optional encryption key. If not provided, uses settings.ENCRYPTION_KEY.

    Returns:
        str: Decrypted plaintext string.

    Raises:
        ValueError: If the key is invalid or decryption fails.

    Example:
        >>> decrypted = decrypt(encrypted_string)
        >>> # decrypted = "my-api-key"
    """
    if not ciphertext:
        return ""

    key_bytes = get_fernet_key(key)
    f = Fernet(key_bytes)

    try:
        decrypted_bytes = f.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        raise ValueError(
            "Decryption failed. The ciphertext may be corrupted or the key may be incorrect."
        )


def encrypt_dict(data: dict, key: Optional[str] = None) -> dict:
    """
    Encrypt all string values in a dictionary.

    Args:
        data: Dictionary with string values to encrypt.
        key: Optional encryption key.

    Returns:
        dict: Dictionary with encrypted values.
    """
    return {k: encrypt(v, key) if isinstance(v, str) and v else v for k, v in data.items()}


def decrypt_dict(data: dict, key: Optional[str] = None) -> dict:
    """
    Decrypt all string values in a dictionary.

    Args:
        data: Dictionary with encrypted string values.
        key: Optional encryption key.

    Returns:
        dict: Dictionary with decrypted values.
    """
    return {k: decrypt(v, key) if isinstance(v, str) and v else v for k, v in data.items()}
