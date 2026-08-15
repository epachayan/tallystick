"""Structural visibility invariant (step 3, closes P0-1).

For every hidden field: clone a scenario, change the hidden value, hold the
projected EvidenceView fixed, and require the protocol's verdict not to move.
A protocol that reads hidden state fails here by construction, which is what
the v0.9 leak audit could not do -- it looked for suspicious reads rather than
making them impossible.

The mutators deliberately try to flip each hidden field to something a leaking
protocol would behave differently on: the guilty party, the party states, the
adjudicability flag, `adjudicator.colluding`, and `key_claim.genuine`.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Callable, Iterable

from ..model.dispute import build_disputes
from ..model.evidence import build_view
from ..protocols.baselines import PROTOCOLS, Protocol


def _set(sc: dict, dotted: str, value) -> dict:
    out = copy.deepcopy(sc)
    node = out
    parts = dotted.split(".")
    for p in parts[:-1]:
        node = node.setdefault(p, {})
    node[parts[-1]] = value
    return out


#: field -> callable(scenario) -> mutated scenario. Each must leave the
#: EvidenceView byte-identical; if it does not, the harness raises rather than
#: quietly passing.
MUTATORS: dict[str, Callable[[dict], dict]] = {
    "ground_truth.dishonest_party": lambda sc: _set(
        sc, "ground_truth.dishonest_party",
        "E" if sc["ground_truth"].get("dishonest_party") != "E" else "P"),
    "ground_truth.p_state": lambda sc: _set(
        sc, "ground_truth.p_state",
        "dishonest" if sc["ground_truth"].get("p_state") != "dishonest" else "honest"),
    "ground_truth.e_state": lambda sc: _set(
        sc, "ground_truth.e_state",
        "dishonest" if sc["ground_truth"].get("e_state") != "dishonest" else "honest"),
    "ground_truth.adjudicable": lambda sc: _set(
        sc, "ground_truth.adjudicable", not sc["ground_truth"].get("adjudicable", True)),
    "ground_truth.claim": lambda sc: _set(sc, "ground_truth.claim", "mutated"),
    "ground_truth.actual": lambda sc: _set(sc, "ground_truth.actual", "mutated"),
    "adjudicator.colluding": lambda sc: _set(
        sc, "adjudicator.colluding", not sc.get("adjudicator", {}).get("colluding", False)),
    "adjudicator.favours": lambda sc: _set(sc, "adjudicator.favours", "E"),
    "key_claim.genuine": lambda sc: _set(
        sc, "key_claim.genuine", not sc.get("key_claim", {}).get("genuine", False)),
    "m_class": lambda sc: _set(sc, "m_class", "MX"),
    "mutation_family": lambda sc: _set(sc, "mutation_family", "mutated"),
}


class VisibilityLeak(AssertionError):
    pass


@dataclass(frozen=True)
class Leak:
    protocol: str
    scenario_id: str
    field: str
    before: tuple
    after: tuple

    def __str__(self) -> str:
        return (f"{self.protocol} leaked {self.field!r} on {self.scenario_id}: "
                f"{self.before} -> {self.after}")


def check(protocol: Protocol, scenarios: Iterable[dict],
          mutators=None) -> list[Leak]:
    mutators = mutators or MUTATORS
    leaks: list[Leak] = []
    for sc in scenarios:
        view_a, oracle_a = build_view(sc, protocol.policy, protocol.entitlements)
        verdict_a = protocol.fn(view_a, build_disputes(view_a), oracle_a)
        for field, mutate in mutators.items():
            mutated = mutate(sc)
            view_b, oracle_b = build_view(mutated, protocol.policy, protocol.entitlements)
            if view_b.fingerprint() != view_a.fingerprint():
                raise VisibilityLeak(
                    f"mutator for {field!r} changed the EvidenceView on "
                    f"{sc['scenario_id']}; it must hold visible evidence fixed")
            verdict_b = protocol.fn(view_b, build_disputes(view_b), oracle_b)
            if verdict_a.key() != verdict_b.key():
                leaks.append(Leak(protocol.name, sc["scenario_id"], field,
                                  verdict_a.key(), verdict_b.key()))
    return leaks


def check_all(scenarios, protocols=None) -> list[Leak]:
    protocols = protocols or PROTOCOLS
    out: list[Leak] = []
    for proto in protocols.values():
        out.extend(check(proto, scenarios))
    return out


def main():
    import json
    from ..reporting.harness import load_corpus

    scs = load_corpus()
    # one instance per class is enough to cover every structure
    sample = {}
    for s in scs:
        sample.setdefault(s["m_class"], s)
    leaks = check_all(list(sample.values()))
    if leaks:
        for l in leaks:
            print(l)
        raise SystemExit(f"VISIBILITY: {len(leaks)} leak(s)")
    print(f"visibility: {len(PROTOCOLS)} protocols x {len(sample)} classes "
          f"x {len(MUTATORS)} hidden fields -- no leaks")


if __name__ == "__main__":
    main()
