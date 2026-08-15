"""Full run: project, adjudicate, score, report.

Every number here comes from src/scoring/metrics.py. The v0.9 scripts each
computed their own notion of "correct" -- run.py counted a class as adjudicable
if any instance produced a correct blame or abstention, sweep.py tracked three
outcome labels out of eight, regression.py's "correct" omitted correct
abstention entirely. Those are now one function.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.generator import M_CLASSES, PRINCIPAL_LIAR
from src.model.types import Outcome
from src.protocols.baselines import PROTOCOLS
from src.reporting.harness import disclosure, load_corpus, reports, run_all

RESULTS = Path(__file__).resolve().parents[2] / "results"


def corpus_context_line(scenarios) -> str:
    """Describe corpus multiplicity from the corpus itself, never from a stale literal."""
    counts = Counter(s["m_class"] for s in scenarios)
    per_class = sorted(set(counts.values()))
    if len(per_class) == 1:
        multiplicity = f"{per_class[0]} times each"
    else:
        multiplicity = f"between {per_class[0]} and {per_class[-1]} times each"
    return (f"{len(counts)} adversarial structures instantiated {multiplicity} -- "
            f"NOT {len(scenarios)} independent empirical incidents.")


def main():
    scenarios = load_corpus()
    reps = reports(scenarios)
    disc = disclosure(scenarios)

    out: list[str] = []
    w = out.append

    class_counts = Counter(s["m_class"] for s in scenarios)
    multiplicities = sorted(set(class_counts.values()))
    per_class_text = (str(multiplicities[0]) if len(multiplicities) == 1
                      else f"{multiplicities[0]}-{multiplicities[-1]}")
    w(f"corpus: {len(scenarios)} scenarios, {len(M_CLASSES)} classes, "
      f"{per_class_text} instances per class")
    w(corpus_context_line(scenarios))
    w("")

    # -- headline ------------------------------------------------------------
    w("=" * 96)
    w("SECURITY SUMMARY  (full-class success is the adversarial metric: the "
      "attacker picks the input)")
    w("=" * 96)
    hdr = (f"{'protocol':<28}{'scenario':>10}{'full-class':>12}{'worst class':>14}"
           f"{'false attr':>12}{'missed':>9}")
    w(hdr)
    w("-" * len(hdr))
    for name, rep in reps.items():
        w(f"{name:<28}{rep.scenario_success:>9.1%}"
          f"{rep.classes_fully_solved:>7}/{rep.classes_total:<4}"
          f"{rep.worst_class_success:>9.0%} ({rep.worst_class})"
          f"{rep.false_attribution_rate:>11.1%}{rep.miss_rate:>9.1%}")
    w("")

    # -- full outcome distribution ------------------------------------------
    w("=" * 96)
    w("AGGREGATE OUTCOMES")
    w("=" * 96)
    labels = [o.value for o in Outcome]
    w(f"{'protocol':<28}" + "".join(f"{l[:11]:>13}" for l in labels))
    for name, rep in reps.items():
        totals = {o: 0 for o in Outcome}
        for c in rep.per_class.values():
            for o, n in c.counts.items():
                totals[o] += n
        w(f"{name:<28}" + "".join(f"{totals[o]:>13}" for o in Outcome))
    w("")

    # -- the regression column ----------------------------------------------
    w("=" * 96)
    w("PRINCIPAL-LIAR CLASSES (M5 M6 M7 M9) -- can a correct executor defend itself?")
    w("=" * 96)
    w(f"{'protocol':<28}{'correct_blame':>15}{'correct_contra':>16}"
      f"{'false_accusation':>18}{'missed':>9}")
    for name, rep in reps.items():
        cb = cc = fa = ms = 0
        for m in PRINCIPAL_LIAR:
            c = rep.per_class.get(m)
            if not c:
                continue
            cb += c.counts.get(Outcome.CORRECT_BLAME, 0)
            cc += c.counts.get(Outcome.CORRECT_CONTRADICTION, 0)
            fa += c.counts.get(Outcome.FALSE_ACCUSATION, 0)
            ms += c.counts.get(Outcome.MISSED, 0)
        w(f"{name:<28}{cb:>15}{cc:>16}{fa:>18}{ms:>9}")
    w("")

    # -- per class, full distribution, not the modal label -------------------
    w("=" * 96)
    w("PER-CLASS SUCCESS RATE  (not the modal label: a class is solved only if "
      "every instance succeeds)")
    w("=" * 96)
    classes = sorted(M_CLASSES, key=lambda m: int(m[1:]))
    w(f"{'protocol':<28}" + "".join(f"{m:>5}" for m in classes))
    for name, rep in reps.items():
        cells = []
        for m in classes:
            c = rep.per_class.get(m)
            if c is None:
                cells.append("    -")
            elif c.fully_solved:
                cells.append("  100")
            else:
                cells.append(f"{c.success_rate * 100:>5.0f}")
        w(f"{name:<28}" + "".join(cells))
    w("")

    # -- disclosure ----------------------------------------------------------
    w("=" * 96)
    w("DISCLOSURE TO ADJUDICATOR  (bytes actually transmitted, mean)")
    w("=" * 96)
    b1 = statistics.mean(disc["B1_bilateral_commitment"])
    w(f"{'protocol':<28}{'mean bytes':>12}{'vs B1':>9}{'full-class':>12}")
    for name, rep in reps.items():
        mean = statistics.mean(disc[name])
        w(f"{name:<28}{mean:>12.0f}{mean / b1:>8.2f}x"
          f"{rep.classes_fully_solved:>8}/{rep.classes_total}")
    w("")

    # -- what disclosure buys ------------------------------------------------
    w("=" * 96)
    w("WHAT DIES WHEN CONTENTS ARE WITHHELD  (B1 full disclosure -> B2 commitments only)")
    w("=" * 96)
    lost, kept = [], []
    for m in classes:
        a = reps["B1_bilateral_commitment"].per_class.get(m)
        b = reps["B2_commitment_only"].per_class.get(m)
        if a and b and a.fully_solved and not b.fully_solved:
            lost.append(m)
        elif a and b and a.fully_solved and b.fully_solved:
            kept.append(m)
    w(f"survives commitment-only adjudication : {', '.join(kept) or '(none)'}")
    w(f"lost when contents are withheld       : {', '.join(lost) or '(none)'}")
    w("")

    text = "\n".join(out)
    print(text)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "summary.txt").write_text(text + "\n")
    (RESULTS / "per_class.json").write_text(json.dumps(
        {name: {m: {o.value: n for o, n in c.counts.items()}
                for m, c in rep.per_class.items()}
         for name, rep in reps.items()}, indent=2))
    print("wrote results/summary.txt and results/per_class.json", file=sys.stderr)


if __name__ == "__main__":
    main()
