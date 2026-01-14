"""
Encryption Service for sensitive data.

Uses Fernet symmetric encryption for API keys and other sensitive configuration.
The encryption key should be stored in environment variable ENCRYPTION_KEY.
"""

import base64
import os

from cryptography.fernet import Fernet, InvalidToken

from research_agent.shared.utils.logger import logger


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.

    Uses Fernet (AES 128-bit in CBC mode with HMAC-SHA256).
    """

    def __init__(self, encryption_key: str | None = None):
        """
        Initialize encryption service.

        Args:
            encryption_key: Base64-encoded 32-byte key.
                           If not provided, reads from ENCRYPTION_KEY env var.
                           If env var is not set, generates a new key (not recommended for production).
        """
        self._key = self._resolve_key(encryption_key)
        self._fernet = Fernet(self._key)

    def _resolve_key(self, provided_key: str | None) -> bytes:
        """Resolve the encryption key from various sources."""
        # Priority: provided_key > env var > generate new
        if provided_key:
            return provided_key.encode()

        env_key = os.environ.get("ENCRYPTION_KEY")
        if env_key:
            return env_key.encode()

        # Generate a new key if none provided (development only)
        logger.warning(
            "[Encryption] No ENCRYPTION_KEY found. Generating temporary key. "
            "This is NOT suitable for production - encrypted data will be lost on restart!"
        )
        return Fernet.generate_key()

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        encrypted_bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails (invalid token or corrupted data)
        """
        if not ciphertext:
            return ""

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken as e:
            logger.error(f"[Encryption] Decryption failed: {e}")
            raise ValueError("Failed to decrypt data. The encryption key may have changed.") from e

    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value appears to be encrypted (Fernet format).

        Args:
            value: String to check

        Returns:
            True if the value looks like a Fernet token
        """
        if not value:
            return False

        # Fernet tokens are base64-encoded and start with "gAAAAA"
        try:
            decoded = base64.urlsafe_b64decode(value.encode())
            return len(decoded) > 32 and decoded[0:1] == b"\x80"
        except Exception:
            return False

    def mask_value(self, value: str, visible_chars: int = 4) -> str:
        """
        Mask a sensitive value for display.

        Args:
            value: Value to mask
            visible_chars: Number of characters to show at the end

        Returns:
            Masked string like "****abcd"
        """
        if not value:
            return ""

        if len(value) <= visible_chars:
            return "*" * len(value)

        return "*" * (len(value) - visible_chars) + value[-visible_chars:]

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded 32-byte key
        """
        return Fernet.generate_key().decode("utf-8")


# Singleton instance
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Get singleton EncryptionService instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
