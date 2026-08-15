"""When does conservation of ambiguity bind, and when can it be escaped?

T8 was argued from three observations, each showing a cost move rather than
vanish. This derives the boundary instead, and then checks the derivation
against every protocol and every twin pair in the corpus.

--------------------------------------------------------------------------
The argument
--------------------------------------------------------------------------

An evidential twin pair projects to ONE EvidenceView. Any evidence-determined
mechanism is a function of that view, so it returns ONE verdict for both worlds.
Whether that single verdict can be correct in both is therefore a question about
the SCORER, not about the mechanism:

    Conservation BINDS on a pair when no verdict is correct in both worlds.
    Conservation is ESCAPABLE when some verdict is correct in both.

One structural condition decides it. Write D(w) for the set of parties whose
account diverges from the record in world w:

    D(guilty) == D(honest)   ->  ESCAPABLE
    D(guilty) != D(honest)   ->  BINDS

The reason is short. A non-attributive verdict asserts "these parties' accounts
contradict the record". Its truth value is fixed by D. If the two worlds share a
D, one such verdict is true in both, and a mechanism using that vocabulary
handles the pair. If they differ -- typically one world has D empty, because
nothing diverged at all -- then no assertion about D holds in both, and any
mechanism must be wrong about one of them.

In plainer terms:

    Twins differing only in WHY a divergence happened are escapable.
    Twins differing in WHETHER one happened are not.

Mistake-versus-malice is the first kind: the principal's account contradicts the
record either way, and only the intent behind it differs. Loss-versus-
concealment is the second: in the honest world nothing diverged at all, the
party simply cannot produce a record.

This explains, with no new argument, why the non-attributive vocabulary buys
real resolution on M15/M6 and buys nothing on M10/M19. It was never a general
escape. It is an exact escape from one of the two kinds.

--------------------------------------------------------------------------
What is empirical here and what is not
--------------------------------------------------------------------------

The rule is a theorem about evidence-determined functions; no corpus confirms
it. What the corpus supplies is:

  * a check that the harness obeys it -- a violation means something reads
    outside the view and the visibility invariant missed it
  * which side of the boundary each modelled adversary falls on
  * for binding pairs, which currency each mechanism chooses to pay in

Entitled protocols are excluded per pair: an entitlement widens the view, so the
pair is not a twin FOR THAT PROTOCOL. That is not an escape from conservation,
it is a larger view whose cost is the assumption itself.
"""

from __future__ import annotations

from ..model.evidence import DisclosurePolicy, build_view
from ..model.types import GroundTruth
from ..protocols.baselines import PROTOCOLS
from ..validation.twins import PAIRS

PAD = 8

#: pairs that are twins only under commitment-only disclosure
COMMITMENT_ONLY = {("M30", "M31")}


def divergence_signature(scenarios, m_class) -> frozenset:
    """D(w): which parties' accounts diverge from the record. Constant within a
    class by construction; asserted here rather than assumed."""
    sigs = {frozenset(GroundTruth.from_scenario(s).diverges)
            for s in scenarios if s["m_class"] == m_class}
    if len(sigs) != 1:
        raise AssertionError(f"{m_class} has inconsistent divergence signatures: {sigs}")
    return next(iter(sigs))


def classify(scenarios) -> list[tuple]:
    """Returns (guilty, honest, 'escapable'|'binds', D_guilty, D_honest)."""
    out = []
    for honest, guilty, status, _why in PAIRS:
        if status not in ("twin", "twin_commitment_only"):
            continue
        dg = divergence_signature(scenarios, guilty)
        dh = divergence_signature(scenarios, honest)
        out.append((guilty, honest, "escapable" if dg == dh else "binds", dg, dh))
    return out


def views_identical(scenarios, guilty, honest, proto) -> bool:
    """Evidence-identical FOR THIS PROTOCOL, given its policy and entitlements."""
    if (guilty, honest) in COMMITMENT_ONLY and proto.policy is not DisclosurePolicy.COMMITMENT_ONLY:
        return False
    xs = [s for s in scenarios if s["m_class"] == guilty]
    ys = [s for s in scenarios if s["m_class"] == honest]
    for a, b in zip(xs, ys):
        va, _ = build_view(a, proto.policy, proto.entitlements, pad_to=PAD)
        vb, _ = build_view(b, proto.policy, proto.entitlements, pad_to=PAD)
        if va.observable_fingerprint() != vb.observable_fingerprint():
            return False
    return True


def solved_both(scenarios, reps, guilty, honest) -> list[str]:
    out = []
    for name, proto in PROTOCOLS.items():
        if not views_identical(scenarios, guilty, honest, proto):
            continue
        g, h = reps[name].per_class[guilty], reps[name].per_class[honest]
        if g.correct == g.n and h.correct == h.n:
            out.append(name)
    return out


def _fmt(d) -> str:
    return "{" + ",".join(sorted(p.value for p in d)) + "}" if d else "{}"


def main():
    from ..reporting.harness import load_corpus, reports

    scs = load_corpus()
    reps = reports(scs)
    rows = classify(scs)

    print("=" * 92)
    print("CONSERVATION BOUNDARY -- which twin pairs admit an escape, and which do not")
    print("=" * 92)
    print("\n  D(w) = parties whose account diverges from the record in world w.")
    print("  same D  -> some verdict is true in both worlds -> ESCAPABLE")
    print("  diff D  -> no verdict is true in both          -> BINDS\n")
    print(f"  {'pair':<12}{'D(guilty)':<12}{'D(honest)':<12}verdict")
    for guilty, honest, verdict, dg, dh in rows:
        print(f"  {guilty + '/' + honest:<12}{_fmt(dg):<12}{_fmt(dh):<12}{verdict}")

    print("\n-- prediction check --")
    print(f"  {'pair':<12}{'predicted':<12}{'solved both by':<12}")
    violations = []
    for guilty, honest, verdict, _dg, _dh in rows:
        both = solved_both(scs, reps, guilty, honest)
        print(f"  {guilty + '/' + honest:<12}{verdict:<12}{len(both)} protocols")
        if verdict == "binds" and both:
            violations.append((guilty, honest, both))
        if verdict == "escapable" and not both:
            violations.append((guilty, honest, ["NONE -- escape predicted but unrealised"]))

    print()
    if violations:
        print("  VIOLATION of the derived boundary:")
        for g, h, names in violations:
            print(f"    {g}/{h}: {', '.join(names)}")
        print("  A binding pair solved by an unentitled mechanism means something")
        print("  reads outside the EvidenceView. Investigate before trusting results/.")
        raise SystemExit("CONSERVATION: prediction violated")

    escapable = [r for r in rows if r[2] == "escapable"]
    binding = [r for r in rows if r[2] == "binds"]
    print(f"  boundary holds: {len(binding)} binding pairs, none solved by any "
          f"unentitled mechanism;")
    print(f"                  {len(escapable)} escapable pairs, solved by the "
          f"non-attributive family.")
    print()
    print("  Conservation is therefore NOT universal, and the boundary is sharp:")
    print("  twins differing only in WHY a divergence occurred are escapable, by")
    print("  changing what the verdict claims. Twins differing in WHETHER one")
    print("  occurred are not escapable by any vocabulary.")


if __name__ == "__main__":
    main()
