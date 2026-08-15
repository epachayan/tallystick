"""Coverage audit: do the 26 hand-built classes span the space they claim to?

F-H3 showed one twin declaration had been wrong since the corpus was built, and
nothing caught it. The taxonomy is a hand-maintained artifact of the same kind,
so it deserves the same treatment: derive the space, then check the declaration
against it.

The space is the cross-product of the two axes that actually determine what an
adjudicator can do, both read from the projected EvidenceView rather than from
the class label:

    ASSERTION   what each party volunteered that a commitment could contradict
    WITHHOLDING what was not produced

Those are the axes because B13's residual falls out of exactly one of them --
"the refuge is silence" is a statement about the assertion axis -- and B17's
exchange falls out of the other.

A cell is REACHED if some scenario in the corpus projects into it. An unreached
cell is not automatically a gap: many are structurally impossible (you cannot
assert contents for a record you withhold). The audit separates the two and
reports only cells that are possible and unpopulated.
"""

from __future__ import annotations

import itertools
from collections import defaultdict

from ..model.evidence import DisclosurePolicy, build_view
from ..model.types import GroundTruth, Party


# ---------------------------------------------------------------------------
# The two axes, derived from the view
# ---------------------------------------------------------------------------

def assertion_profile(view) -> tuple[str, str]:
    """What each party said that a commitment could check."""
    def one(claims):
        said = []
        if claims.asserted_scope is not None:
            said.append("scope")
        if claims.asserted_actions is not None:
            said.append("actions")
        return "+".join(said) if said else "silent"
    return one(view.p), one(view.e)


def withholding_profile(view) -> str:
    parts = []
    if not view.auth_committed:
        parts.append("no_commitment")
    if not view.auth_exists:
        parts.append("no_grant")
    if not view.e.record_available:
        parts.append("e_record")
    if not view.p.record_available:
        parts.append("p_record")
    if view.attestor_present and not view.attestor_available:
        parts.append("attestor")
    if view.key_revocation_claimed:
        parts.append("keys_voided")
    return "+".join(parts) if parts else "nothing"


def cell(sc) -> tuple:
    view, _ = build_view(sc, DisclosurePolicy.COMMITMENT_ONLY)
    p_says, e_says = assertion_profile(view)
    return (p_says, e_says, withholding_profile(view))


# ---------------------------------------------------------------------------
# Which cells are structurally possible
# ---------------------------------------------------------------------------

P_SAYS = ("silent", "scope", "actions", "scope+actions")
E_SAYS = ("silent", "scope", "actions", "scope+actions")
WITHHELD = ("nothing", "e_record", "p_record", "no_grant", "keys_voided",
            "attestor", "no_commitment")


def possible(p_says: str, e_says: str, withheld: str) -> bool:
    """Structural feasibility, independent of whether the corpus has an instance.

    The one hard rule: a party cannot assert the contents of a record it is
    simultaneously refusing to produce. Everything else is a world someone could
    construct.
    """
    if "e_record" in withheld and "actions" in e_says:
        return False
    if "no_commitment" in withheld and withheld != "no_commitment":
        return False
    return True


def audit(scenarios):
    """Returns (reached, missing, by_cell)."""
    by_cell: dict[tuple, list[str]] = defaultdict(list)
    for sc in scenarios:
        by_cell[cell(sc)].append(sc["m_class"])

    reached = set(by_cell)
    space = {(p, e, w) for p, e, w in itertools.product(P_SAYS, E_SAYS, WITHHELD)
             if possible(p, e, w)}
    missing = space - reached
    return reached, missing, by_cell


# ---------------------------------------------------------------------------
# Which gaps actually matter
# ---------------------------------------------------------------------------

def interesting(missing) -> list[tuple]:
    """A gap matters when it could change a claim already made.

    The two live claims are B13's ("the refuge is silence") and B17's (the duty
    exchange). Both turn on the executor's assertion profile interacting with
    withholding, so the gaps that matter are the ones where E says something
    unusual while something is withheld -- those are the cells that could
    contain a counterexample.
    """
    out = []
    for p_says, e_says, withheld in sorted(missing):
        if withheld == "nothing":
            continue                      # nothing withheld: nothing to hide
        if e_says == "silent" and withheld in ("e_record", "no_commitment"):
            continue                      # already the studied residual
        out.append((p_says, e_says, withheld))
    return out


def main():
    from ..reporting.harness import load_corpus

    scs = load_corpus()
    reached, missing, by_cell = audit(scs)

    print("=" * 88)
    print("COVERAGE AUDIT -- do 26 hand-built classes span the assertion x withholding space?")
    print("=" * 88)
    print(f"\ncells occupied by the corpus: {len(reached)}")
    print(f"structurally possible cells : {len(reached) + len(missing)}")
    print(f"possible but unpopulated    : {len(missing)}")

    print("\n-- occupied cells --")
    print(f"  {'P asserts':<15}{'E asserts':<16}{'withheld':<22}classes")
    for c in sorted(by_cell, key=lambda k: (k[2], k[1], k[0])):
        classes = sorted(set(by_cell[c]), key=lambda m: int(m[1:]))
        print(f"  {c[0]:<15}{c[1]:<16}{c[2]:<22}{', '.join(classes)}")

    gaps = interesting(missing)
    print(f"\n-- gaps that could bear on a live claim: {len(gaps)} --")
    if not gaps:
        print("  (none)")
    for p_says, e_says, withheld in gaps:
        print(f"  P={p_says:<15}E={e_says:<16}withheld={withheld}")

    # -- the asymmetry check: is withholding modelled for both parties? -----
    p_withholds = sum(1 for s_ in scs if not s_["p_view"]["record_available"])
    e_withholds = sum(1 for s_ in scs if not s_["e_view"]["record_available"])
    print("\n-- withholding, by party --")
    print(f"  principal withholds its own record : {p_withholds:>4} / {len(scs)}")
    print(f"  executor  withholds its own record : {e_withholds:>4} / {len(scs)}")
    if p_withholds == 0 and e_withholds > 0:
        print("  ASYMMETRY: withholding is modelled as an executor-only behaviour.")
        print("  No class states this; it is a property of how every class is built.")
        print("  Any mechanism whose duty attaches on non-production inherits it (RC-H9).")

    print("\nA gap is not automatically a missing class. It is a question:")
    print("could a scenario in this cell contradict something already claimed?")
    return gaps


if __name__ == "__main__":
    main()
