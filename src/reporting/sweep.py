"""Scale sweep.

Two questions, one run:

1. How does disclosure grow with record size, and where does selective
   disclosure actually pay? The v0.9 sweep answered this with a three-label
   accuracy tally of its own; it now uses the canonical metrics module.

2. What does commitment padding cost? A sound sorted-leaf commitment publishes
   |set| to every verifier, which separates two twin pairs the project treats as
   indistinguishable (M10/M19, M21/M20). Padding to a fixed cardinality restores
   the indistinguishability. This measures the bytes that costs -- the point
   being that the ambiguity does not disappear, it changes denomination.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import generator
from src.crypto.merkle import MerkleSet, encoded_size
from src.model.dispute import build_disputes
from src.model.evidence import build_view, pad_set
from src.model.types import GroundTruth
from src.protocols.baselines import PROTOCOLS
from src.scoring.metrics import ScoredScenario, build_report
from src.scoring.scorer import score

RESULTS = Path(__file__).resolve().parents[2] / "results"

SCOPE_SIZES = [2, 4, 8, 16, 32, 64]
SEED = 20260808
PER_CLASS = 15

COMPARE = ["B3_suspected_exposed", "B10_composed", "B5_dispute_driven",
           "B7_verifiable_adjudication", "B13_witness_messages"]


def build(scope_size):
    generator.SCOPE_SIZE = scope_size
    return list(generator.generate(SEED, PER_CLASS))


def _evaluate(proto, sc, pad_to=None):
    view, oracle = build_view(sc, proto.policy, proto.entitlements, pad_to=pad_to)
    return proto.fn(view, build_disputes(view), oracle)


def main():
    rows, per_size = [], {}

    for n in SCOPE_SIZES:
        scenarios = build(n)
        row = {"scope": n}
        for name in COMPARE:
            proto = PROTOCOLS[name]
            byts, scored = [], []
            for sc in scenarios:
                v = _evaluate(proto, sc)
                byts.append(v.disclosed_bytes)
                scored.append(ScoredScenario(sc["scenario_id"], sc["m_class"],
                                             score(GroundTruth.from_scenario(sc), v)))
            rep = build_report(scored)
            row[name] = statistics.mean(byts)
            per_size.setdefault(name, {})[n] = {
                "scenario_success": rep.scenario_success,
                "full_class": f"{rep.classes_fully_solved}/{rep.classes_total}",
                "false_attribution": rep.false_attribution_rate,
                "worst_class": rep.worst_class_success,
            }
        rows.append(row)

    w = [8] + [28] * len(COMPARE)
    print("=" * 96)
    print("DISCLOSURE vs RECORD SIZE  (mean bytes actually transmitted)")
    print("=" * 96)
    print("  ".join(s.ljust(x) for s, x in zip(["scope"] + COMPARE, w)))
    for r in rows:
        print("  ".join(s.ljust(x) for s, x in zip(
            [str(r["scope"])] + [f"{r[b]:.0f}" for b in COMPARE], w)))
    print()

    print("=" * 96)
    print("SELECTIVE DISCLOSURE AS A FRACTION OF FULL-RECORD BILATERAL (B7 / B3)")
    print("=" * 96)
    for r in rows:
        for name in ("B7_verifiable_adjudication", "B13_witness_messages"):
            ratio = r[name] / r["B3_suspected_exposed"]
            print(f"  scope={r['scope']:>3}  {name:<28}{ratio:5.2f}x   "
                  f"{'#' * max(1, int(ratio * 40))}")
    print()

    print("=" * 96)
    print("DOES ACCURACY HOLD ACROSS SCALE?  (full-class solved / false-attribution rate)")
    print("=" * 96)
    w2 = [30] + [14] * len(SCOPE_SIZES)
    print("  ".join(s.ljust(x) for s, x in zip(
        ["protocol"] + [f"scope={n}" for n in SCOPE_SIZES], w2)))
    for name in COMPARE:
        cells = [name] + [f"{per_size[name][n]['full_class']} {per_size[name][n]['false_attribution']:.0%}"
                          for n in SCOPE_SIZES]
        print("  ".join(s.ljust(x) for s, x in zip(cells, w2)))
    print()

    # -- padding cost --------------------------------------------------------
    print("=" * 96)
    print("COST OF RESTORING TWIN INDISTINGUISHABILITY BY PADDING")
    print("=" * 96)
    print("A cardinality-binding root publishes |set|. Padding hides it, at the")
    print("price of a deeper tree and therefore larger proofs.")
    print()
    print(f"  {'real |set|':>11}{'pad to':>9}{'proof bytes':>14}{'padded':>10}{'overhead':>11}")
    pad_rows = []
    for real in (2, 3, 4, 8, 16):
        for pad in (8, 16, 64):
            if pad < real:
                continue
            items = [f"op:{i:03d}" for i in range(real)]
            absent = "op:999"
            plain = encoded_size(MerkleSet(items).prove_non_membership(absent))
            padded = encoded_size(MerkleSet(pad_set(items, pad)).prove_non_membership(absent))
            print(f"  {real:>11}{pad:>9}{plain:>14}{padded:>10}{padded / plain:>10.2f}x")
            pad_rows.append({"real": real, "pad_to": pad, "plain": plain,
                             "padded": padded, "overhead": padded / plain})
    print()

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "sweep.json").write_text(json.dumps(
        {"disclosure": rows,
         "accuracy": {k: {str(n): v for n, v in d.items()} for k, d in per_size.items()},
         "padding_cost": pad_rows}, indent=2))
    print("wrote results/sweep.json", file=sys.stderr)


if __name__ == "__main__":
    main()
