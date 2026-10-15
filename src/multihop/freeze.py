"""Two-party freeze.

The multi-hop phase adds a corpus, protocols and gate stages. It may not move a
single two-party figure: every published claim rests on those numbers, and the
three-party work is presented as an extension of them, not a revision.

This pins the two-party corpus by hash and every two-party protocol's
full-class count and correct-scenario total by value. A change to any of them
fails the gate, and the fix is a recorded decision -- update the pins here, in
the same commit, with a note in RESEARCH.md saying why -- never a silent drift.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TWO_PARTY_CORPUS = ROOT / "corpus" / "corpus.v0.9.jsonl"

PINNED_SHA256 = "50e5c6b5d3d93a4654db4c991b0a0e20f59e98c04cd97c1fb7c438854843d8c1"
PINNED_SIZE = (850, 34, 18)       # scenarios, classes, protocols

#: protocol -> (classes fully solved, correct scenarios), pinned 2026-10-15 at v0.10.2
PINNED_RESULTS = {
    "B0_bearer_executor_log": (13, 325),
    "B1_bilateral_commitment": (21, 525),
    "B2_commitment_only": (18, 450),
    "B3_suspected_exposed": (21, 525),
    "B4_scope_predicates": (20, 500),
    "B5_dispute_driven": (20, 500),
    "B6_accountable_queries": (21, 525),
    "B7_verifiable_adjudication": (22, 550),
    "B6c_under_collusion": (21, 525),
    "B9_non_attributive": (25, 625),
    "B10_composed": (26, 650),
    "B11_stateful": (24, 652),
    "B7r_under_revocation": (22, 550),
    "B15_short_term_keys": (26, 650),
    "B16c_custodial_attestor": (28, 700),
    "B16d_digest_attestor": (26, 650),
    "B13_witness_messages": (26, 650),
    "B17_duty_to_answer": (26, 650),
}


def check() -> list[str]:
    from ..generator import M_CLASSES
    from ..protocols.baselines import PROTOCOLS
    from ..reporting.harness import load_corpus, reports

    errs = []
    digest = hashlib.sha256(TWO_PARTY_CORPUS.read_bytes()).hexdigest()
    if digest != PINNED_SHA256:
        errs.append(f"two-party corpus hash changed: {digest[:16]}... "
                    f"(pinned {PINNED_SHA256[:16]}...)")
    scs = load_corpus()
    size = (len(scs), len(M_CLASSES), len(PROTOCOLS))
    if size != PINNED_SIZE:
        errs.append(f"two-party size changed: {size}, pinned {PINNED_SIZE}")
    reps = reports(scs)
    got = {n: (r.classes_fully_solved, sum(c.correct for c in r.per_class.values()))
           for n, r in reps.items()}
    for name in sorted(set(got) | set(PINNED_RESULTS)):
        if got.get(name) != PINNED_RESULTS.get(name):
            errs.append(f"two-party result moved: {name} {got.get(name)}, "
                        f"pinned {PINNED_RESULTS.get(name)}")
    return errs


def main():
    print("-- two-party freeze (the multi-hop phase may not move a two-party figure)")
    errs = check()
    if errs:
        for e in errs:
            print(f"  {e}")
        raise SystemExit("FREEZE: two-party figures moved")
    print(f"  corpus hash, size {PINNED_SIZE} and {len(PINNED_RESULTS)} protocols' "
          f"results match their pins")


if __name__ == "__main__":
    main()
