from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.types import Outcome
from src.scoring.metrics import ScoredScenario, build_report, pareto_point


def make(mclass: str, outcomes: list[Outcome]) -> list[ScoredScenario]:
    return [ScoredScenario(f"{mclass}-{i}", mclass, o) for i, o in enumerate(outcomes)]


def test_full_class_success_requires_every_instance():
    scored = make("M20", [Outcome.CORRECT_BLAME] * 24 + [Outcome.MISSED])
    r = build_report(scored)
    assert r.per_class["M20"].partially_solved
    assert not r.per_class["M20"].fully_solved
    assert r.classes_fully_solved == 0
    assert r.per_class["M20"].success_rate == 24 / 25


def test_correct_abstention_counts_as_success():
    """regression.py's old aggregate omitted these."""
    scored = make("M3", [Outcome.CORRECT_ABSTAIN, Outcome.CORRECT_ABSTAIN_AMB])
    r = build_report(scored)
    assert r.scenario_success == 1.0
    assert r.per_class["M3"].fully_solved


def test_false_attribution_includes_unsupported_blame():
    scored = make("M7", [Outcome.FALSE_ACCUSATION, Outcome.UNSUPPORTED_BLAME, Outcome.CORRECT_BLAME])
    r = build_report(scored)
    assert r.per_class["M7"].false_attribution == 2
    assert abs(r.false_attribution_rate - 2 / 3) < 1e-9


def test_worst_class_is_reported_not_averaged_away():
    scored = make("M1", [Outcome.CORRECT_BLAME] * 10) + make(
        "M2", [Outcome.CORRECT_BLAME] * 4 + [Outcome.MISSED] * 6
    )
    r = build_report(scored)
    assert r.scenario_success == 0.7
    assert r.worst_class_success == 0.4
    assert r.worst_class == "M2"


def test_pareto_uses_full_class_success():
    scored = make("M1", [Outcome.CORRECT_BLAME] * 5) + make(
        "M2", [Outcome.CORRECT_BLAME] + [Outcome.MISSED] * 4
    )
    p = pareto_point(build_report(scored), disclosure=100.0, cost=1.0)
    assert p["full_class_success"] == 0.5  # not 1.0, which any-instance would give
    assert p["worst_class_success"] == 0.2


def test_summary_and_table_render():
    scored = make("M1", [Outcome.CORRECT_BLAME, Outcome.MISSED])
    r = build_report(scored)
    assert "classes fully solved" in r.summary()
    assert "M1" in r.table()
