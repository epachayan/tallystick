"""The single execution path from corpus to scored outcome.

Every reporting script goes through here, so there is one place where a
protocol receives its input and one place where ground truth is read.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from ..model.dispute import build_disputes
from ..model.evidence import build_view
from ..model.types import GroundTruth, Outcome, Verdict
from ..protocols.baselines import PROTOCOLS, Protocol
from ..scoring.metrics import ScoredScenario, build_report
from ..scoring.scorer import score

DEFAULT_CORPUS = Path(__file__).resolve().parents[2] / "corpus" / "corpus.v0.9.jsonl"


def load_corpus(path=DEFAULT_CORPUS) -> list[dict]:
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


@dataclass(frozen=True)
class Run:
    scenario_id: str
    mclass: str
    protocol: str
    verdict: Verdict
    outcome: Outcome


def evaluate(protocol: Protocol, sc: dict) -> Verdict:
    """Project, build the complaint, run the protocol. Ground truth is not
    touched anywhere in this function."""
    view, oracle = build_view(sc, protocol.policy, protocol.entitlements)
    disputes = build_disputes(view)
    return protocol.fn(view, disputes, oracle)


def run_all(scenarios: Iterable[dict], protocols=None) -> Iterator[Run]:
    protocols = protocols or PROTOCOLS
    for sc in scenarios:
        truth = GroundTruth.from_scenario(sc)
        for name, proto in protocols.items():
            verdict = evaluate(proto, sc)
            yield Run(sc["scenario_id"], sc["m_class"], name, verdict,
                      score(truth, verdict))


def reports(scenarios, protocols=None):
    """protocol name -> Report."""
    protocols = protocols or PROTOCOLS
    buckets: dict[str, list[ScoredScenario]] = {n: [] for n in protocols}
    for r in run_all(scenarios, protocols):
        buckets[r.protocol].append(ScoredScenario(r.scenario_id, r.mclass, r.outcome))
    return {n: build_report(v) for n, v in buckets.items()}


def disclosure(scenarios, protocols=None):
    """protocol name -> list of disclosed byte counts."""
    protocols = protocols or PROTOCOLS
    out: dict[str, list[int]] = {n: [] for n in protocols}
    for sc in scenarios:
        for name, proto in protocols.items():
            out[name].append(evaluate(proto, sc).disclosed_bytes)
    return out
