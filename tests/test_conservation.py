"""The conservation boundary.

The single most consequential claim the project makes, so it gets tested as a
derivation rather than as an observation: the rule is stated, then checked
against every protocol and every twin pair.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.types import GroundTruth, Outcome, Party
from src.protocols.baselines import PROTOCOLS
from src.reporting.harness import evaluate, load_corpus, reports
from src.scoring.scorer import score
from src.validation.conservation import (
    classify,
    divergence_signature,
    solved_both,
    views_identical,
)

CORPUS = load_corpus()
REPS = reports(CORPUS)
ROWS = classify(CORPUS)


def by_class(m):
    return [s for s in CORPUS if s["m_class"] == m]


# ---------------------------------------------------------------------------
# the rule
# ---------------------------------------------------------------------------

def test_the_boundary_predicts_every_pair():
    """BINDS -> no unentitled mechanism solves both. ESCAPABLE -> some does."""
    for guilty, honest, verdict, _dg, _dh in ROWS:
        both = solved_both(CORPUS, REPS, guilty, honest)
        if verdict == "binds":
            assert both == [], f"{guilty}/{honest} predicted binding but {both} solved both"
        else:
            assert both, f"{guilty}/{honest} predicted escapable but nothing solved both"


def test_escapable_pairs_are_exactly_the_mistake_vs_malice_pairs():
    escapable = {(g, h) for g, h, v, *_ in ROWS if v == "escapable"}
    assert escapable == {("M6", "M15"), ("M7", "M17")}


def test_binding_pairs_are_exactly_the_loss_vs_concealment_pairs():
    binding = {(g, h) for g, h, v, *_ in ROWS if v == "binds"}
    assert binding == {("M19", "M10"), ("M20", "M21"), ("M22", "M23"),
                       ("M24", "M25"), ("M26", "M27"), ("M28", "M29"),
                       ("M30", "M31"), ("M32", "M33")}


def test_escapable_means_both_worlds_share_a_divergence_signature():
    for guilty, honest, verdict, dg, dh in ROWS:
        assert (dg == dh) == (verdict == "escapable")


def test_binding_pairs_have_an_empty_honest_signature():
    """The structural reason conservation binds: in the honest world nothing
    diverged at all, so no assertion about divergence is true in both."""
    for _guilty, honest, verdict, _dg, dh in ROWS:
        if verdict == "binds":
            assert dh == frozenset(), honest


# ---------------------------------------------------------------------------
# the mechanism of the escape
# ---------------------------------------------------------------------------

def test_the_escape_is_the_non_attributive_vocabulary():
    """On an escapable pair the protocol issues the SAME verdict for both worlds
    and it is correct in both -- because the claim is about the record, not the
    person, and both parties' accounts do diverge."""
    for guilty, honest in (("M6", "M15"), ("M7", "M17")):
        proto = PROTOCOLS["B10_composed"]
        a, b = by_class(guilty)[0], by_class(honest)[0]
        va, vb = evaluate(proto, a), evaluate(proto, b)
        assert va.key() == vb.key()
        assert va.attributes_fault is False
        assert score(GroundTruth.from_scenario(a), va) is Outcome.CORRECT_CONTRADICTION
        assert score(GroundTruth.from_scenario(b), vb) is Outcome.CORRECT_CONTRADICTION


def test_attributive_protocols_cannot_take_the_escape():
    """An attributive mechanism must name someone, and the two worlds differ in
    whether anyone is culpable. Same verdict, one of them wrong."""
    proto = PROTOCOLS["B1_bilateral_commitment"]
    a, b = by_class("M6")[0], by_class("M15")[0]
    va, vb = evaluate(proto, a), evaluate(proto, b)
    assert va.key() == vb.key()
    assert score(GroundTruth.from_scenario(a), va) is Outcome.CORRECT_BLAME
    assert score(GroundTruth.from_scenario(b), vb) is Outcome.OVER_ATTRIBUTION


def test_the_escape_does_not_generalise_to_binding_pairs():
    """The same non-attributive protocol gains nothing on a binding pair."""
    proto = PROTOCOLS["B10_composed"]
    a, b = by_class("M19")[0], by_class("M10")[0]
    va, vb = evaluate(proto, a), evaluate(proto, b)
    assert va.key() == vb.key()
    assert score(GroundTruth.from_scenario(a), va) is Outcome.MISSED
    assert score(GroundTruth.from_scenario(b), vb) is Outcome.CORRECT_ABSTAIN


# ---------------------------------------------------------------------------
# entitlements are not an escape
# ---------------------------------------------------------------------------

def test_an_entitled_protocol_is_not_a_counterexample():
    """B16c solves both sides of some binding pairs, but only because its
    custodial entitlement means the pair is not a twin for it. That is a larger
    view, not an escape from conservation."""
    proto = PROTOCOLS["B16c_custodial_attestor"]
    assert not views_identical(CORPUS, "M19", "M10", proto)
    plain = PROTOCOLS["B13_witness_messages"]
    assert views_identical(CORPUS, "M19", "M10", plain)


def test_divergence_signature_is_constant_within_a_class():
    for m in {s["m_class"] for s in CORPUS}:
        divergence_signature(CORPUS, m)   # raises if not


# ---------------------------------------------------------------------------
# the headline the boundary replaces
# ---------------------------------------------------------------------------

def test_no_class_is_unreachable_by_every_mechanism():
    """M22 was previously described as the one class nothing reaches. That was
    an artifact of looking only at the commitment-only family: full-disclosure
    protocols do solve M22 -- and fail M23 for it."""
    unreached = {m for m in REPS["B0_bearer_executor_log"].per_class
                 if all(r.per_class[m].correct != r.per_class[m].n
                        for r in REPS.values())}
    assert unreached == set()


def test_m22_and_m23_partition_the_protocol_set():
    """Every protocol solves exactly one of the pair. The partition IS the
    conservation, per protocol rather than in aggregate."""
    for name, rep in REPS.items():
        a, b = rep.per_class["M22"], rep.per_class["M23"]
        solved_a, solved_b = a.correct == a.n, b.correct == b.n
        assert solved_a != solved_b, name
