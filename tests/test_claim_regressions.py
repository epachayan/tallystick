"""Headline-claim regressions.

These tests pin the exact populations and denominators quoted in the article.
They exist because F01 was once correct on the subset it measured while the
subset itself was wrong. The population is therefore derived from corpus ground
truth first, and the protocol scores are checked only after that derivation.
"""

from __future__ import annotations

from src.generator import (
    PRINCIPAL_DISHONEST,
    PRINCIPAL_LIAR,
    PRINCIPAL_LIAR_BOTH,
    PRINCIPAL_LIAR_NON_ASSERTIONAL,
)
from src.model.types import Outcome
from src.reporting.harness import load_corpus, reports
from src.reporting.run import corpus_context_line

CORPUS = load_corpus()
REPS = reports(CORPUS)


def _ordered(xs):
    return sorted(xs, key=lambda m: int(m[1:]))


def _n(classes):
    return sum(1 for s in CORPUS if s["m_class"] in classes)


def _correct(protocol, classes):
    return sum(REPS[protocol].per_class[m].correct for m in classes)


def _correct_blame(protocol, classes):
    return sum(
        REPS[protocol].per_class[m].counts.get(Outcome.CORRECT_BLAME, 0)
        for m in classes
    )


def test_principal_dishonesty_population_is_derived_and_complete():
    """No hand-maintained F01 subset may silently omit a new principal-side class."""
    derived = {
        s["m_class"]
        for s in CORPUS
        if s["ground_truth"]["dishonest_party"] in ("P", "both")
    }
    assert PRINCIPAL_DISHONEST == derived
    assert PRINCIPAL_DISHONEST == (
        PRINCIPAL_LIAR | PRINCIPAL_LIAR_NON_ASSERTIONAL | PRINCIPAL_LIAR_BOTH
    )
    assert not (PRINCIPAL_LIAR & PRINCIPAL_LIAR_NON_ASSERTIONAL)
    assert not (PRINCIPAL_LIAR & PRINCIPAL_LIAR_BOTH)
    assert not (PRINCIPAL_LIAR_NON_ASSERTIONAL & PRINCIPAL_LIAR_BOTH)


def test_non_assertional_population_includes_abort_after_delivery():
    """RC-H7 added M32 after the original F01 scope audit; keep it in scope."""
    assert _ordered(PRINCIPAL_LIAR_NON_ASSERTIONAL) == ["M13", "M26", "M28", "M32"]
    assert _n(PRINCIPAL_LIAR_NON_ASSERTIONAL) == 100


def test_f01_assertional_result_is_exactly_zero_vs_one_hundred():
    """Four classes x 25 instances: B0 cannot defend; B1 can on all 100."""
    assert _ordered(PRINCIPAL_LIAR) == ["M5", "M6", "M7", "M9"]
    assert _n(PRINCIPAL_LIAR) == 100
    assert _correct_blame("B0_bearer_executor_log", PRINCIPAL_LIAR) == 0
    assert _correct_blame("B1_bilateral_commitment", PRINCIPAL_LIAR) == 100


def test_f01_non_assertional_result_pins_the_actual_limit():
    """Commitments alone remain no better than B0 once there is no assertion to contradict."""
    classes = PRINCIPAL_LIAR_NON_ASSERTIONAL
    assert _correct("B0_bearer_executor_log", classes) == 0
    assert _correct("B1_bilateral_commitment", classes) == 0
    assert _correct("B13_witness_messages", classes) == 50
    assert _correct("B17_duty_to_answer", classes) == 100


def test_f01_denominators_are_not_assumed_to_be_25_per_class():
    """The article may quote 100 today, but tests derive N from the corpus itself."""
    counts = {
        m: sum(1 for s in CORPUS if s["m_class"] == m)
        for m in PRINCIPAL_LIAR | PRINCIPAL_LIAR_NON_ASSERTIONAL
    }
    assert set(counts.values()) == {25}
    assert sum(counts[m] for m in PRINCIPAL_LIAR) == 100
    assert sum(counts[m] for m in PRINCIPAL_LIAR_NON_ASSERTIONAL) == 100


def test_reporting_corpus_context_is_derived_not_hard_coded():
    """RC-H17: generated narrative must track corpus growth, not retain old 26/650 literals."""
    counts = {
        m: sum(1 for s in CORPUS if s["m_class"] == m)
        for m in {s["m_class"] for s in CORPUS}
    }
    assert len(set(counts.values())) == 1
    n_each = next(iter(counts.values()))
    line = corpus_context_line(CORPUS)
    assert line == (
        f"{len(counts)} adversarial structures instantiated {n_each} times each -- "
        f"NOT {len(CORPUS)} independent empirical incidents."
    )
    assert "26 adversarial structures" not in line
    assert "650 independent" not in line
