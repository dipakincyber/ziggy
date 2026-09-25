"""
Ziggy Core Cryptography API.

This module provides foundational cryptographic primitives for Ziggy.

The initial implementation deliberately uses established primitives
available through Python's standard library:

- SHA-256 hashing
- HMAC-SHA-256 authentication
- cryptographically secure random bytes

Encryption, asymmetric signatures, and persistent key management are
left to later Core layers.
"""

import hashlib
import hmac
import secrets


class CryptoError(RuntimeError):
    """Base error for cryptographic operations."""


class InvalidCryptoInputError(CryptoError):
    """Raised when cryptographic input is invalid."""


class CryptoService:
    """Foundational cryptographic service."""

    HASH_ALGORITHM = "sha256"
    HMAC_ALGORITHM = "hmac-sha256"

    @staticmethod
    def hash(data: bytes) -> str:
        """
        Return the SHA-256 hexadecimal digest of the supplied data.
        """

        if not isinstance(data, bytes):
            raise InvalidCryptoInputError(
                "Hash input must be bytes."
            )

        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hmac(key: bytes, data: bytes) -> str:
        """
        Return an HMAC-SHA-256 hexadecimal digest.
        """

        if not isinstance(key, bytes):
            raise InvalidCryptoInputError(
                "HMAC key must be bytes."
            )

        if not key:
            raise InvalidCryptoInputError(
                "HMAC key cannot be empty."
            )

        if not isinstance(data, bytes):
            raise InvalidCryptoInputError(
                "HMAC input must be bytes."
            )

        return hmac.new(
            key,
            data,
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def verify_hmac(
        key: bytes,
        data: bytes,
        expected: str,
    ) -> bool:
        """
        Verify an HMAC-SHA-256 hexadecimal digest.

        Comparison uses a constant-time comparison operation.
        """

        if not isinstance(expected, str):
            raise InvalidCryptoInputError(
                "Expected HMAC must be a string."
            )

        actual = CryptoService.hmac(key, data)

        return hmac.compare_digest(actual, expected)

    @staticmethod
    def random_bytes(length: int = 32) -> bytes:
        """
        Generate cryptographically secure random bytes.
        """

        if not isinstance(length, int):
            raise InvalidCryptoInputError(
                "Random byte length must be an integer."
            )

        if length <= 0:
            raise InvalidCryptoInputError(
                "Random byte length must be greater than zero."
            )

        return secrets.token_bytes(length)
