import hashlib

import pytest

from core.trust import (
    InvalidTrustValueError,
    TrustError,
    TrustIdentity,
    TrustStatus,
    TrustVerifier,
)


def test_trust_identity_accepts_valid_identity():
    identity = TrustIdentity(
        identity="ziggy-official",
        status=TrustStatus.TRUSTED,
    )

    assert identity.identity == "ziggy-official"
    assert identity.status is TrustStatus.TRUSTED


def test_trust_identity_defaults_to_unknown():
    identity = TrustIdentity("community-author")

    assert identity.status is TrustStatus.UNKNOWN


def test_trust_identity_rejects_non_string_identity():
    with pytest.raises(InvalidTrustValueError):
        TrustIdentity(123)


def test_trust_identity_rejects_empty_identity():
    with pytest.raises(InvalidTrustValueError):
        TrustIdentity("")


def test_trust_identity_requires_valid_status():
    with pytest.raises(InvalidTrustValueError):
        TrustIdentity(
            "ziggy-official",
            "TRUSTED",
        )


def test_verifier_starts_empty():
    verifier = TrustVerifier()

    assert verifier.count() == 0


def test_register_identity():
    verifier = TrustVerifier()

    identity = TrustIdentity(
        "ziggy-official",
        TrustStatus.TRUSTED,
    )

    verifier.register_identity(identity)

    assert verifier.count() == 1
    assert verifier.get_identity("ziggy-official") == identity


def test_register_identity_replaces_existing_identity():
    verifier = TrustVerifier()

    verifier.register_identity(
        TrustIdentity(
            "ziggy-official",
            TrustStatus.TRUSTED,
        )
    )

    verifier.register_identity(
        TrustIdentity(
            "ziggy-official",
            TrustStatus.REVOKED,
        )
    )

    assert verifier.count() == 1
    assert (
        verifier.get_identity("ziggy-official").status
        is TrustStatus.REVOKED
    )


def test_get_unknown_identity_returns_none():
    verifier = TrustVerifier()

    assert verifier.get_identity("unknown") is None


def test_remove_identity():
    verifier = TrustVerifier()

    verifier.register_identity(
        TrustIdentity(
            "community",
            TrustStatus.TRUSTED,
        )
    )

    verifier.remove_identity("community")

    assert verifier.count() == 0
    assert verifier.get_identity("community") is None


def test_remove_unknown_identity_raises():
    verifier = TrustVerifier()

    with pytest.raises(TrustError):
        verifier.remove_identity("unknown")


def test_trusted_identity_and_matching_hash_are_trusted():
    verifier = TrustVerifier()

    verifier.register_identity(
        TrustIdentity(
            "ziggy-official",
            TrustStatus.TRUSTED,
        )
    )

    artifact = b"ziggy module"
    expected = hashlib.sha256(artifact).hexdigest()

    result = verifier.verify_artifact(
        "ziggy-official",
        artifact,
        expected,
    )

    assert result.status is TrustStatus.TRUSTED
    assert result.integrity_valid is True
    assert result.is_valid is True


def test_unknown_identity_is_not_trusted():
    verifier = TrustVerifier()

    artifact = b"ziggy module"
    expected = hashlib.sha256(artifact).hexdigest()

    result = verifier.verify_artifact(
        "unknown",
        artifact,
        expected,
    )

    assert result.status is TrustStatus.UNKNOWN
    assert result.integrity_valid is True
    assert result.is_valid is False


def test_revoked_identity_is_not_trusted():
    verifier = TrustVerifier()

    verifier.register_identity(
        TrustIdentity(
            "revoked-author",
            TrustStatus.REVOKED,
        )
    )

    artifact = b"ziggy module"
    expected = hashlib.sha256(artifact).hexdigest()

    result = verifier.verify_artifact(
        "revoked-author",
        artifact,
        expected,
    )

    assert result.status is TrustStatus.REVOKED
    assert result.integrity_valid is True
    assert result.is_valid is False


def test_untrusted_identity_is_not_trusted():
    verifier = TrustVerifier()

    verifier.register_identity(
        TrustIdentity(
            "untrusted-author",
            TrustStatus.UNTRUSTED,
        )
    )

    artifact = b"ziggy module"
    expected = hashlib.sha256(artifact).hexdigest()

    result = verifier.verify_artifact(
        "untrusted-author",
        artifact,
        expected,
    )

    assert result.status is TrustStatus.UNTRUSTED
    assert result.integrity_valid is True
    assert result.is_valid is False


def test_invalid_identity_is_not_trusted():
    verifier = TrustVerifier()

    verifier.register_identity(
        TrustIdentity(
            "invalid-author",
            TrustStatus.INVALID,
        )
    )

    artifact = b"ziggy module"
    expected = hashlib.sha256(artifact).hexdigest()

    result = verifier.verify_artifact(
        "invalid-author",
        artifact,
        expected,
    )

    assert result.status is TrustStatus.INVALID
    assert result.integrity_valid is True
    assert result.is_valid is False


def test_modified_artifact_fails_integrity():
    verifier = TrustVerifier()

    verifier.register_identity(
        TrustIdentity(
            "ziggy-official",
            TrustStatus.TRUSTED,
        )
    )

    original = b"original module"
    modified = b"modified module"

    expected = hashlib.sha256(original).hexdigest()

    result = verifier.verify_artifact(
        "ziggy-official",
        modified,
        expected,
    )

    assert result.status is TrustStatus.INVALID
    assert result.integrity_valid is False
    assert result.is_valid is False


def test_invalid_identity_input_is_rejected():
    verifier = TrustVerifier()

    with pytest.raises(InvalidTrustValueError):
        verifier.verify_artifact(
            "",
            b"artifact",
            "hash",
        )


def test_artifact_must_be_bytes():
    verifier = TrustVerifier()

    with pytest.raises(InvalidTrustValueError):
        verifier.verify_artifact(
            "identity",
            "artifact",
            "hash",
        )


def test_expected_hash_must_be_string():
    verifier = TrustVerifier()

    with pytest.raises(InvalidTrustValueError):
        verifier.verify_artifact(
            "identity",
            b"artifact",
            123,
        )


def test_expected_hash_cannot_be_empty():
    verifier = TrustVerifier()

    with pytest.raises(InvalidTrustValueError):
        verifier.verify_artifact(
            "identity",
            b"artifact",
            "",
        )
