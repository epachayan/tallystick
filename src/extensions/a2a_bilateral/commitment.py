"""Build, sign, and check commitments to a party's asserted set.

This module reuses src/crypto/merkle.py: the repository's sorted-leaf,
domain-separated, cardinality-bound Merkle set implementation. It never
inspects a true set when checking a later assertion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

from ...crypto.merkle import build_root


@runtime_checkable
class Signer(Protocol):
    def sign(self, payload: bytes) -> str: ...


@runtime_checkable
class Verifier(Protocol):
    def verify(self, payload: bytes, signature: str) -> bool: ...


@dataclass(frozen=True)
class Commitment:
    root: str
    cardinality: int
    signature: str
    signer_id: str


def _as_set(items: Sequence[str]) -> list[str]:
    """Normalize a set-shaped API while keeping the Merkle implementation strict."""
    return sorted(set(items))


def commit(items: Sequence[str], *, signer: Signer, signer_id: str) -> Commitment:
    """Commit the asserting party to a set of operation/action strings."""
    normalized = _as_set(items)
    root = build_root(normalized)
    signature = signer.sign(root.encode("utf-8"))
    return Commitment(
        root=root,
        cardinality=len(normalized),
        signature=signature,
        signer_id=signer_id,
    )


def check_assertion(asserted_items: Sequence[str], commitment: Commitment) -> bool:
    """Return whether a current assertion matches an earlier commitment.

    Only the current assertion and commitment are used. A false result proves
    contradiction with the commitment; it does not establish why the party's
    account differs, and silence leaves no assertion to check.
    """
    return build_root(_as_set(asserted_items)) == commitment.root


def verify_signature(commitment: Commitment, *, verifier: Verifier) -> bool:
    """Verify the caller-supplied signature over the commitment root."""
    return verifier.verify(commitment.root.encode("utf-8"), commitment.signature)
