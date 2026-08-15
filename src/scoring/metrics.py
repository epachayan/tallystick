"""The one metrics module (step 5).

run.py, sweep.py, regression.py and experiments.py must all import from here.
Nothing else is allowed to define its own notion of "correct".

The headline distinction this module enforces:

    scenario success   -- fraction of individual scenarios handled
    full-class success -- fraction of classes where EVERY instance succeeded

For adversarial security claims the second is the real number, because the
adversary picks the input. 24/25 does not solve a class.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from ..model.types import (
    FALSE_ATTRIBUTION_OUTCOMES,
    SUCCESS_OUTCOMES,
    Outcome,
)


@dataclass(frozen=True)
class ScoredScenario:
    scenario_id: str
    mclass: str
    outcome: Outcome


@dataclass(frozen=True)
class ClassReport:
    mclass: str
    n: int
    counts: Mapping[Outcome, int]

    @property
    def correct(self) -> int:
        return sum(self.counts.get(o, 0) for o in SUCCESS_OUTCOMES)

    @property
    def success_rate(self) -> float:
        return self.correct / self.n if self.n else 0.0

    @property
    def false_attribution(self) -> int:
        return sum(self.counts.get(o, 0) for o in FALSE_ATTRIBUTION_OUTCOMES)

    @property
    def false_attribution_rate(self) -> float:
        return self.false_attribution / self.n if self.n else 0.0

    @property
    def missed(self) -> int:
        return self.counts.get(Outcome.MISSED, 0)

    @property
    def miss_rate(self) -> float:
        return self.missed / self.n if self.n else 0.0

    @property
    def ambiguous_abstention(self) -> int:
        return self.counts.get(Outcome.CORRECT_ABSTAIN_AMB, 0)

    @property
    def ambiguous_abstention_rate(self) -> float:
        return self.ambiguous_abstention / self.n if self.n else 0.0

    @property
    def fully_solved(self) -> bool:
        """Every instance succeeded. This is the adversarial criterion."""
        return self.n > 0 and self.correct == self.n

    @property
    def partially_solved(self) -> bool:
        """At least one instance succeeded. Reported for continuity with the old
        Pareto metric, never used as the security claim."""
        return self.correct > 0

    def distribution_line(self) -> str:
        parts = [f"{o.value}:{c}" for o, c in sorted(self.counts.items(), key=lambda kv: kv[0].value) if c]
        return f"{self.mclass}  n={self.n}  " + "  ".join(parts)


@dataclass(frozen=True)
class Report:
    per_class: Mapping[str, ClassReport]
    n_scenarios: int

    @property
    def scenario_success(self) -> float:
        correct = sum(c.correct for c in self.per_class.values())
        return correct / self.n_scenarios if self.n_scenarios else 0.0

    @property
    def classes_total(self) -> int:
        return len(self.per_class)

    @property
    def classes_fully_solved(self) -> int:
        return sum(1 for c in self.per_class.values() if c.fully_solved)

    @property
    def classes_partially_solved(self) -> int:
        return sum(1 for c in self.per_class.values() if c.partially_solved)

    @property
    def worst_class_success(self) -> float:
        if not self.per_class:
            return 0.0
        return min(c.success_rate for c in self.per_class.values())

    @property
    def worst_class(self) -> str:
        return min(self.per_class.values(), key=lambda c: c.success_rate).mclass

    @property
    def false_attribution_rate(self) -> float:
        fa = sum(c.false_attribution for c in self.per_class.values())
        return fa / self.n_scenarios if self.n_scenarios else 0.0

    @property
    def miss_rate(self) -> float:
        m = sum(c.missed for c in self.per_class.values())
        return m / self.n_scenarios if self.n_scenarios else 0.0

    def summary(self) -> str:
        return (
            f"scenario success:          {self.scenario_success:.1%}\n"
            f"classes partially solved:  {self.classes_partially_solved} / {self.classes_total}\n"
            f"classes fully solved:      {self.classes_fully_solved} / {self.classes_total}\n"
            f"worst class success:       {self.worst_class_success:.0%} ({self.worst_class})\n"
            f"false attribution rate:    {self.false_attribution_rate:.1%}\n"
            f"miss rate:                 {self.miss_rate:.1%}"
        )

    def table(self) -> str:
        header = f"{'class':<8}{'n':>5}{'correct':>10}{'false-attr':>12}{'missed':>9}{'amb-abst':>10}"
        rows = [header, "-" * len(header)]
        for mclass in sorted(self.per_class, key=_class_sort_key):
            c = self.per_class[mclass]
            rows.append(
                f"{c.mclass:<8}{c.n:>5}{c.correct:>10}{c.false_attribution:>12}"
                f"{c.missed:>9}{c.ambiguous_abstention:>10}"
            )
        return "\n".join(rows)


def _class_sort_key(name: str):
    digits = "".join(ch for ch in name if ch.isdigit())
    return (0, int(digits)) if digits else (1, name)


def build_report(scored: Iterable[ScoredScenario]) -> Report:
    buckets: dict[str, dict[Outcome, int]] = defaultdict(lambda: defaultdict(int))
    totals: dict[str, int] = defaultdict(int)
    n = 0
    for s in scored:
        buckets[s.mclass][s.outcome] += 1
        totals[s.mclass] += 1
        n += 1
    per_class = {
        mclass: ClassReport(mclass=mclass, n=totals[mclass], counts=dict(counts))
        for mclass, counts in buckets.items()
    }
    return Report(per_class=per_class, n_scenarios=n)


def pareto_point(report: Report, disclosure: float, cost: float) -> dict[str, float]:
    """Pareto coordinates for E8. Uses full-class success, not any-instance
    success, which was the metric bug flagged in the findings."""
    return {
        "full_class_success": report.classes_fully_solved / report.classes_total
        if report.classes_total
        else 0.0,
        "worst_class_success": report.worst_class_success,
        "false_attribution_rate": report.false_attribution_rate,
        "disclosure": disclosure,
        "cost": cost,
    }
