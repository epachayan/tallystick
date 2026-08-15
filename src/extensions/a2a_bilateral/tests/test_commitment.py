"""Tests for the standalone bilateral commitment primitive."""

from __future__ import annotations

import hashlib
import hmac

from src.extensions.a2a_bilateral import (
    check_assertion,
    commit,
    verify_signature,
)


class HmacFixture:
    """Symmetric test fixture, not a real third-party-verifiable signer."""

    def __init__(self, key: bytes):
        self.key = key

    def sign(self, payload: bytes) -> str:
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()

    def verify(self, payload: bytes, signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)


def test_commitment_is_set_deterministic_and_cardinality_bound():
    signer = HmacFixture(b"principal-test-key")
    first = commit(["read:logs", "deploy:staging", "read:logs"],
                   signer=signer, signer_id="principal-1")
    second = commit(["deploy:staging", "read:logs"],
                    signer=signer, signer_id="principal-1")

    assert first.cardinality == 2
    assert first.root == second.root
    assert first.signature == second.signature


def test_matching_assertion_is_accepted():
    original = ["deploy:staging", "read:logs"]
    commitment = commit(original, signer=HmacFixture(b"key"), signer_id="executor-1")

    assert check_assertion(list(reversed(original)), commitment)


def test_added_removed_and_altered_items_are_rejected():
    commitment = commit(
        ["deploy:staging", "read:logs"],
        signer=HmacFixture(b"key"),
        signer_id="executor-1",
    )

    assert not check_assertion(["deploy:staging", "read:logs", "write:logs"], commitment)
    assert not check_assertion(["deploy:staging"], commitment)
    assert not check_assertion(["deploy:production", "read:logs"], commitment)


def test_strict_subset_omission_is_rejected():
    commitment = commit(
        ["deploy:staging", "read:logs"],
        signer=HmacFixture(b"key"),
        signer_id="executor-1",
    )

    assert not check_assertion(["deploy:staging"], commitment)


def test_signature_requires_the_matching_verifier_key():
    matching = HmacFixture(b"matching-key")
    different = HmacFixture(b"different-key")
    commitment = commit(["read:logs"], signer=matching, signer_id="principal-1")

    assert verify_signature(commitment, verifier=matching)
    assert not verify_signature(commitment, verifier=different)
