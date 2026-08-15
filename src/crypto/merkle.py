"""Sorted-leaf Merkle commitment with real proof verification (P0-4).

Replaces the v0.9 module, which built proof objects and measured them but never
verified one. Baselines could therefore "prove" things by consulting the true
set. Here the verifier takes (root, value, proof) and nothing else.

Soundness-relevant choices, each of which the old module got wrong or omitted:

* Domain separation: leaf 0x00, internal 0x01, root 0x02. Without it a leaf
  hash can be passed off as an internal node.

* The leaf COUNT is bound into the root:  root = H(0x02 ‖ n ‖ apex).
  The old root was just the apex. An unauthenticated n makes every boundary and
  adjacency claim forgeable, which is what non-membership rests on.

  Consequence worth noticing: n is then unavoidably public to anyone who
  verifies any proof. A commitment to a set leaks its cardinality. That is a
  disclosure fact, not a bug, and it is charged as one -- see CARDINALITY_NOTE.

* Odd levels PROMOTE the last node. The old module duplicated it
  (`level + [level[-1]]`), which admits the classic tree-shape forgery: a
  duplicated final leaf lets a 2k+1-leaf tree be presented as a 2k+2-leaf one.

* Sibling orientation is DERIVED from (index, n), never carried. The old module
  shipped `dirs` in the proof, so a prover could assert its own orientation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"
ROOT_PREFIX = b"\x02"

CARDINALITY_NOTE = (
    "A cardinality-binding root publishes |set| to any proof verifier. This is "
    "unavoidable for sound non-membership and is accounted as disclosed."
)


class MerkleError(ValueError):
    pass


def _h(*parts: bytes) -> str:
    d = hashlib.sha256()
    for p in parts:
        d.update(p)
    return d.hexdigest()


def leaf_hash(value: str) -> str:
    return _h(LEAF_PREFIX, value.encode("utf-8"))


def node_hash(left: str, right: str) -> str:
    return _h(NODE_PREFIX, bytes.fromhex(left), bytes.fromhex(right))


def root_hash(n: int, apex: str) -> str:
    return _h(ROOT_PREFIX, n.to_bytes(8, "big"), bytes.fromhex(apex))


@dataclass(frozen=True)
class MembershipProof:
    value: str
    index: int
    n: int
    siblings: tuple[str, ...]


@dataclass(frozen=True)
class NonMembershipProof:
    value: str
    left: MembershipProof | None
    right: MembershipProof | None
    n: int


def _levels(leaves: Sequence[str]) -> list[list[str]]:
    level = [leaf_hash(v) for v in leaves]
    levels = [level]
    while len(level) > 1:
        nxt: list[str] = []
        i = 0
        while i < len(level):
            if i + 1 < len(level):
                nxt.append(node_hash(level[i], level[i + 1]))
                i += 2
            else:
                nxt.append(level[i])       # promote, do not duplicate
                i += 1
        level = nxt
        levels.append(level)
    return levels


def normalize(values: Sequence[str]) -> list[str]:
    vals = list(values)
    if len(set(vals)) != len(vals):
        raise MerkleError("duplicate values: sorted-leaf commitment requires a set")
    return sorted(vals)


class MerkleSet:
    """Commitment to a set of strings. The PROVER side: holds the contents.

    A protocol must never be handed one of these. It gets the root and a
    ProofOracle, which answers named queries only.
    """

    def __init__(self, items: Sequence[str]):
        self.items = normalize(items)
        self.n = len(self.items)
        if not self.items:
            self.root = root_hash(0, _h(ROOT_PREFIX, b"empty"))
            self.levels: list[list[str]] = []
            return
        self.levels = _levels(self.items)
        self.root = root_hash(self.n, self.levels[-1][0])

    def _siblings(self, idx: int) -> tuple[str, ...]:
        sibs: list[str] = []
        j = idx
        for level in self.levels[:-1]:
            if j % 2 == 0:
                if j + 1 < len(level):
                    sibs.append(level[j + 1])
            else:
                sibs.append(level[j - 1])
            j //= 2
        return tuple(sibs)

    def prove_membership(self, value: str) -> MembershipProof:
        if value not in self.items:
            raise MerkleError(f"cannot prove membership of absent value {value!r}")
        idx = self.items.index(value)
        return MembershipProof(value, idx, self.n, self._siblings(idx))

    def prove_non_membership(self, value: str) -> NonMembershipProof:
        if value in self.items:
            raise MerkleError(f"cannot prove non-membership of present value {value!r}")
        below = [v for v in self.items if v < value]
        above = [v for v in self.items if v > value]
        left = self.prove_membership(below[-1]) if below else None
        right = self.prove_membership(above[0]) if above else None
        return NonMembershipProof(value, left, right, self.n)


def build_root(values: Sequence[str]) -> str:
    return MerkleSet(values).root


# ---------------------------------------------------------------------------
# Verification. Consults nothing but (root, value, proof).
# ---------------------------------------------------------------------------

def _max_siblings(n: int) -> int:
    count, size = 0, n
    while size > 1:
        count += 1
        size = (size + 1) // 2
    return count


def verify_membership(root: str, value: str, proof: object) -> bool:
    if not isinstance(proof, MembershipProof) or not isinstance(root, str) or not root:
        return False
    n, idx = proof.n, proof.index
    if not isinstance(n, int) or not isinstance(idx, int) or isinstance(idx, bool):
        return False
    if n <= 0 or idx < 0 or idx >= n:
        return False
    if proof.value != value:
        return False
    if not isinstance(proof.siblings, tuple) or len(proof.siblings) > _max_siblings(n):
        return False
    for s in proof.siblings:
        if not isinstance(s, str) or len(s) != 64:
            return False
        try:
            bytes.fromhex(s)
        except ValueError:
            return False

    cur = leaf_hash(value)
    j, size, k = idx, n, 0
    while size > 1:
        if j % 2 == 0 and j + 1 == size:
            pass                                    # promoted: consumes no sibling
        else:
            if k >= len(proof.siblings):
                return False                        # missing sibling
            sib = proof.siblings[k]
            k += 1
            cur = node_hash(cur, sib) if j % 2 == 0 else node_hash(sib, cur)
        j //= 2
        size = (size + 1) // 2
    if k != len(proof.siblings):
        return False                                # trailing junk
    return root_hash(n, cur) == root


def verify_non_membership(root: str, value: str, proof: object) -> bool:
    if not isinstance(proof, NonMembershipProof) or proof.value != value:
        return False
    n = proof.n
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        return False

    if n == 0:
        return proof.left is None and proof.right is None and build_root([]) == root

    left, right = proof.left, proof.right
    if left is None and right is None:
        return False

    if left is not None:
        if left.n != n or not verify_membership(root, left.value, left):
            return False
        if not left.value < value:
            return False
    if right is not None:
        if right.n != n or not verify_membership(root, right.value, right):
            return False
        if not value < right.value:
            return False

    if left is None:
        return right is not None and right.index == 0
    if right is None:
        return left.index == n - 1
    return right.index == left.index + 1


# ---------------------------------------------------------------------------
# Wire accounting. One encoder for both sides of any crossover comparison.
# ---------------------------------------------------------------------------

HASH_BYTES = 32
INDEX_BYTES = 4
COUNT_BYTES = 4


def encoded_size(proof: MembershipProof | NonMembershipProof) -> int:
    """Compact binary encoding: raw 32-byte digests, fixed-width integers, the
    value as UTF-8. Orientation costs nothing because it is derived, which is
    one fewer field than the v0.9 encoding carried."""
    if isinstance(proof, MembershipProof):
        return (len(proof.value.encode()) + INDEX_BYTES + COUNT_BYTES
                + HASH_BYTES * len(proof.siblings))
    total = len(proof.value.encode()) + COUNT_BYTES
    for side in (proof.left, proof.right):
        if side is not None:
            total += encoded_size(side)
    return total


# ---------------------------------------------------------------------------
# Functional wrappers. Convenient for tests and for callers that hold the set.
# A protocol must NOT use these -- it gets a ProofOracle instead.
# ---------------------------------------------------------------------------

def prove_membership(values: Sequence[str], value: str) -> MembershipProof:
    return MerkleSet(values).prove_membership(value)


def prove_non_membership(values: Sequence[str], value: str) -> NonMembershipProof:
    return MerkleSet(values).prove_non_membership(value)
