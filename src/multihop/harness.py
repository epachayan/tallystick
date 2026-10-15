"""Single execution path for the three-party corpus: project, adjudicate, score.

Reuses the two-party metrics module unchanged, so "full-class success" and
"false attribution" mean exactly what they mean in results/canonical.txt.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..model.types import Outcome
from ..scoring.metrics import ScoredScenario, build_report
from .evidence import build_view
from .generator import load_corpus
from .model import Truth3, Verdict3, localised, score3
from .protocols import PROTOCOLS3, Protocol3


def evaluate(proto: Protocol3, sc: dict) -> Verdict3:
    view, oracle = build_view(proto.spec, sc, proto.disclosure)
    return proto.fn(view, oracle)


@dataclass(frozen=True)
class Run3:
    scenario_id: str
    h_class: str
    protocol: str
    verdict: Verdict3
    outcome: Outcome
    localised: bool


def run_all(scenarios, protocols=None):
    protocols = protocols or PROTOCOLS3
    for sc in scenarios:
        truth = Truth3.from_scenario(sc)
        for name, proto in protocols.items():
            v = evaluate(proto, sc)
            yield Run3(sc["scenario_id"], sc["h_class"], name, v,
                       score3(truth, v), localised(truth, v))


def reports(scenarios, protocols=None):
    """protocol -> (metrics Report, {class: localised count}, [disclosed bytes])."""
    protocols = protocols or PROTOCOLS3
    buckets = {n: [] for n in protocols}
    loc = {n: defaultdict(int) for n in protocols}
    disc = {n: [] for n in protocols}
    for r in run_all(scenarios, protocols):
        buckets[r.protocol].append(ScoredScenario(r.scenario_id, r.h_class, r.outcome))
        loc[r.protocol][r.h_class] += int(r.localised)
        disc[r.protocol].append(r.verdict.disclosed_bytes)
    return {n: (build_report(buckets[n]), dict(loc[n]), disc[n]) for n in protocols}


def load():
    return load_corpus()
