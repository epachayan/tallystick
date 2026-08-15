"""B13 witness-carrying messages.

Two properties carry the result and both are pinned here:

  * root recomputation uses only the party's OWN assertion plus the committed
    root, so it discloses nothing the party had not already volunteered
  * disclosure is O(1) in record size, unlike every full-disclosure protocol
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.crypto.merkle import build_root
from src.model.dispute import build_disputes
from src.model.evidence import DisclosurePolicy, build_view
from src.model.types import GroundTruth, Outcome, Party
from src.protocols.baselines import PROTOCOLS, b13_witness_messages
from src.reporting.harness import evaluate, load_corpus
from src.scoring.scorer import score
from src.validation import visibility

CORPUS = load_corpus()
ONE_PER_CLASS = list({s["m_class"]: s for s in CORPUS}.values())
B13 = PROTOCOLS["B13_witness_messages"]


def _run(sc):
    return evaluate(B13, sc)


def _outcome(sc):
    return score(GroundTruth.from_scenario(sc), _run(sc))


def by_class(m):
    return [s for s in CORPUS if s["m_class"] == m]


# ---------------------------------------------------------------------------
# the mechanism
# ---------------------------------------------------------------------------

def test_root_recomputation_detects_a_narrowed_assertion():
    """M6: the principal asserts a smaller scope than it committed to. The check
    hashes what P asserted; the true scope is never read."""
    for sc in by_class("M6"):
        v = _run(sc)
        assert Party.P in v.contradicted
        assert "root_recomputation" in v.flags


def test_root_recomputation_reaches_concealed_omission():
    """M1: the executor conceals an out-of-scope action by omitting it from its
    account. No QUERY can reach this -- the complainant cannot name what it was
    never told. Recomputing the root from what E DID assert catches it anyway."""
    for sc in by_class("M1"):
        v = _run(sc)
        assert Party.E in v.contradicted
        assert "root_recomputation" in v.flags


def test_only_root_recomputation_survives_padding_on_M1():
    """The dispute-driven protocol also reaches M1, but only through the
    cardinality a plain commitment leaks. Pad the commitment and that route
    closes; recomputation still works, because its input is the executor's own
    assertion rather than the record's size."""
    b5 = PROTOCOLS["B5_dispute_driven"]
    for sc in by_class("M1")[:5]:
        # unpadded: B5 gets there, and says how
        v5 = evaluate(b5, sc)
        assert v5.blamed is Party.E and "cardinality_binding" in v5.flags

        # padded: B5 loses it, B13 keeps it
        view5, oracle5 = build_view(sc, b5.policy, b5.entitlements, pad_to=8)
        assert b5.fn(view5, build_disputes(view5), oracle5).blamed is not Party.E

        view13, oracle13 = build_view(sc, B13.policy, B13.entitlements, pad_to=8)
        v13 = b13_witness_messages(view13, build_disputes(view13), oracle13)
        assert Party.E in v13.contradicted


def test_recomputation_uses_only_the_assertion_and_the_root():
    """The check must pass on a truthful assertion and fail on any edit to it,
    with no reference to the committed set."""
    sc = by_class("M0")[0]
    view, _ = build_view(sc, DisclosurePolicy.COMMITMENT_ONLY)
    truthful = view.p.asserted_scope
    assert build_root(truthful) == view.scope_root
    assert build_root(list(truthful)[:-1]) != view.scope_root


def test_recomputation_respects_padding():
    sc = by_class("M0")[0]
    view, _ = build_view(sc, DisclosurePolicy.COMMITMENT_ONLY, pad_to=8)
    assert view.pad_to == 8
    v = b13_witness_messages(view, build_disputes(view), _oracle(sc, 8))
    assert v.contradicted == ()


def _oracle(sc, pad_to):
    return build_view(sc, DisclosurePolicy.COMMITMENT_ONLY, pad_to=pad_to)[1]


def test_a_duplicate_bearing_assertion_cannot_form_the_committed_set():
    sc = by_class("M0")[0]
    view, oracle = build_view(sc, DisclosurePolicy.COMMITMENT_ONLY)
    from src.protocols.baselines import _root_of
    dupes = list(view.p.asserted_scope) + [view.p.asserted_scope[0]]
    assert _root_of(dupes, view) == "<unformable>"


# ---------------------------------------------------------------------------
# behaviour
# ---------------------------------------------------------------------------

def test_b13_never_attributes_fault():
    """A root mismatch is a claim about the record; it cannot separate
    misremembering from lying."""
    for sc in ONE_PER_CLASS:
        v = _run(sc)
        assert v.attributes_fault is False
        assert v.blamed is Party.NONE


def test_b13_names_no_party_ever():
    """Non-attributive, so it cannot make a false ACCUSATION anywhere."""
    bad = {Outcome.FALSE_ACCUSATION, Outcome.OVER_ATTRIBUTION,
           Outcome.UNSUPPORTED_BLAME}
    assert not [s["scenario_id"] for s in CORPUS if _outcome(s) in bad]


def test_b13_false_contradictions_are_confined_to_the_abort_leg():
    """RC-H7. Before the abort classes existed B13 made no false contradiction
    at all. It now makes them on exactly one class: M33, where the delivery
    acknowledgement was lost in transit and B13 cannot tell that from M32, the
    deliberate abort. It gained M32 and paid with M33."""
    wrong = {s["m_class"] for s in CORPUS
             if _outcome(s) is Outcome.FALSE_CONTRADICTION}
    assert wrong == {"M33"}


def test_b13_cannot_reach_an_executor_abort():
    """The fairness asymmetry in the witness chain, made visible. After step 2
    the executor holds evidence of origin and the principal holds nothing about
    the execution, so an executor that acts and then aborts leaves no commitment
    to check against. This is what a fair-exchange protocol exists to close."""
    assert set(_outcome(s) for s in by_class("M30")) == {Outcome.MISSED}


def test_b13_handles_the_twin_pairs_identically():
    """M15/M6 and M17/M7: identical evidence must produce identical verdicts."""
    for mistake, malicious in (("M15", "M6"), ("M17", "M7")):
        a = [_run(s).key() for s in by_class(mistake)]
        b = [_run(s).key() for s in by_class(malicious)]
        assert a == b


def test_b13_residual_is_exactly_the_withheld_record_classes():
    """The four classes B13 cannot reach are the ones where the executor asserts
    nothing and withholds contents. Recomputation needs an assertion to check."""
    failing = set()
    for sc in CORPUS:
        if _outcome(sc) not in (Outcome.CORRECT_BLAME, Outcome.CORRECT_CONTRADICTION,
                                Outcome.CORRECT_ABSTAIN, Outcome.CORRECT_ABSTAIN_AMB):
            failing.add(sc["m_class"])
    assert failing == {"M19", "M20", "M22", "M24", "M26", "M28", "M30", "M33"}
    # In every one, SOME party is silent about the artifact in dispute. Which
    # party differs -- M19/M20/M22/M24 are executor-side, M26/M28 principal-side
    # -- and that is exactly the point: the residual tracks silence, not role.
    # In every one, some party is silent about the artifact in dispute -- either
    # because it withheld a record, or (M30/M33) because an abort meant the
    # commitment was never delivered to the party who would check it.
    for m in failing:
        sc = by_class(m)[0]
        e_silent = sc["e_view"]["asserted_actions"] is None
        p_silent = sc["p_view"]["asserted_scope"] is None
        chain_broken = not (sc["chain"]["exec_receipt_sent"]
                            and sc["chain"]["delivery_ack_sent"])
        assert e_silent or p_silent or chain_broken, m


def test_b13_catches_the_corrupt_adjudicator():
    """C_witness: a published verdict must recompute from the published
    witnesses."""
    for sc in by_class("M14"):
        v = _run(sc)
        assert Party.J in v.contradicted
        assert "transcript_mismatch" in v.flags


def test_b13_refutes_a_baseless_complaint():
    for sc in by_class("M13"):
        v = _run(sc)
        assert Party.P in v.contradicted
        assert "baseless_complaint" in v.flags


def test_b13_abstains_when_no_commitment_exists():
    for sc in by_class("M12"):
        assert _outcome(sc) is Outcome.CORRECT_ABSTAIN_AMB


# ---------------------------------------------------------------------------
# cost
# ---------------------------------------------------------------------------

def test_b13_disclosure_is_flat_in_record_size():
    """The comparison that matters: full-disclosure cost grows with the record,
    B13's does not."""
    from src import generator

    sizes, b13, full = [2, 32], {}, {}
    for n in sizes:
        generator.SCOPE_SIZE = n
        scs = list(generator.generate(20260808, 3))
        b13[n] = sum(evaluate(B13, s).disclosed_bytes for s in scs) / len(scs)
        full[n] = sum(evaluate(PROTOCOLS["B10_composed"], s).disclosed_bytes
                      for s in scs) / len(scs)
    generator.SCOPE_SIZE = 3
    assert b13[32] / b13[2] < 1.1, "B13 disclosure should be near-constant"
    assert full[32] / full[2] > 2.0, "full disclosure should grow with the record"


def test_b13_passes_the_visibility_invariant():
    assert visibility.check(B13, ONE_PER_CLASS) == []
