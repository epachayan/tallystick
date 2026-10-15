"""Twins and the conservation boundary, with three parties.

Two things are DERIVED here rather than declared:

1. Which class pairs are evidential twins, and under which protocols. A pair is
   a twin for a protocol when every instance projects to the same observable
   view under that protocol's specification and disclosure. The declared
   expectation (EXPECTED_TWINS) is diffed against the derivation; a mismatch
   fails the gate.

2. Whether a twin pair is escapable. The two-party rule (findings/12) was

       escapable  iff  D(guilty) == D(honest)

   derived on twin pairs in which every world had at most one diverging party.
   The underlying statement is more general -- a pair is escapable iff SOME
   verdict is scored correct in both worlds -- and once a world can have two
   diverging parties (with or without an intermediary) the equality rule is no
   longer equivalent to it. The general condition, read off the scorer:

       escapable  iff  D(g) & D(h) is non-empty         (contradict the overlap)
                   or  abstention is correct in both     (nobody dishonest,
                                                          every divergence a mistake)

   This module computes escapability by brute force over every verdict the
   vocabulary can express, checks that the intersection rule reproduces it on
   every pair (three-party AND two-party), reports where the equality rule
   disagrees, and checks the empirical side: no protocol solves both worlds of
   a binding pair for which the pair is a twin.

3. Whether a twin pair is localisable: some single verdict names exactly D in
   both worlds. The rule is

       localisable  iff  D(a) == D(b), and D is non-empty

   (an honest world has nothing to localise). Also computed by brute force.

Both rules are additionally checked on every pair of adjudicable three-party
worlds (each party honest, mistaken or dishonest: 27 worlds, 729 pairs), so
they do not rest on the four pairs the corpus happens to contain.
"""

from __future__ import annotations

from itertools import combinations, product

from ..model.types import SUCCESS_OUTCOMES
from .evidence import build_view
from .generator import H_CLASSES, load_corpus
from .model import PARTIES, State, Status3, Truth3, Verdict3, fmt, localised, score3
from .protocols import PROTOCOLS3

#: (honest-or-mistaken class, guilty class) -> protocols' specs under which the
#: pair is expected to be an evidential twin. Diffed against the derivation.
EXPECTED_TWINS = {
    ("H3", "H2"): {"bearer3", "hop3", "chain3"},
    ("H4", "H5"): {"bearer3", "hop3"},
    ("H7", "H6"): {"bearer3", "hop3", "chain3"},
    ("H9", "H8"): {"bearer3", "hop3"},
}


# ---------------------------------------------------------------------------
# Derivation of twins
# ---------------------------------------------------------------------------

def _by_class(scenarios):
    out: dict[str, list[dict]] = {}
    for s in scenarios:
        out.setdefault(s["h_class"], []).append(s)
    return out


def twin_under(scenarios, a: str, b: str, proto) -> bool:
    bc = _by_class(scenarios)
    xs, ys = bc[a], bc[b]
    if len(xs) != len(ys):
        return False
    for x, y in zip(xs, ys):
        vx, _ = build_view(proto.spec, x, proto.disclosure)
        vy, _ = build_view(proto.spec, y, proto.disclosure)
        if vx.fingerprint() != vy.fingerprint():
            return False
    return True


def derive_twins(scenarios) -> dict[tuple[str, str], set[str]]:
    """Every class pair, every protocol. Returns pair -> set of protocol names."""
    out: dict[tuple[str, str], set[str]] = {}
    for a, b in combinations(H_CLASSES, 2):
        for name, proto in PROTOCOLS3.items():
            if twin_under(scenarios, a, b, proto):
                out.setdefault((a, b), set()).add(name)
    return out


def twin_audit(scenarios) -> list[str]:
    """Derive, then diff against EXPECTED_TWINS (stated per specification)."""
    derived = derive_twins(scenarios)
    errs = []
    norm = {tuple(sorted(k)): v for k, v in derived.items()}
    expected = {tuple(sorted(k)): v for k, v in EXPECTED_TWINS.items()}
    for pair in sorted(set(norm) | set(expected)):
        got = {PROTOCOLS3[n].spec_name for n in norm.get(pair, set())}
        want = expected.get(pair, set())
        if got != want:
            errs.append(f"twin {pair[0]}/{pair[1]}: declared under {sorted(want)}, "
                        f"derived under {sorted(got)}")
    return errs


# ---------------------------------------------------------------------------
# Escapability
# ---------------------------------------------------------------------------

def all_verdicts3():
    yield Verdict3()
    yield Verdict3(detected=True, status=Status3.SUSPECTED)
    for k in range(1, 4):
        for c in combinations(PARTIES, k):
            yield Verdict3(detected=True, contradicted=frozenset(c), attributes_fault=False,
                           status=Status3.CONTRADICTED)
            yield Verdict3(detected=True, blamed=frozenset(c), attributes_fault=True,
                           status=Status3.EXPOSED)


def brute_escapable3(tg: Truth3, th: Truth3) -> bool:
    return any(score3(tg, v) in SUCCESS_OUTCOMES and score3(th, v) in SUCCESS_OUTCOMES
               for v in all_verdicts3())


def _abstain_ok(d, mistaken, dishonest) -> bool:
    return not dishonest and d <= mistaken


def rule_intersection(dg, mg, xg, dh, mh, xh) -> bool:
    return bool(dg & dh) or (_abstain_ok(dg, mg, xg) and _abstain_ok(dh, mh, xh))


def rule_equality(dg, dh) -> bool:
    return dg == dh


def brute_localisable3(ta: Truth3, tb: Truth3) -> bool:
    return any(localised(ta, v) and localised(tb, v) for v in all_verdicts3())


def rule_localisation(da, db) -> bool:
    return bool(da) and da == db


def all_worlds3():
    """Every adjudicable three-party world: each party honest, mistaken or dishonest."""
    for states in product(State, repeat=len(PARTIES)):
        yield Truth3(tuple(zip(PARTIES, states)))


def exhaustive_rule_check() -> list[str]:
    """Both boundary rules against brute force on every pair of adjudicable
    three-party worlds, not only on the pairs the corpus contains."""
    errs = []
    for ta, tb in product(all_worlds3(), repeat=2):
        if rule_intersection(ta.diverges, ta.mistaken, ta.dishonest,
                             tb.diverges, tb.mistaken, tb.dishonest) != brute_escapable3(ta, tb):
            errs.append(f"world pair {ta.states}/{tb.states}: intersection rule disagrees "
                        f"with brute force")
        if rule_localisation(ta.diverges, tb.diverges) != brute_localisable3(ta, tb):
            errs.append(f"world pair {ta.states}/{tb.states}: localisation rule disagrees "
                        f"with brute force")
    return errs


def _single_divergence(t: Truth3) -> bool:
    return len(t.diverges) <= 1


def _abstain_both(ta: Truth3, tb: Truth3) -> bool:
    return (_abstain_ok(ta.diverges, ta.mistaken, ta.dishonest)
            and _abstain_ok(tb.diverges, tb.mistaken, tb.dishonest))


def coincidence_check() -> list[str]:
    """Where the equality rule (findings/12) and the intersection rule agree.

    They agree on every pair of adjudicable worlds in which each world has at
    most one diverging party, apart from pairs where abstention is correct in
    both worlds. They can disagree as soon as one world has two diverging
    parties, and that already happens with the intermediary honest, i.e. with
    only two parties active. So the condition under which finding 12's rule is
    exact is single divergence, not two parties. Also pinned: every published
    two-party twin pair is single-divergence, which is why finding 12 was never
    contradicted.
    """
    errs = []
    split_two_active = False
    for ta, tb in product(all_worlds3(), repeat=2):
        brute = brute_escapable3(ta, tb)
        eq = rule_equality(ta.diverges, tb.diverges)
        if _single_divergence(ta) and _single_divergence(tb) and not _abstain_both(ta, tb):
            if eq != brute:
                errs.append(f"world pair {ta.states}/{tb.states}: single divergence, "
                            f"but equality rule disagrees with brute force")
        i_honest = all(dict(t.states)[PARTIES[1]] is State.HONEST for t in (ta, tb))
        if i_honest and eq != brute and not _abstain_both(ta, tb):
            split_two_active = True
    if not split_two_active:
        errs.append("expected a two-active-party pair (I honest) where the equality rule "
                    "and brute force disagree; the coincidence claim needs rewording")
    errs.extend(_two_party_pairs_single_divergence())
    return errs


def _two_party_pairs_single_divergence() -> list[str]:
    from ..reporting.harness import load_corpus as load2
    from ..validation.conservation import classify as classify2
    errs = []
    for guilty, honest, _verdict, dg, dh in classify2(load2()):
        if len(dg) > 1 or len(dh) > 1:
            errs.append(f"two-party {guilty}/{honest}: a world has more than one diverging "
                        f"party; finding 12's equality rule is not guaranteed there")
    return errs


def _truth_of(scenarios, h) -> Truth3:
    ts = {Truth3.from_scenario(s) for s in scenarios if s["h_class"] == h}
    if len(ts) != 1:
        raise AssertionError(f"{h}: inconsistent ground truth across instances")
    return next(iter(ts))


def classify(scenarios):
    """For every derived twin pair: (a, b, protocols, brute, intersection, equality, Da, Db)."""
    rows = []
    for (a, b), protos in sorted(derive_twins(scenarios).items()):
        ta, tb = _truth_of(scenarios, a), _truth_of(scenarios, b)
        brute = brute_escapable3(ta, tb)
        inter = rule_intersection(ta.diverges, ta.mistaken, ta.dishonest,
                                  tb.diverges, tb.mistaken, tb.dishonest)
        eq = rule_equality(ta.diverges, tb.diverges)
        rows.append((a, b, protos, brute, inter, eq, ta.diverges, tb.diverges))
    return rows


def two_party_rule_check() -> list[str]:
    """The intersection rule must also reproduce brute force on every two-party
    twin pair, and agree there with the equality rule findings/12 states --
    otherwise the generalisation contradicts the published result."""
    from ..model.types import GroundTruth, Party, PartyState
    from ..model.types import Verdict as V2
    from ..model.types import VerdictStatus as S2
    from ..reporting.harness import load_corpus as load2
    from ..scoring.scorer import score as score2
    from ..validation.conservation import classify as classify2

    scs = load2()

    def truth(m):
        return next(GroundTruth.from_scenario(s) for s in scs if s["m_class"] == m)

    verdicts = [V2(), V2(detected=True, status=S2.SUSPECTED)]
    for b in (Party.P, Party.E, Party.BOTH, Party.J):
        verdicts.append(V2(detected=True, blamed=b, status=S2.EXPOSED))
    for k in range(1, 4):
        for c in combinations((Party.P, Party.E, Party.J), k):
            verdicts.append(V2(detected=True, contradicted=tuple(c), attributes_fault=False,
                               status=S2.CONTRADICTED))

    errs = []
    for guilty, honest, verdict, dg, dh in classify2(scs):
        tg, th = truth(guilty), truth(honest)
        brute = any(score2(tg, v) in SUCCESS_OUTCOMES and score2(th, v) in SUCCESS_OUTCOMES
                    for v in verdicts)

        def parts(t):
            d = frozenset(t.diverges)
            m = frozenset(t.mistaken)
            x = frozenset() if t.dishonest_party is Party.NONE else frozenset({t.dishonest_party})
            return d, m, x

        dg_, mg, xg = parts(tg)
        dh_, mh, xh = parts(th)
        inter = rule_intersection(dg_, mg, xg, dh_, mh, xh)
        if inter != brute:
            errs.append(f"two-party {guilty}/{honest}: intersection rule {inter}, brute {brute}")
        if (verdict == "escapable") != brute:
            errs.append(f"two-party {guilty}/{honest}: findings/12 says {verdict}, brute {brute}")
        _ = PartyState
    return errs


def solved_both(scenarios, reps, a, b, protos) -> list[str]:
    out = []
    for name in sorted(protos):
        rep = reps[name][0]
        ca, cb = rep.per_class[a], rep.per_class[b]
        if ca.correct == ca.n and cb.correct == cb.n:
            out.append(name)
    return out


def check(scenarios=None, reps=None) -> tuple[list[tuple], list[str]]:
    from .harness import reports
    scenarios = scenarios or load_corpus()
    reps = reps or reports(scenarios)
    rows = classify(scenarios)
    errs = list(twin_audit(scenarios))
    for a, b, protos, brute, inter, _eq, da, db in rows:
        if inter != brute:
            errs.append(f"{a}/{b}: intersection rule says {inter}, brute force {brute}")
        loc = brute_localisable3(_truth_of(scenarios, a), _truth_of(scenarios, b))
        if rule_localisation(da, db) != loc:
            errs.append(f"{a}/{b}: localisation rule says {rule_localisation(da, db)}, "
                        f"brute force {loc}")
        both = solved_both(scenarios, reps, a, b, protos)
        if not brute and both:
            errs.append(f"{a}/{b}: binding pair solved in both worlds by {both} -- "
                        f"something reads outside the view")
    errs.extend(two_party_rule_check())
    errs.extend(exhaustive_rule_check())
    errs.extend(coincidence_check())
    return rows, errs


def main():
    from .harness import reports
    scs = load_corpus()
    reps = reports(scs)
    rows, errs = check(scs, reps)

    print("=" * 96)
    print("THREE-PARTY TWINS AND THE CONSERVATION BOUNDARY")
    print("=" * 96)
    print(f"\n  {'pair':<8}{'D(a)':<9}{'D(b)':<9}{'twin under spec':<24}"
          f"{'brute':<8}{'D&D':<8}{'D==D':<8}solved both by")
    for a, b, protos, brute, inter, eq, da, db in rows:
        both = solved_both(scs, reps, a, b, protos)
        specs = ",".join(sorted({PROTOCOLS3[n].spec_name for n in protos}))
        print(f"  {a + '/' + b:<8}{fmt(da):<9}{fmt(db):<9}{specs:<24}"
              f"{'esc' if brute else 'binds':<8}{'esc' if inter else 'binds':<8}"
              f"{'esc' if eq else 'binds':<8}{', '.join(both) or '-'}")

    disagree = [(a, b) for a, b, _p, brute, _i, eq, _da, _db in rows if eq != brute]
    print()
    if disagree:
        print("  The two-party equality rule disagrees with brute force on: "
              + ", ".join(f"{a}/{b}" for a, b in disagree))
        print("  The intersection rule reproduces brute force on every pair, two-party")
        print("  and three-party. Equality is exact only while each world has at most")
        print("  one diverging party (abstention-in-both aside).")
    if errs:
        print("\n  GATE FAILURES:")
        for e in errs:
            print(f"    {e}")
        raise SystemExit("MULTIHOP BOUNDARY: failed")
    print("\n  both rules (escapable iff D&D, localisable iff D==D and non-empty) match")
    print("  brute force on every pair of adjudicable three-party worlds (729 pairs)")
    print("  equality and intersection agree on every single-divergence pair and split")
    print("  on two-divergence pairs even with I honest; every two-party twin pair is")
    print("  single-divergence")
    print("  twins match their declaration; boundary holds on every derived pair")


if __name__ == "__main__":
    main()
