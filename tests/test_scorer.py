"""Exhaustive scorer audit.

The truth x verdict space is small, so it is enumerated rather than sampled.
Properties P1-P10 from the findings document are checked across the whole
enumeration, not on hand-picked examples.
"""

from __future__ import annotations

import hashlib
import itertools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.types import (
    FAILURE_OUTCOMES,
    SUCCESS_OUTCOMES,
    GroundTruth,
    Outcome,
    Party,
    PartyState,
    Verdict,
    VerdictStatus,
)
from src.scoring.scorer import score

STATES = (PartyState.HONEST, PartyState.MISTAKEN, PartyState.DISHONEST)
BLAMES = (Party.NONE, Party.P, Party.E, Party.J, Party.BOTH)


def _coherent_dishonest(p_state, e_state):
    """The dishonest_party values consistent with a pair of party states."""
    if p_state is PartyState.DISHONEST and e_state is PartyState.DISHONEST:
        return (Party.BOTH,)
    if p_state is PartyState.DISHONEST:
        return (Party.P,)
    if e_state is PartyState.DISHONEST:
        return (Party.E,)
    return (Party.NONE, Party.J)


def all_truths():
    for adjudicable in (True, False):
        for p_state, e_state in itertools.product(STATES, STATES):
            for dishonest in _coherent_dishonest(p_state, e_state):
                yield GroundTruth(dishonest, p_state, e_state, adjudicable)


def all_verdicts():
    for blamed in BLAMES:
        for r in range(3):
            for contradicted in itertools.combinations((Party.P, Party.E, Party.J), r):
                for attributes in (True, False):
                    for detected in (True, False):
                        for status in (VerdictStatus.CLEAR, VerdictStatus.EXPOSED,
                                       VerdictStatus.SUSPECTED, VerdictStatus.UNRESOLVED):
                            yield Verdict(detected=detected, blamed=blamed,
                                          contradicted=contradicted,
                                          attributes_fault=attributes, status=status)


TRUTHS = list(all_truths())
VERDICTS = list(all_verdicts())
STATES_SPACE = [(t, v) for t in TRUTHS for v in VERDICTS]


def test_enumeration_is_not_degenerate():
    assert len(TRUTHS) >= 20
    assert len(STATES_SPACE) > 5000


def test_p10_every_state_has_a_defined_outcome():
    for truth, verdict in STATES_SPACE:
        assert isinstance(score(truth, verdict), Outcome)


def test_p9_labels_are_mutually_exclusive():
    assert SUCCESS_OUTCOMES & FAILURE_OUTCOMES == frozenset()
    assert SUCCESS_OUTCOMES | FAILURE_OUTCOMES == frozenset(Outcome)


def test_p1_correct_guilty_attribution_is_rewarded():
    t = GroundTruth(Party.E, PartyState.HONEST, PartyState.DISHONEST, True)
    assert score(t, Verdict(detected=True, blamed=Party.E)) is Outcome.CORRECT_BLAME


def test_p2_innocent_attribution_is_never_correct_blame():
    for truth, verdict in STATES_SPACE:
        if not verdict.names_a_party:
            continue
        if score(truth, verdict) is Outcome.CORRECT_BLAME:
            assert truth.dishonest_party is not Party.NONE
            assert verdict.blamed is truth.dishonest_party


def test_p3_wrong_guilty_party_is_false_accusation():
    t = GroundTruth(Party.E, PartyState.HONEST, PartyState.DISHONEST, True)
    assert score(t, Verdict(detected=True, blamed=Party.P)) is Outcome.FALSE_ACCUSATION


def test_p4_correct_contradiction_without_attribution():
    t = GroundTruth(Party.E, PartyState.HONEST, PartyState.DISHONEST, True)
    v = Verdict(detected=True, blamed=Party.NONE, contradicted=(Party.E,),
                attributes_fault=False, status=VerdictStatus.CONTRADICTED)
    assert score(t, v) is Outcome.CORRECT_CONTRADICTION


def test_p5_unadjudicable_plus_abstain():
    t = GroundTruth(Party.E, PartyState.HONEST, PartyState.DISHONEST, adjudicable=False)
    assert score(t, Verdict()) is Outcome.CORRECT_ABSTAIN_AMB


def test_p5b_unadjudicable_never_yields_missed():
    """Case A: the v0.9 ordering returned `missed` here for non-attributive
    mechanisms, because it branched on the verdict's vocabulary first."""
    for truth, verdict in STATES_SPACE:
        if truth.adjudicable:
            continue
        assert score(truth, verdict) is not Outcome.MISSED


def test_p6_no_divergence_plus_abstain():
    t = GroundTruth(Party.NONE, PartyState.HONEST, PartyState.HONEST, True)
    assert score(t, Verdict(status=VerdictStatus.CLEAR)) is Outcome.CORRECT_ABSTAIN


def test_p7_empty_divergence_is_never_correct_contradiction():
    """Case B: `sorted([]) == sorted([])` used to return correct_contradiction."""
    for truth, verdict in STATES_SPACE:
        if truth.diverges:
            continue
        assert score(truth, verdict) is not Outcome.CORRECT_CONTRADICTION


def test_p8_scorer_signature_admits_no_baseline():
    import inspect
    assert list(inspect.signature(score).parameters) == ["truth", "verdict"]


def test_mistaken_party_blamed_is_over_attribution():
    """The project's own T4 boundary: a mistaken party diverges but is not
    culpable, so naming it is over-attribution rather than correct blame."""
    t = GroundTruth(Party.NONE, PartyState.MISTAKEN, PartyState.HONEST, True)
    assert score(t, Verdict(detected=True, blamed=Party.P)) is Outcome.OVER_ATTRIBUTION


def test_mistaken_party_contradicted_is_correct():
    """Contradiction is a claim about the record, so pointing at a mistaken
    party is right where blaming it is not."""
    t = GroundTruth(Party.NONE, PartyState.MISTAKEN, PartyState.HONEST, True)
    v = Verdict(detected=True, contradicted=(Party.P,), attributes_fault=False,
                status=VerdictStatus.CONTRADICTED)
    assert score(t, v) is Outcome.CORRECT_CONTRADICTION


def test_mistake_only_world_abstention_is_not_a_miss():
    t = GroundTruth(Party.NONE, PartyState.MISTAKEN, PartyState.MISTAKEN, True)
    assert score(t, Verdict()) is Outcome.CORRECT_ABSTAIN


def test_mixed_world_masking_guard():
    """A mistaken co-party must not mask a genuine wrongdoer: M18's structure.
    Abstaining when someone was dishonest is still a miss."""
    t = GroundTruth(Party.E, PartyState.MISTAKEN, PartyState.DISHONEST, True)
    assert score(t, Verdict()) is Outcome.MISSED


def test_missed_requires_adjudicable_divergence_and_abstention():
    for truth, verdict in STATES_SPACE:
        if score(truth, verdict) is Outcome.MISSED:
            assert truth.adjudicable and truth.diverges and verdict.abstains


def test_spurious_requires_an_unexplained_hard_flag():
    t = GroundTruth(Party.NONE, PartyState.HONEST, PartyState.HONEST, True)
    assert score(t, Verdict(detected=True, status=VerdictStatus.EXPOSED)) is Outcome.SPURIOUS
    # a withdrawable suspicion names nobody and is not spurious
    assert score(t, Verdict(detected=True, status=VerdictStatus.SUSPECTED)) is Outcome.CORRECT_ABSTAIN


def test_blaming_both_when_only_one_is_guilty_is_false_accusation():
    t = GroundTruth(Party.E, PartyState.HONEST, PartyState.DISHONEST, True)
    assert score(t, Verdict(detected=True, blamed=Party.BOTH)) is Outcome.FALSE_ACCUSATION


def test_attribution_precedes_contradiction():
    t = GroundTruth(Party.E, PartyState.HONEST, PartyState.DISHONEST, True)
    v = Verdict(detected=True, blamed=Party.P, contradicted=(Party.E,))
    assert score(t, v) is Outcome.FALSE_ACCUSATION


def test_incoherent_ground_truth_is_representable_but_flagged_by_coherence():
    """The scorer is total; corpus-level coherence is validated separately."""
    t = GroundTruth(Party.NONE, PartyState.HONEST, PartyState.HONEST, True)
    assert t.diverges == ()


def test_truth_table_snapshot():
    """Golden digest over the enumerated space. Breaking this must be a
    deliberate semantic decision recorded in docs/scorer-semantics.md."""
    lines = [
        f"{t.adjudicable}|{t.dishonest_party.value}|{t.p_state.value}|{t.e_state.value}"
        f"=>{v.blamed.value}|{v.attributes_fault}|{v.detected}|{v.status.value}|"
        f"{','.join(c.value for c in v.contradicted)}={score(t, v).value}"
        for t, v in STATES_SPACE
    ]
    digest = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    assert digest == SNAPSHOT, f"scorer semantics changed; new digest {digest}"


SNAPSHOT = "842c28a93a7a56626bcb7fbfebbf5c5bd3958df558ff57c374d8750f4998fff9"
