"""Documentation staleness check.

Every findings document carries absolute figures, and those figures go stale
every time the corpus grows or a mechanism is corrected. Hand-maintained
staleness banners are no better: the banners themselves went stale ("the corpus
grew from 325 to 650") the moment it reached 750.

So this checks the documents against the code rather than against a reader's
memory. Three things are verified:

  1. every declared corpus size matches, or is explicitly marked superseded
  2. every full-class figure of the form N/D uses the current class count
  3. the headline claims in the current findings still hold when recomputed

A document may be legitimately out of date -- the earlier findings are a record
of what was believed at the time, and rewriting them would destroy that record.
What is NOT legitimate is a stale figure with nothing saying so. The check
therefore demands a marker, not a rewrite.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

#: A document carrying one of these is a historical record. It must still be
#: internally consistent, but its figures are not expected to match current code.
SUPERSEDED_MARKERS = ("STALENESS NOTICE", "SUPERSEDED", "HISTORICAL RECORD", "HISTORICAL FINDING", "HISTORICAL DIFF")

#: Documents that describe the CURRENT state and must match the code exactly.
LIVE_DOCS = (
    "../README.md",
    "../RESEARCH.md",
    "scorer-semantics.md",
    "architecture.md",
    "findings/12-conservation-boundary.md",
    "what-is-established.md",
    "pruning.md",
    "findings/13-abort-and-declarations.md",
    "../INDEX.md",
    "../CONTRIBUTING.md",
    "../CITATION.cff",
    "articles/02-general-audience.md",
    "test-evidence-map.md",
)

#: Claims that have been corrected. Any document asserting the OLD form must
#: carry a pointer to where it was corrected -- the numeric check cannot see
#: superseded REASONING, only superseded figures, and five documents were found
#: carrying refuted arguments while passing the numeric check cleanly.
CORRECTED_CLAIMS = (
    ("M22", "resisted every mechanism",
     "M22 is solved by the full-disclosure family at the cost of M23",
     "findings/12"),
    ("PRINCIPAL_LIAR", "principal-liar classes (M5",
     "F01 is scoped to ASSERTIONAL lies; B1 scores 0 on M13/M26/M28/M32",
     "RC-H12"),
    ("residual", "no party-made commitment can bind",
     "bindability is pairwise, not per class",
     "RC-H12"),
    ("OPEN-3", "needs your call",
     "resolved as a coherence invariant",
     "scorer-semantics"),
    # Articles are the most expensive place for drift: once published, a stale
    # figure cannot be quietly corrected. They are checked like live docs.
    ("A2A", "None of them is cited by the 2024-2026",
     "scoped to the proposals actually checked",
     "prior-art/2026-protocol-landscape"),
    ("T4", "T4's impossibility as novel",
     "T4 is subsumed by the conservation boundary",
     "findings/12"),
)

CORPUS_SIZE_RE = re.compile(r"\b(\d{3,4})\s+scenarios\b")
#: Test-suite size is quoted in live documents. It was not previously checked,
#: and an earlier report was sitting at 108 while the suite was at 157 --
#: passing the numeric gate cleanly, because the gate did not parse this shape.
#: Same lesson as RC-H15: a check is only as wide as the forms it can read.
TEST_COUNT_RE = re.compile(r"\b(\d{2,4})\s+tests\b")
CLASS_COUNT_RE = re.compile(r"\b(\d{1,2})\s+(?:M-)?classes\b")
FULL_CLASS_RE = re.compile(r"\b(\d{1,2})/(\d{2})\b")


def collected_test_count() -> int:
    """Number of tests pytest actually collects. Derived, never asserted."""
    import subprocess

    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/"],
        cwd=ROOT, capture_output=True, text=True)
    for line in reversed(out.stdout.strip().splitlines()):
        m = re.match(r"(\d+) tests? collected", line.strip())
        if m:
            return int(m.group(1))
    raise SystemExit("STALENESS: could not determine the collected test count")


def current_facts() -> dict:
    from ..generator import M_CLASSES
    from ..protocols.baselines import PROTOCOLS
    from ..reporting.harness import load_corpus

    scs = load_corpus()
    return {
        "scenarios": len(scs),
        "classes": len(M_CLASSES),
        "protocols": len(PROTOCOLS),
        "tests": collected_test_count(),
    }


def check_doc(path: Path, facts: dict) -> list[str]:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(DOCS)
    superseded = any(m in text for m in SUPERSEDED_MARKERS)
    live = str(rel) in LIVE_DOCS
    errs: list[str] = []

    sizes = {int(m) for m in CORPUS_SIZE_RE.findall(text)}
    counts = {int(m) for m in CLASS_COUNT_RE.findall(text)}
    wrong_size = sizes - {facts["scenarios"]}
    wrong_count = counts - {facts["classes"]}

    if live:
        if wrong_size:
            errs.append(f"{rel}: live doc cites corpus size(s) {sorted(wrong_size)}, "
                        f"current is {facts['scenarios']}")
        if wrong_count:
            errs.append(f"{rel}: live doc cites class count(s) {sorted(wrong_count)}, "
                        f"current is {facts['classes']}")
        wrong_tests = {int(m) for m in TEST_COUNT_RE.findall(text)} - {facts["tests"]}
        if wrong_tests:
            errs.append(f"{rel}: live doc cites test count(s) {sorted(wrong_tests)}, "
                        f"current is {facts['tests']}")
        denominators = {int(d) for _n, d in FULL_CLASS_RE.findall(text)}
        wrong_denom = {d for d in denominators if d in (26, 30) and d != facts["classes"]}
        # 25 is the per-class instance count and is legitimate; only flag class
        # denominators that were the OLD class count.
        wrong_denom = {d for d in wrong_denom if d != 25}
        if wrong_denom:
            errs.append(f"{rel}: live doc uses stale full-class denominator(s) "
                        f"{sorted(wrong_denom)}, current is {facts['classes']}")
    elif (wrong_size or wrong_count) and not superseded:
        errs.append(f"{rel}: cites stale figures {sorted(wrong_size | wrong_count)} "
                    f"with no staleness marker")

    # superseded REASONING, which the numeric checks cannot see
    for _tag, old_form, _correction, pointer in CORRECTED_CLAIMS:
        if old_form in text and pointer not in text and not superseded:
            errs.append(f"{rel}: asserts a corrected claim ({old_form!r}) with no "
                        f"pointer to {pointer}")

    return errs


def check_root_doc(path, facts: dict) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errs = []
    sizes = {int(m) for m in CORPUS_SIZE_RE.findall(text)} - {facts["scenarios"]}
    counts = {int(m) for m in CLASS_COUNT_RE.findall(text)} - {facts["classes"]}
    if sizes:
        errs.append(f"{path.name}: cites corpus size(s) {sorted(sizes)}, "
                    f"current is {facts['scenarios']}")
    if counts:
        errs.append(f"{path.name}: cites class count(s) {sorted(counts)}, "
                    f"current is {facts['classes']}")
    tests = {int(m) for m in TEST_COUNT_RE.findall(text)} - {facts["tests"]}
    if tests:
        errs.append(f"{path.name}: cites test count(s) {sorted(tests)}, "
                    f"current is {facts['tests']}")
    for _tag, old_form, _correction, pointer in CORRECTED_CLAIMS:
        if old_form in text and pointer not in text:
            errs.append(f"{path.name}: asserts a corrected claim ({old_form!r}) "
                        f"with no pointer to {pointer}")
    return errs


def check_headline_claims() -> list[str]:
    """Recompute the claims the current findings actually rest on. A document
    that states one of these is only as good as the recomputation."""
    from ..generator import PRINCIPAL_LIAR
    from ..model.types import Outcome
    from ..protocols.baselines import PROTOCOLS
    from ..reporting.harness import load_corpus, reports

    scs = load_corpus()
    reps = reports(scs)
    errs: list[str] = []

    def claim(ok, msg):
        if not ok:
            errs.append(f"CLAIM FAILED: {msg}")

    # F01 -- the regression
    b0 = sum(reps["B0_bearer_executor_log"].per_class[m].counts.get(Outcome.CORRECT_BLAME, 0)
             for m in PRINCIPAL_LIAR)
    b1 = sum(reps["B1_bilateral_commitment"].per_class[m].counts.get(Outcome.CORRECT_BLAME, 0)
             for m in PRINCIPAL_LIAR)
    n = 25 * len(PRINCIPAL_LIAR)
    claim(b0 == 0, f"F01: B0 should score 0 correct blame on principal-liar classes, got {b0}")
    claim(b1 == n, f"F01: B1 should score {n}/{n}, got {b1}")

    # B13 / B17 -- the exchange
    r13, r17 = reps["B13_witness_messages"], reps["B17_duty_to_answer"]
    claim(r13.classes_fully_solved == r17.classes_fully_solved,
          f"B17 exchange: full-class should be unchanged, "
          f"{r13.classes_fully_solved} vs {r17.classes_fully_solved}")
    claim(r13.false_attribution_rate == 0.0 and r17.false_attribution_rate == 0.0,
          "B13/B17 should make no false attributions")

    def fails(r):
        return {m for m, c in r.per_class.items() if c.correct != c.n}

    lost, gained = fails(r17) - fails(r13), fails(r13) - fails(r17)
    claim(len(lost) == len(gained),
          f"B17 exchange should be one-for-one, lost {len(lost)} gained {len(gained)}")

    missed13 = sum(c.counts.get(Outcome.MISSED, 0) for c in r13.per_class.values())
    missed17 = sum(c.counts.get(Outcome.MISSED, 0) for c in r17.per_class.values())
    fc13 = sum(c.counts.get(Outcome.FALSE_CONTRADICTION, 0) for c in r13.per_class.values())
    fc17 = sum(c.counts.get(Outcome.FALSE_CONTRADICTION, 0) for c in r17.per_class.values())
    claim((missed13 - missed17) == (fc17 - fc13),
          "B17 exchange should conserve exactly: misses traded for false contradictions")

    # worst-class success -- the honest headline
    claim(all(r.worst_class_success == 0.0 for r in reps.values()),
          "at least one protocol no longer has a fully-failed class; "
          "the 'no mechanism is adversarially complete' claim needs revising")

    # No class is unreachable by EVERY mechanism. This corrects the earlier
    # claim that M22 was: that was measured across the commitment-only family
    # only, and the full-disclosure family solves M22 at the cost of M23.
    unreached = {m for m in reps["B0_bearer_executor_log"].per_class
                 if all(r.per_class[m].correct != r.per_class[m].n for r in reps.values())}
    claim(unreached == set(),
          f"no class should be unreachable by every mechanism, got {unreached}")

    # The conservation boundary predicts every twin pair.
    from ..validation.conservation import classify, solved_both
    for guilty, honest, verdict, _dg, _dh in classify(scs):
        both = solved_both(scs, reps, guilty, honest)
        claim((verdict == "escapable") == bool(both),
              f"conservation boundary: {guilty}/{honest} predicted {verdict}, "
              f"{len(both)} mechanism(s) solved both")

    return errs


def main():
    facts = current_facts()
    print("=" * 88)
    print("DOCUMENTATION STALENESS CHECK")
    print("=" * 88)
    print(f"\ncurrent: {facts['scenarios']} scenarios, {facts['classes']} classes, "
          f"{facts['protocols']} protocols, {facts['tests']} tests\n")

    errs: list[str] = []
    for path in sorted(DOCS.rglob("*.md")):
        errs.extend(check_doc(path, facts))
    # Public-facing root documents are checked directly. ARTICLE-MEDIUM.md is the
    # single canonical technical article; keeping a duplicate under docs/articles/
    # created a needless drift surface.
    for name in ("README.md", "RESEARCH.md", "INDEX.md",
                 "CONTRIBUTING.md", "CITATION.cff", "ARTICLE-MEDIUM.md"):
        root_doc = ROOT / name
        if root_doc.exists():
            errs.extend(check_root_doc(root_doc, facts))

    claim_errs = check_headline_claims()

    if errs:
        print("-- stale figures --")
        for e in errs:
            print(f"  {e}")
    else:
        print("-- stale figures: none --")

    if claim_errs:
        print("\n-- headline claims --")
        for e in claim_errs:
            print(f"  {e}")
    else:
        print("-- headline claims: all recompute correctly --")

    if errs or claim_errs:
        raise SystemExit(f"STALENESS: {len(errs) + len(claim_errs)} issue(s)")


if __name__ == "__main__":
    main()
