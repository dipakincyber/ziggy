import hashlib

import pytest

from core.crypto import (
    CryptoService,
    InvalidCryptoInputError,
)


def test_sha256_hash_matches_standard_library():
    data = b"ziggy"

    expected = hashlib.sha256(data).hexdigest()

    assert CryptoService.hash(data) == expected


def test_hash_returns_hexadecimal_string():
    result = CryptoService.hash(b"ziggy")

    assert isinstance(result, str)
    assert len(result) == 64


def test_hash_is_deterministic():
    data = b"same input"

    assert CryptoService.hash(data) == CryptoService.hash(data)


def test_different_inputs_produce_different_hashes():
    first = CryptoService.hash(b"first")
    second = CryptoService.hash(b"second")

    assert first != second


def test_hash_requires_bytes():
    with pytest.raises(InvalidCryptoInputError):
        CryptoService.hash("ziggy")


def test_hmac_matches_standard_library():
    key = b"secret-key"
    data = b"ziggy"

    expected = __import__("hmac").new(
        key,
        data,
        hashlib.sha256,
    ).hexdigest()

    assert CryptoService.hmac(key, data) == expected


def test_hmac_is_deterministic():
    key = b"secret-key"
    data = b"ziggy"

    first = CryptoService.hmac(key, data)
    second = CryptoService.hmac(key, data)

    assert first == second


def test_hmac_changes_when_data_changes():
    key = b"secret-key"

    first = CryptoService.hmac(key, b"first")
    second = CryptoService.hmac(key, b"second")

    assert first != second


def test_hmac_changes_when_key_changes():
    data = b"ziggy"

    first = CryptoService.hmac(b"key-one", data)
    second = CryptoService.hmac(b"key-two", data)

    assert first != second


def test_hmac_requires_bytes_key():
    with pytest.raises(InvalidCryptoInputError):
        CryptoService.hmac("secret", b"data")


def test_hmac_rejects_empty_key():
    with pytest.raises(InvalidCryptoInputError):
        CryptoService.hmac(b"", b"data")


def test_hmac_requires_bytes_data():
    with pytest.raises(InvalidCryptoInputError):
        CryptoService.hmac(b"secret", "data")


def test_verify_hmac_accepts_valid_digest():
    key = b"secret-key"
    data = b"ziggy"

    digest = CryptoService.hmac(key, data)

    assert CryptoService.verify_hmac(
        key,
        data,
        digest,
    )


def test_verify_hmac_rejects_modified_data():
    key = b"secret-key"
    digest = CryptoService.hmac(key, b"original")

    assert not CryptoService.verify_hmac(
        key,
        b"modified",
        digest,
    )


def test_verify_hmac_rejects_modified_digest():
    key = b"secret-key"
    data = b"ziggy"

    digest = CryptoService.hmac(key, data)
    modified = digest[:-1] + ("0" if digest[-1] != "0" else "1")

    assert not CryptoService.verify_hmac(
        key,
        data,
        modified,
    )


def test_verify_hmac_requires_string_digest():
    with pytest.raises(InvalidCryptoInputError):
        CryptoService.verify_hmac(
            b"secret-key",
            b"ziggy",
            b"not-a-string",
        )


def test_random_bytes_returns_requested_length():
    result = CryptoService.random_bytes(32)

    assert isinstance(result, bytes)
    assert len(result) == 32


def test_random_bytes_different_calls_are_not_identical():
    first = CryptoService.random_bytes(32)
    second = CryptoService.random_bytes(32)

    assert first != second


def test_random_bytes_rejects_non_integer_length():
    with pytest.raises(InvalidCryptoInputError):
        CryptoService.random_bytes("32")


def test_random_bytes_rejects_zero_length():
    with pytest.raises(InvalidCryptoInputError):
        CryptoService.random_bytes(0)


def test_random_bytes_rejects_negative_length():
    with pytest.raises(InvalidCryptoInputError):
        CryptoService.random_bytes(-1)
