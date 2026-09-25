"""
Ziggy Core Trust & Verification API.

This module provides the foundational trust model for Ziggy modules.

The initial implementation represents trusted identities and verifies
artifact integrity using SHA-256.

Asymmetric release-signature verification is deliberately left to a
later layer using an established cryptographic implementation.
"""

from dataclasses import dataclass
from enum import Enum


class TrustError(RuntimeError):
    """Base error for trust operations."""


class InvalidTrustValueError(TrustError):
    """Raised when a trust value is invalid."""


class TrustStatus(str, Enum):
    """Current trust state of an identity or artifact."""

    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


@dataclass(frozen=True)
class TrustIdentity:
    """
    Identity associated with a module publisher or signer.
    """

    identity: str
    status: TrustStatus = TrustStatus.UNKNOWN

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str):
            raise InvalidTrustValueError(
                "Trust identity must be a string."
            )

        if not self.identity.strip():
            raise InvalidTrustValueError(
                "Trust identity cannot be empty."
            )

        if not isinstance(self.status, TrustStatus):
            raise InvalidTrustValueError(
                "Trust status must be a TrustStatus."
            )


@dataclass(frozen=True)
class VerificationResult:
    """
    Result of verifying an artifact against expected metadata.
    """

    status: TrustStatus
    integrity_valid: bool
    reasons: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        """Return whether the verification result is valid."""

        return (
            self.status is TrustStatus.TRUSTED
            and self.integrity_valid
        )


class TrustVerifier:
    """
    In-memory trust and integrity verifier.

    This implementation verifies SHA-256 artifact hashes and maintains
    an explicit trusted-identity registry.
    """

    def __init__(self) -> None:
        self._identities: dict[str, TrustIdentity] = {}

    def register_identity(
        self,
        identity: TrustIdentity,
    ) -> None:
        """Register or replace a trust identity."""

        if not isinstance(identity, TrustIdentity):
            raise TypeError(
                "Identity must be a TrustIdentity."
            )

        self._identities[identity.identity] = identity

    def remove_identity(self, identity: str) -> None:
        """Remove a registered identity."""

        if identity not in self._identities:
            raise TrustError(
                "Trust identity is not registered."
            )

        del self._identities[identity]

    def get_identity(
        self,
        identity: str,
    ) -> TrustIdentity | None:
        """Return a registered identity or None."""

        return self._identities.get(identity)

    def count(self) -> int:
        """Return the number of registered identities."""

        return len(self._identities)

    def verify_artifact(
        self,
        identity: str,
        artifact: bytes,
        expected_sha256: str,
    ) -> VerificationResult:
        """
        Verify artifact integrity and the registered identity status.

        A trusted identity plus a matching SHA-256 hash produces TRUSTED.

        A revoked, untrusted, unknown, or invalid identity cannot produce
        a trusted result even when the artifact hash matches.
        """

        if not isinstance(identity, str):
            raise InvalidTrustValueError(
                "Identity must be a string."
            )

        if not identity.strip():
            raise InvalidTrustValueError(
                "Identity cannot be empty."
            )

        if not isinstance(artifact, bytes):
            raise InvalidTrustValueError(
                "Artifact must be bytes."
            )

        if not isinstance(expected_sha256, str):
            raise InvalidTrustValueError(
                "Expected SHA-256 must be a string."
            )

        if not expected_sha256.strip():
            raise InvalidTrustValueError(
                "Expected SHA-256 cannot be empty."
            )

        import hashlib

        actual_sha256 = hashlib.sha256(artifact).hexdigest()
        integrity_valid = actual_sha256 == expected_sha256

        registered = self._identities.get(identity)

        if registered is None:
            return VerificationResult(
                status=TrustStatus.UNKNOWN,
                integrity_valid=integrity_valid,
                reasons=("Identity is not registered.",),
            )

        if registered.status is TrustStatus.REVOKED:
            return VerificationResult(
                status=TrustStatus.REVOKED,
                integrity_valid=integrity_valid,
                reasons=("Identity has been revoked.",),
            )

        if registered.status is TrustStatus.UNTRUSTED:
            return VerificationResult(
                status=TrustStatus.UNTRUSTED,
                integrity_valid=integrity_valid,
                reasons=("Identity is explicitly untrusted.",),
            )

        if registered.status is TrustStatus.INVALID:
            return VerificationResult(
                status=TrustStatus.INVALID,
                integrity_valid=integrity_valid,
                reasons=("Identity is marked invalid.",),
            )

        if not integrity_valid:
            return VerificationResult(
                status=TrustStatus.INVALID,
                integrity_valid=False,
                reasons=("Artifact SHA-256 does not match.",),
            )

        if registered.status is TrustStatus.TRUSTED:
            return VerificationResult(
                status=TrustStatus.TRUSTED,
                integrity_valid=True,
                reasons=("Trusted identity and artifact integrity verified.",),
            )

        return VerificationResult(
            status=TrustStatus.UNKNOWN,
            integrity_valid=integrity_valid,
            reasons=("Identity trust status is unknown.",),
        )
