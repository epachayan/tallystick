"""Canonical numbers, re-derived from current code.

Any absolute count in a document that was not produced by this script is stale
by construction. Paste from here; never carry a figure forward by hand.

The v0.9 version of this script defined "correct" as
`correct_blame + correct_contradiction`, which silently discarded both
abstention outcomes and so scored a mechanism that correctly refuses to blame
anyone as a total failure. It now uses the canonical metrics module.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.commitments import minimal_cover, residual
from src.generator import (M_CLASSES, PRINCIPAL_LIAR,
                           PRINCIPAL_LIAR_NON_ASSERTIONAL)
from src.model.types import Outcome
from src.protocols.baselines import PROTOCOLS
from src.reporting.harness import load_corpus, reports
from src.scoring.scorer import score
from src.validation import twins

RESULTS = Path(__file__).resolve().parents[2] / "results"


def main():
    scs = load_corpus()
    reps = reports(scs)
    out: list[str] = []
    w = out.append

    w("=" * 96)
    w(f"CANONICAL NUMBERS -- corpus.v0.9.jsonl, {len(scs)} scenarios, "
      f"{len(M_CLASSES)} classes, {len(PROTOCOLS)} protocols")
    w("hardened harness: evidence-only protocol input, world-first scorer, "
      "verified Merkle proofs")
    w("=" * 96)

    # -- F01 -----------------------------------------------------------------
    w("\n[F01] can a correct executor defend itself when the principal lies?")
    w("      SCOPE (RC-H12): stated over ASSERTIONAL lies only -- the principal")
    w("      asserts something a signature contradicts. The corpus has four more")
    w("      classes with a dishonest principal and a correct executor where the")
    w("      misconduct is non-assertional, and bilateral commitment does not reach it.")
    tot = 25 * len(PRINCIPAL_LIAR)
    tot2 = 25 * len(PRINCIPAL_LIAR_NON_ASSERTIONAL)
    w(f"\n      assertional ({' '.join(sorted(PRINCIPAL_LIAR, key=lambda m: int(m[1:])))}):")
    for n in ("B0_bearer_executor_log", "B1_bilateral_commitment"):
        cb = sum(reps[n].per_class[m].counts.get(Outcome.CORRECT_BLAME, 0)
                 for m in PRINCIPAL_LIAR)
        w(f"        {n:<28}{cb}/{tot} correct blame")
    w(f"\n      non-assertional "
      f"({' '.join(sorted(PRINCIPAL_LIAR_NON_ASSERTIONAL, key=lambda m: int(m[1:])))}) "
      f"-- baseless complaint, withheld record, abort:")
    for n in ("B0_bearer_executor_log", "B1_bilateral_commitment",
              "B13_witness_messages", "B17_duty_to_answer"):
        ok = sum(reps[n].per_class[m].correct for m in PRINCIPAL_LIAR_NON_ASSERTIONAL)
        w(f"        {n:<28}{ok}/{tot2} handled")
    w("\n      B1 scores 0 on the non-assertional set, exactly as B0 does. The")
    w("      original F01 denominator excluded these, which flattered B1.")

    # -- F03 -----------------------------------------------------------------
    w("\n[F03] over-attribution -- naming a MISTAKEN party as culpable")
    for n in ("B7_verifiable_adjudication", "B10_composed", "B16d_digest_attestor"):
        oa = sum(c.counts.get(Outcome.OVER_ATTRIBUTION, 0)
                 for c in reps[n].per_class.values())
        w(f"  {n:<30}{oa}/{len(scs)}")

    # -- aggregate -----------------------------------------------------------
    w("\n[aggregate] every protocol, canonical metrics")
    w(f"  {'protocol':<30}{'scenario':>10}{'full-class':>12}{'worst':>8}"
      f"{'false-attr':>12}{'missed':>9}")
    for n, rep in reps.items():
        w(f"  {n:<30}{rep.scenario_success:>9.1%}"
          f"{rep.classes_fully_solved:>7}/{rep.classes_total:<4}"
          f"{rep.worst_class_success:>7.0%}{rep.false_attribution_rate:>12.1%}"
          f"{rep.miss_rate:>9.1%}")

    # -- F07 -----------------------------------------------------------------
    cov, res = minimal_cover(), residual()
    w(f"\n[F07] minimal commitment set: {len(cov)} -- {', '.join(cov)}")
    w(f"      residual classes under that vocabulary: {len(res)} -- {', '.join(sorted(res))}")
    w("      NOTE: M19 and M20 are separated from their benign twins by the")
    w("      cardinality a sound commitment already binds. T10's residual is")
    w("      narrower than the vocabulary in commitments.py suggests.")

    # -- F08 paired test -----------------------------------------------------
    w("\n[F08] paired test -- catch the adversarial twin WITHOUT condemning the benign one")
    good = {Outcome.CORRECT_BLAME, Outcome.CORRECT_CONTRADICTION}
    bad = {Outcome.FALSE_ACCUSATION, Outcome.OVER_ATTRIBUTION,
           Outcome.UNSUPPORTED_BLAME, Outcome.FALSE_CONTRADICTION}
    for mistake, malicious, status, _why in twins.PAIRS:
        if status != "twin":
            continue
        winners = []
        for n, rep in reps.items():
            a = rep.per_class.get(malicious)
            b = rep.per_class.get(mistake)
            if not a or not b:
                continue
            caught = sum(a.counts.get(o, 0) for o in good)
            harmed = sum(b.counts.get(o, 0) for o in bad)
            if caught > 0 and harmed == 0:
                winners.append(n)
        w(f"  {malicious + '/' + mistake:<12}{', '.join(winners) if winners else 'NONE'}")

    # -- twin standing -------------------------------------------------------
    w("\n[F09] twin indistinguishability under the projection (observable fingerprint)")
    for a, b, status, why in twins.PAIRS:
        w(f"  {a + '/' + b:<10}{status:<10}{why}")

    # -- F10: does the mechanism survive hiding cardinality? -----------------
    w("\n[F10] full-class success with and without the cardinality leak")
    w("      A sound sorted-leaf commitment publishes |set|. Padding hides it.")
    w("      A mechanism that loses classes here was leaning on the leak.")
    from src.model.dispute import build_disputes
    from src.model.evidence import build_view
    from src.protocols.baselines import PROTOCOLS as _P
    from src.scoring.metrics import ScoredScenario, build_report
    from src.model.types import GroundTruth as _GT
    w(f"  {'protocol':<30}{'unpadded':>10}{'padded':>9}{'delta':>8}")
    for n, proto in _P.items():
        cells = []
        for pad in (None, 8):
            rows = []
            for s_ in scs:
                v, o = build_view(s_, proto.policy, proto.entitlements, pad_to=pad)
                rows.append(ScoredScenario(s_["scenario_id"], s_["m_class"],
                                           score(_GT.from_scenario(s_),
                                                 proto.fn(v, build_disputes(v), o))))
            cells.append(build_report(rows).classes_fully_solved)
        delta = cells[1] - cells[0]
        w(f"  {n:<30}{cells[0]:>7}/{len(M_CLASSES)}{cells[1]:>6}/{len(M_CLASSES)}{delta:>+8}")

    w("\n" + "=" * 96)
    w("STALENESS: any published figure of the form 'X of 325/375/475/600' predates")
    w(f"this corpus ({len(scs)}). Any figure produced before the hardening refactor")
    w("predates the current scorer and the evidence-only protocol input.")
    w("=" * 96)

    text = "\n".join(out)
    print(text)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "canonical.txt").write_text(text + "\n")
    print("wrote results/canonical.txt", file=sys.stderr)


if __name__ == "__main__":
    main()
