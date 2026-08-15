"""Derive-and-diff for the last four hand-maintained declarations (RC-H12).

Four declarations have now been audited this way and four were wrong:

    TWIN_OF          M16/M1 declared a twin; M1 conceals, M16 admits (F-H3)
    withholding      modelled for the executor only, 0/650 for the principal (RC-H9)
    "M22 residual"   true of the commitment-only family, not of every mechanism (RC-H10)
    protocol set     B4 uncited because a real result was never written down (RC-H14)

These are the four that remain. Each is derived from the corpus or the code and
diffed against what the declaration says. A disagreement is not automatically a
defect in the declaration -- twice now the derivation has been the thing that was
wrong -- so each check reports the disagreement and names which side to inspect.

    PRINCIPAL_LIAR    generator.py -- classes where the principal is dishonest
    mutation_family   generator.py -- the family label on every scenario
    ENTITLEMENTS      evidence.py  -- which protocols see beyond the base view
    BINDING/RESIDUAL  commitments.py -- which acts a commitment can bind
"""

from __future__ import annotations

from ..model.evidence import DisclosurePolicy, build_view
from ..model.types import GroundTruth, Party
from ..protocols.baselines import PROTOCOLS


# ---------------------------------------------------------------------------
# 1. PRINCIPAL_LIAR
# ---------------------------------------------------------------------------

def audit_principal_liar(scenarios) -> list[str]:
    """Derived: every class whose ground truth names the principal as dishonest.

    The declaration drives F01, the project's most durable empirical claim, so a
    class missing from it means the regression is being measured on a subset.
    """
    from ..generator import (
        PRINCIPAL_DISHONEST,
        PRINCIPAL_LIAR,
        PRINCIPAL_LIAR_BOTH,
        PRINCIPAL_LIAR_NON_ASSERTIONAL,
    )

    derived = {s["m_class"] for s in scenarios
               if s["ground_truth"]["dishonest_party"] in ("P", "both")}
    errs = []
    if derived != PRINCIPAL_DISHONEST:
        errs.append(f"PRINCIPAL_DISHONEST is {sorted(PRINCIPAL_DISHONEST, key=_k)} but the "
                    f"corpus gives {sorted(derived, key=_k)}")

    # The three subsets must partition it -- no class may be silently dropped
    # from the F01 accounting, which is what the original single set allowed.
    union = PRINCIPAL_LIAR | PRINCIPAL_LIAR_NON_ASSERTIONAL | PRINCIPAL_LIAR_BOTH
    if union != PRINCIPAL_DISHONEST:
        errs.append(f"the three principal-liar subsets do not cover "
                    f"PRINCIPAL_DISHONEST; missing {sorted(PRINCIPAL_DISHONEST - union, key=_k)}")
    for a, b in (("PRINCIPAL_LIAR", PRINCIPAL_LIAR),
                 ("PRINCIPAL_LIAR_NON_ASSERTIONAL", PRINCIPAL_LIAR_NON_ASSERTIONAL),
                 ("PRINCIPAL_LIAR_BOTH", PRINCIPAL_LIAR_BOTH)):
        for c, d in (("PRINCIPAL_LIAR", PRINCIPAL_LIAR),
                     ("PRINCIPAL_LIAR_NON_ASSERTIONAL", PRINCIPAL_LIAR_NON_ASSERTIONAL),
                     ("PRINCIPAL_LIAR_BOTH", PRINCIPAL_LIAR_BOTH)):
            if a < c and b & d:
                errs.append(f"{a} and {c} overlap on {sorted(b & d, key=_k)}")

    # BOTH classes must really have both parties dishonest.
    for m in PRINCIPAL_LIAR_BOTH:
        states = {(s["ground_truth"]["p_state"], s["ground_truth"]["e_state"])
                  for s in scenarios if s["m_class"] == m}
        if not all(e == "dishonest" for _p, e in states):
            errs.append(f"{m} is in PRINCIPAL_LIAR_BOTH but its executor is not dishonest")
    return errs


def _k(m):
    return int(m[1:])


# ---------------------------------------------------------------------------
# 2. mutation_family
# ---------------------------------------------------------------------------

#: What each family asserts about the world, as a predicate on the scenario.
#: Derived from the family NAME, which is the point: a label that does not
#: describe its members is worse than no label.
FAMILY_PREDICATES = {
    "control": lambda s: s["ground_truth"]["dishonest_party"] == "none"
                         and s["p_view"]["record_available"]
                         and s["e_view"]["record_available"],
    "record_tampering": lambda s: (not s["p_view"]["record_intact"]
                                   or not s["e_view"]["record_intact"]),
    "benign_divergence": lambda s: s["ground_truth"]["dishonest_party"] == "none",
    "no_commitment": lambda s: not s["authorization"]["committed"],
    "mistake": lambda s: "mistaken" in (s["ground_truth"]["p_state"],
                                        s["ground_truth"]["e_state"]),
    "pattern_abuse": lambda s: _has_history(s),
    "pattern_benign": lambda s: _has_history(s)
                                and s["ground_truth"]["dishonest_party"] == "none",
    "excuse_abuse": lambda s: s["key_claim"]["revoked"],
    "excuse_benign": lambda s: s["key_claim"]["revoked"]
                               and s["ground_truth"]["dishonest_party"] == "none",
    "attestor_abuse": lambda s: s["attestor"]["present"],
    "attestor_benign": lambda s: s["attestor"]["present"]
                                 and s["ground_truth"]["dishonest_party"] == "none",
    "abort_abuse": lambda s: not (s["chain"]["exec_receipt_sent"]
                                  and s["chain"]["delivery_ack_sent"]),
    "abort_benign": lambda s: not (s["chain"]["exec_receipt_sent"]
                                   and s["chain"]["delivery_ack_sent"])
                              and s["ground_truth"]["dishonest_party"] == "none",
    "adjudicator_abuse": lambda s: s["adjudicator"]["colluding"],
    "query_abuse": lambda s: s["p_view"]["disputed_action"] is not None,
    "mixed": lambda s: "mistaken" in (s["ground_truth"]["p_state"],
                                       s["ground_truth"]["e_state"])
                       and s["ground_truth"]["dishonest_party"] != "none",
    "behavioural": lambda s: True,     # the catch-all; asserts nothing
}


def _has_history(s):
    h = s.get("history", {})
    return any(v for k, v in h.items() if k.endswith("_disputes"))


def audit_mutation_family(scenarios) -> list[str]:
    """Every scenario must satisfy the predicate its family label implies."""
    errs = []
    bad: dict[str, set[str]] = {}
    for s in scenarios:
        fam = s["mutation_family"]
        pred = FAMILY_PREDICATES.get(fam)
        if pred is None:
            bad.setdefault(f"{fam}: no predicate defined", set()).add(s["m_class"])
            continue
        if not pred(s):
            bad.setdefault(f"{fam}: label does not hold", set()).add(s["m_class"])
    for msg, classes in sorted(bad.items()):
        errs.append(f"mutation_family {msg} for {sorted(classes, key=_k)}")
    return errs


# ---------------------------------------------------------------------------
# 3. ENTITLEMENTS
# ---------------------------------------------------------------------------

def audit_entitlements(scenarios) -> list[str]:
    """An entitlement is a declared trust assumption. Two failure modes:

      UNDECLARED  a protocol's view differs from the base view without one
      UNUSED      a protocol declares one that changes nothing it can see

    Both matter. The first is a hidden assumption; the second is an assumption
    charged against a mechanism that does not rely on it.
    """
    errs = []
    sample = list({s["m_class"]: s for s in scenarios}.values())
    for name, proto in PROTOCOLS.items():
        for sc in sample:
            base, _ = build_view(sc, proto.policy, frozenset())
            with_ent, _ = build_view(sc, proto.policy, proto.entitlements)
            differs = base.fingerprint() != with_ent.fingerprint()
            if differs and not proto.entitlements:
                errs.append(f"{name}: view differs from the base view with no "
                            f"entitlement declared ({sc['m_class']})")
                break
            if proto.entitlements and differs:
                break
        else:
            if proto.entitlements:
                errs.append(f"{name}: declares {sorted(proto.entitlements)} but its view "
                            f"is identical to the base view on every class -- the "
                            f"assumption is charged and unused")
    return errs


# ---------------------------------------------------------------------------
# 4. BINDING / RESIDUAL in commitments.py
# ---------------------------------------------------------------------------

def audit_commitments(scenarios, reps) -> list[str]:
    """The declaration says which acts a commitment can force into concealment,
    and which are RESIDUAL. Derived test: a class declared residual should be
    unreachable by mechanisms holding the relevant commitments; a class declared
    bindable should be reachable by some mechanism.
    """
    from ..commitments import BINDING, residual

    errs = []
    declared_residual = set(residual())
    dishonest_classes = {s["m_class"] for s in scenarios
                         if s["ground_truth"]["dishonest_party"] != "none"}

    # PAIRWISE criterion (RC-H12): a class is bindable only if some mechanism
    # solves it WITHOUT convicting its evidentially identical honest twin.
    from ..validation.conservation import classify

    twin_of = {g: h for g, h, _v, _dg, _dh in classify(scenarios)}

    from ..validation.conservation import views_identical

    def solved_with_twin(m):
        t = twin_of.get(m)
        for name, r in reps.items():
            c = r.per_class[m]
            if c.correct != c.n:
                continue
            if t is None:
                return True
            # An ENTITLED protocol sees more than the base view, so the pair is
            # not a twin for it and it is not evidence that a commitment bound
            # the act. Its cost is the assumption, which this module cannot price.
            if not views_identical(scenarios, m, t, PROTOCOLS[name]):
                continue
            tc = r.per_class[t]
            if tc.correct == tc.n:
                return True
        return False

    solved_by_some = {m for m in dishonest_classes if solved_with_twin(m)}

    wrongly_residual = declared_residual & solved_by_some
    if wrongly_residual:
        errs.append(f"commitments.py calls {sorted(wrongly_residual, key=_k)} residual, "
                    f"but some mechanism solves them without convicting the twin")

    declared_bindable = (set(BINDING) - declared_residual) & dishonest_classes
    unreachable = declared_bindable - solved_by_some
    if unreachable:
        errs.append(f"commitments.py calls {sorted(unreachable, key=_k)} bindable, "
                    f"but no mechanism solves them")

    uncovered = dishonest_classes - set(BINDING) - declared_residual
    if uncovered:
        errs.append(f"commitments.py has no entry for dishonest classes "
                    f"{sorted(uncovered, key=_k)}")
    return errs


# ---------------------------------------------------------------------------

def main():
    from ..reporting.harness import load_corpus, reports

    scs = load_corpus()
    reps = reports(scs)

    print("=" * 92)
    print("DECLARATION AUDIT (RC-H12) -- derive, then diff against what is declared")
    print("=" * 92)

    checks = (
        ("PRINCIPAL_LIAR", audit_principal_liar(scs)),
        ("mutation_family", audit_mutation_family(scs)),
        ("ENTITLEMENTS", audit_entitlements(scs)),
        ("commitments.py", audit_commitments(scs, reps)),
    )

    total = 0
    for label, errs in checks:
        print(f"\n-- {label} --")
        if not errs:
            print("   agrees with the derivation")
        for e in errs:
            print(f"   {e}")
        total += len(errs)

    print()
    if total:
        print(f"  {total} disagreement(s). A disagreement is not automatically a defect")
        print("  in the declaration -- twice now the derivation has been the wrong side.")
        print("  Inspect both before changing either.")
        raise SystemExit(f"DECLARATIONS: {total} disagreement(s)")
    print("  all four declarations agree with their derivations")


if __name__ == "__main__":
    main()
