"""B17 duty-to-answer, and the exact-exchange result.

B13's residual is four classes where the executor asserts nothing. B17 closes
that refuge by making non-production a contradiction in its own right. The
result is the sharpest instance of conservation the corpus has produced: three
classes resolved, three honest twins broken, one-for-one, with no net change in
full-class success.

These tests pin the exchange so it cannot be lost to a later edit, and pin the
one class that moves in neither direction.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.types import GroundTruth, Outcome, Party
from src.protocols.baselines import PROTOCOLS
from src.reporting.harness import evaluate, load_corpus
from src.scoring.metrics import ScoredScenario, build_report
from src.scoring.scorer import score
from src.validation import visibility

CORPUS = load_corpus()
ONE_PER_CLASS = list({s["m_class"]: s for s in CORPUS}.values())
B13 = PROTOCOLS["B13_witness_messages"]
B17 = PROTOCOLS["B17_duty_to_answer"]

#: guilty class -> its honest twin. The duty resolves the first and breaks the
#: second, which is the whole finding.
#:
#: The last two are the principal-side mirrors (RC-H9). They are what makes the
#: exchange a claim about the STRUCTURE rather than about the executor.
EXCHANGED = (("M19", "M10"), ("M20", "M21"), ("M24", "M25"),
             ("M26", "M27"), ("M28", "M29"))


def by_class(m):
    return [s for s in CORPUS if s["m_class"] == m]


def outcomes(proto, m):
    return [score(GroundTruth.from_scenario(s), evaluate(proto, s)) for s in by_class(m)]


def report(proto):
    return build_report([
        ScoredScenario(s["scenario_id"], s["m_class"],
                       score(GroundTruth.from_scenario(s), evaluate(proto, s)))
        for s in CORPUS])


# ---------------------------------------------------------------------------
# the exchange
# ---------------------------------------------------------------------------

def test_duty_resolves_the_guilty_classes():
    """M19, M20, M24: the executor tampers or is guilty, then withholds. Under
    B13 these are missed; the duty makes the withholding itself contradictory."""
    for guilty, _honest in EXCHANGED:
        assert set(outcomes(B13, guilty)) == {Outcome.MISSED}
        assert set(outcomes(B17, guilty)) == {Outcome.CORRECT_CONTRADICTION}


def test_duty_breaks_the_honest_twins():
    """M10, M21, M25: genuine loss and a genuine attestor outage. The duty
    cannot tell them from the guilty twin, because non-production is all it
    sees. It contradicts an honest party."""
    for _guilty, honest in EXCHANGED:
        assert set(outcomes(B13, honest)) == {Outcome.CORRECT_ABSTAIN}
        assert set(outcomes(B17, honest)) == {Outcome.FALSE_CONTRADICTION}


def test_the_exchange_is_exactly_one_for_one():
    """Three gained, three lost, no net change. Conservation observed directly
    rather than argued."""
    r13, r17 = report(B13), report(B17)
    assert r13.classes_fully_solved == 26
    assert r17.classes_fully_solved == 26
    assert r13.scenario_success == r17.scenario_success

    def failing(r):
        return {m for m, c in r.per_class.items() if c.correct != c.n}

    # M30 and M33 fail for BOTH and cancel out of the exchange: the abort leg is
    # a gap neither mechanism addresses, not a trade either makes.
    assert failing(r13) == {"M19", "M20", "M22", "M24", "M26", "M28", "M30", "M33"}
    assert failing(r17) == {"M10", "M21", "M22", "M25", "M27", "M29", "M30", "M33"}
    assert len(failing(r13) - failing(r17)) == len(failing(r17) - failing(r13)) == 5


def test_the_ambiguity_changes_denomination_not_quantity():
    """B13 pays in misses, B17 pays in false contradictions. Same count."""
    r13, r17 = report(B13), report(B17)
    assert r13.miss_rate > r17.miss_rate          # duty resolves misses
    fc13 = sum(c.counts.get(Outcome.FALSE_CONTRADICTION, 0)
               for c in r13.per_class.values())
    fc17 = sum(c.counts.get(Outcome.FALSE_CONTRADICTION, 0)
               for c in r17.per_class.values())
    missed13 = sum(c.counts.get(Outcome.MISSED, 0) for c in r13.per_class.values())
    missed17 = sum(c.counts.get(Outcome.MISSED, 0) for c in r17.per_class.values())
    assert (missed13 - missed17) == (fc17 - fc13) == 125


# ---------------------------------------------------------------------------
# the class that moves in neither direction
# ---------------------------------------------------------------------------

def test_m22_is_unreachable_by_either_protocol():
    """The false key-compromise claim. The executor DOES produce its record, so
    no duty is breached; the excuse attacks the signatures rather than the
    record. An obligation to speak is the wrong instrument for it."""
    assert set(outcomes(B13, "M22")) == {Outcome.MISSED}
    assert set(outcomes(B17, "M22")) == {Outcome.MISSED}
    sc = by_class("M22")[0]
    assert sc["e_view"]["record_available"] is True
    assert sc["key_claim"]["revoked"] is True


def test_m23_the_honest_twin_of_m22_is_unharmed_by_the_duty():
    assert set(outcomes(B17, "M23")) == {Outcome.CORRECT_ABSTAIN}


# ---------------------------------------------------------------------------
# the duty attaches only where a commitment demonstrably exists
# ---------------------------------------------------------------------------

def test_no_duty_without_a_witnessed_commitment():
    """M12: no commitment was ever exchanged. There is nothing to be held to,
    so the duty must not fire."""
    assert set(outcomes(B17, "M12")) == {Outcome.CORRECT_ABSTAIN_AMB}


def test_duty_breach_is_flagged_wherever_it_fires():
    for guilty, honest in EXCHANGED:
        for m in (guilty, honest):
            for sc in by_class(m)[:3]:
                assert "duty_breach" in evaluate(B17, sc).flags


def test_b17_never_attributes_fault():
    """Non-production is a claim about the record, not about the person. It
    cannot separate a party that lost its record from one that hid it -- which
    is exactly why the honest twins break."""
    for sc in ONE_PER_CLASS:
        v = evaluate(B17, sc)
        assert v.attributes_fault is False
        assert v.blamed is Party.NONE


def test_b17_makes_no_false_ATTRIBUTION_despite_false_contradictions():
    """The distinction earns its keep here: B17 wrongs five honest classes, but
    it never names anyone. A protocol with attributive vocabulary would have
    produced 125 false accusations instead."""
    r = report(B17)
    assert r.false_attribution_rate == 0.0
    fc = sum(c.counts.get(Outcome.FALSE_CONTRADICTION, 0) for c in r.per_class.values())
    assert fc == 150      # 125 from the duty exchange, 25 on the abort leg (M33)


def test_b17_passes_the_visibility_invariant():
    assert visibility.check(B17, ONE_PER_CLASS) == []


# ---------------------------------------------------------------------------
# RC-H11: is the exchange symmetric across parties?
# ---------------------------------------------------------------------------

def test_the_duty_attaches_to_both_parties():
    """M26/M28: the PRINCIPAL tampers then withholds. The v1 duty did not fire
    here at all -- it was written against a corpus where only the executor was
    ever asked to produce anything (RC-H9)."""
    for guilty in ("M26", "M28"):
        assert set(outcomes(B13, guilty)) == {Outcome.MISSED}
        assert set(outcomes(B17, guilty)) == {Outcome.CORRECT_CONTRADICTION}
        for sc in by_class(guilty)[:3]:
            v = evaluate(B17, sc)
            assert Party.P in v.contradicted
            assert "duty_breach" in v.flags


def test_the_exchange_holds_identically_on_the_principal_side():
    """The conservation is a property of the structure, not of the executor.
    Five guilty classes resolved, five honest twins broken, on both sides of
    the relationship."""
    for guilty, honest in EXCHANGED:
        assert set(outcomes(B17, guilty)) == {Outcome.CORRECT_CONTRADICTION}
        assert set(outcomes(B17, honest)) == {Outcome.FALSE_CONTRADICTION}


def test_symmetric_withholding_classes_are_true_twins():
    """M26/M27 and M28/M29 must be evidence-identical, or they test nothing."""
    from src.model.evidence import DisclosurePolicy, build_view
    for guilty, honest in (("M26", "M27"), ("M28", "M29")):
        for a, b in zip(by_class(guilty), by_class(honest)):
            va, _ = build_view(a, DisclosurePolicy.COMMITMENT_ONLY)
            vb, _ = build_view(b, DisclosurePolicy.COMMITMENT_ONLY)
            assert va.observable_fingerprint() == vb.observable_fingerprint()


def test_withholding_is_now_modelled_for_both_parties():
    """The RC-H9 asymmetry itself, pinned so it cannot silently return."""
    p_withholds = sum(1 for s in CORPUS if not s["p_view"]["record_available"])
    e_withholds = sum(1 for s in CORPUS if not s["e_view"]["record_available"])
    assert p_withholds > 0 and e_withholds > 0
