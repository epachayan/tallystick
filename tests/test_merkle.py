"""Merkle verifier tests, including every negative case listed in the findings:

wrong root, modified value, modified sibling hash, wrong left/right orientation,
missing sibling, fake bracket, non-adjacent bracket, invalid minimum boundary,
invalid maximum boundary, duplicate values, odd-size tree / padding edge cases,
malformed proof structure.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.crypto.merkle import (
    MembershipProof,
    MerkleError,
    NonMembershipProof,
    build_root,
    encoded_size,
    leaf_hash,
    prove_membership,
    prove_non_membership,
    verify_membership,
    verify_non_membership,
)

SCOPE = ["read:a", "read:b", "write:c", "write:d", "delete:e"]  # 5 -> odd tree


# --------------------------------------------------------------------------
# Positive
# --------------------------------------------------------------------------

@pytest.mark.parametrize("size", range(1, 18))
def test_membership_roundtrip_all_sizes(size):
    values = [f"op:{i:03d}" for i in range(size)]
    root = build_root(values)
    for v in values:
        assert verify_membership(root, v, prove_membership(values, v))


@pytest.mark.parametrize("size", range(1, 18))
def test_non_membership_roundtrip_all_sizes(size):
    values = [f"op:{i * 2:03d}" for i in range(size)]  # gaps at every odd number
    root = build_root(values)
    for probe in ["op:-01", "op:001", "op:999"]:
        assert verify_non_membership(root, probe, prove_non_membership(values, probe))


def test_empty_set_non_membership():
    root = build_root([])
    assert verify_non_membership(root, "anything", prove_non_membership([], "anything"))


def test_single_leaf_boundaries():
    values = ["m"]
    root = build_root(values)
    assert verify_non_membership(root, "a", prove_non_membership(values, "a"))
    assert verify_non_membership(root, "z", prove_non_membership(values, "z"))
    assert verify_membership(root, "m", prove_membership(values, "m"))


# --------------------------------------------------------------------------
# Negative: membership
# --------------------------------------------------------------------------

def test_wrong_root():
    root = build_root(SCOPE)
    other = build_root(SCOPE + ["read:z"])
    p = prove_membership(SCOPE, "write:c")
    assert verify_membership(root, "write:c", p)
    assert not verify_membership(other, "write:c", p)


def test_modified_value():
    root = build_root(SCOPE)
    p = prove_membership(SCOPE, "write:c")
    tampered = dataclasses.replace(p, value="write:X")
    assert not verify_membership(root, "write:X", tampered)
    # and the verifier must also reject a value/proof mismatch
    assert not verify_membership(root, "write:X", p)


def test_modified_sibling_hash():
    root = build_root(SCOPE)
    p = prove_membership(SCOPE, "write:c")
    sibs = list(p.siblings)
    sibs[0] = leaf_hash("forged")
    assert not verify_membership(root, "write:c", dataclasses.replace(p, siblings=tuple(sibs)))


def test_wrong_orientation():
    """Orientation is derived from (index, n), so flipping the claimed index to
    invert left/right must fail the root check."""
    values = [f"op:{i}" for i in range(8)]
    root = build_root(values)
    p = prove_membership(values, "op:2")
    flipped = dataclasses.replace(p, index=3)
    assert not verify_membership(root, "op:2", flipped)


def test_missing_sibling():
    root = build_root(SCOPE)
    p = prove_membership(SCOPE, "write:c")
    assert not verify_membership(root, "write:c", dataclasses.replace(p, siblings=p.siblings[:-1]))


def test_extra_sibling():
    root = build_root(SCOPE)
    p = prove_membership(SCOPE, "write:c")
    padded = dataclasses.replace(p, siblings=p.siblings + (leaf_hash("junk"),))
    assert not verify_membership(root, "write:c", padded)


def test_index_out_of_range():
    root = build_root(SCOPE)
    p = prove_membership(SCOPE, "write:c")
    assert not verify_membership(root, "write:c", dataclasses.replace(p, index=99))
    assert not verify_membership(root, "write:c", dataclasses.replace(p, index=-1))


def test_lied_leaf_count():
    root = build_root(SCOPE)
    p = prove_membership(SCOPE, "write:c")
    assert not verify_membership(root, "write:c", dataclasses.replace(p, n=len(SCOPE) + 1))


def test_malformed_proof_structure():
    root = build_root(SCOPE)
    for junk in (None, {}, "proof", 42, [], object()):
        assert not verify_membership(root, "write:c", junk)
        assert not verify_non_membership(root, "nope", junk)


def test_malformed_sibling_encoding():
    root = build_root(SCOPE)
    p = prove_membership(SCOPE, "write:c")
    for bad in ("zz", "not-hex" * 9, ""):
        assert not verify_membership(root, "write:c", dataclasses.replace(p, siblings=(bad,)))


def test_absent_value_cannot_be_proved_member():
    root = build_root(SCOPE)
    with pytest.raises(MerkleError):
        prove_membership(SCOPE, "delete:zzz")
    # forging one from a neighbour's path also fails
    p = prove_membership(SCOPE, "delete:e")
    assert not verify_membership(root, "delete:zzz", dataclasses.replace(p, value="delete:zzz"))


# --------------------------------------------------------------------------
# Negative: non-membership
# --------------------------------------------------------------------------

def test_fake_bracket():
    """Brackets that are not real leaves must fail."""
    root = build_root(SCOPE)
    real = prove_non_membership(SCOPE, "read:aa")
    fake_left = MembershipProof(value="read:aZ", index=0, n=len(SCOPE), siblings=real.left.siblings)
    assert not verify_non_membership(
        root, "read:aa", dataclasses.replace(real, left=fake_left)
    )


def test_non_adjacent_bracket():
    """A prover must not hide a leaf between the brackets."""
    values = ["a", "b", "c", "d"]
    root = build_root(values)
    left = prove_membership(values, "a")
    right = prove_membership(values, "c")  # skips "b"
    proof = NonMembershipProof(value="bb", left=left, right=right, n=len(values))
    assert not verify_non_membership(root, "bb", proof)


def test_bracket_ordering_violation():
    values = ["a", "c"]
    root = build_root(values)
    # claim "b" absent but present a left bracket that is above it
    left = prove_membership(values, "c")
    proof = NonMembershipProof(value="b", left=left, right=None, n=len(values))
    assert not verify_non_membership(root, "b", proof)


def test_invalid_minimum_boundary():
    """No left bracket is only legal when the right bracket is leaf 0."""
    values = ["a", "b", "c", "d"]
    root = build_root(values)
    right = prove_membership(values, "c")  # index 2, not the minimum
    proof = NonMembershipProof(value="ba", left=None, right=right, n=len(values))
    assert not verify_non_membership(root, "ba", proof)


def test_invalid_maximum_boundary():
    values = ["a", "b", "c", "d"]
    root = build_root(values)
    left = prove_membership(values, "b")  # index 1, not the maximum
    proof = NonMembershipProof(value="zz", left=left, right=None, n=len(values))
    assert not verify_non_membership(root, "zz", proof)


def test_no_brackets_at_all_is_rejected():
    root = build_root(SCOPE)
    proof = NonMembershipProof(value="anything", left=None, right=None, n=len(SCOPE))
    assert not verify_non_membership(root, "anything", proof)


def test_present_value_cannot_be_proved_absent():
    root = build_root(SCOPE)
    with pytest.raises(MerkleError):
        prove_non_membership(SCOPE, "write:c")
    # nor by bracketing around it with real proofs
    left = prove_membership(SCOPE, "read:b")
    right = prove_membership(SCOPE, "write:d")
    forged = NonMembershipProof(value="write:c", left=left, right=right, n=len(SCOPE))
    assert not verify_non_membership(root, "write:c", forged)


def test_mismatched_n_between_brackets():
    root = build_root(SCOPE)
    p = prove_non_membership(SCOPE, "read:aa")
    bad_left = dataclasses.replace(p.left, n=len(SCOPE) + 1)
    assert not verify_non_membership(root, "read:aa", dataclasses.replace(p, left=bad_left))


# --------------------------------------------------------------------------
# Construction hygiene
# --------------------------------------------------------------------------

def test_duplicate_values_rejected():
    with pytest.raises(MerkleError):
        build_root(["a", "b", "a"])


def test_odd_size_promotion_not_duplication():
    """Three leaves must not collide with four where the last is duplicated."""
    three = build_root(["a", "b", "c"])
    four = build_root(["a", "b", "c", "d"])
    assert three != four
    # and the bound leaf count distinguishes any two different-sized sets
    assert build_root(["a"]) != build_root(["a", "b"])


def test_domain_separation():
    """A leaf hash must not be usable as an internal node."""
    from src.crypto.merkle import node_hash

    assert leaf_hash("a") != node_hash(leaf_hash("a"), leaf_hash("a"))


def test_encoded_size_is_monotonic_in_proof_length():
    small = build_root([f"op:{i}" for i in range(2)])
    big_values = [f"op:{i:03d}" for i in range(64)]
    p_small = prove_membership([f"op:{i}" for i in range(2)], "op:0")
    p_big = prove_membership(big_values, "op:000")
    assert encoded_size(p_big) > encoded_size(p_small)
    assert small  # tree built


def test_non_membership_proof_is_larger_than_membership():
    """Relevant to E3: interior non-membership carries two paths."""
    values = [f"op:{i * 2:03d}" for i in range(32)]
    m = prove_membership(values, "op:010")
    nm = prove_non_membership(values, "op:011")
    assert encoded_size(nm) > encoded_size(m)
