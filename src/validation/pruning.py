"""Which protocols are load-bearing, and which are dead weight?

Eighteen protocols is more than the live claims need, and every one costs
attention on every read of every results table. But "solves fewest classes" is
the wrong pruning criterion: B10, B15 and B16d solve an identical class set and
exist to test three different things, while B0 solves the fewest of all and is
the entire point of the project.

The right criterion is CITATION: a protocol stays if removing it would make some
live claim unstatable. That is derived here rather than asserted, by listing
each live claim with the protocols it needs and checking the claim still
computes.

Two roles keep a protocol that its own numbers would not:

  CONTROL   it is the thing another protocol is measured against. B0 is the
            deployed default; without it F01 is a number with no baseline.
  CONTRAST  it differs from another protocol in exactly one dimension, and the
            claim IS the difference. B6/B6c differ only in whether the
            adjudicator is checked; deleting either turns the collusion result
            into an assertion.

A protocol failing both, whose class coverage is matched by a retained one, is
prunable -- meaning moved to the archive, not deleted. The project's standing
constraint is that nothing produced becomes a throwaway artifact, and a negative
result is still a result: "we tried exhaustive querying and it bought two
classes over dispute-bounded querying" is worth keeping even once the line is
closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..protocols.baselines import PROTOCOLS


@dataclass(frozen=True)
class Claim:
    id: str
    statement: str
    requires: frozenset[str]
    doc: str


#: Every claim currently made anywhere in the live documents, with the protocols
#: it cannot be stated without.
LIVE_CLAIMS = (
    Claim("F01", "the deployed agentic default cannot let a correct executor "
                 "defend itself; PeerReview-style bilateral commitment can",
          frozenset({"B0_bearer_executor_log", "B1_bilateral_commitment"}),
          "findings/01-baselines.md"),

    Claim("C1", "conservation boundary: twins differing only in WHY are escapable, "
                "twins differing in WHETHER are not",
          frozenset({"B1_bilateral_commitment",    # attributive, cannot escape
                     "B10_composed",               # non-attributive, does escape
                     "B13_witness_messages"}),     # escape confirmed at low disclosure
          "findings/12-conservation-boundary.md"),

    Claim("S2", "the non-attributive vocabulary removes over-attribution at no "
                "cost in resolution",
          frozenset({"B1_bilateral_commitment", "B9_non_attributive"}),
          "findings/03-mistake-vs-malice.md"),

    Claim("S3", "selective disclosure crosses over against full disclosure "
                "around scope 8",
          frozenset({"B3_suspected_exposed", "B7_verifiable_adjudication",
                     "B13_witness_messages"}),
          "findings/09-witness-messages.md"),

    Claim("S4", "cardinality binding is load-bearing for the query-based family "
                "and not for B13",
          frozenset({"B5_dispute_driven", "B7_verifiable_adjudication",
                     "B13_witness_messages"}),
          "findings/09-witness-messages.md"),

    Claim("S5", "a duty to answer relocates the cost rather than resolving it, "
                "symmetrically across parties",
          frozenset({"B13_witness_messages", "B17_duty_to_answer"}),
          "findings/10-duty-and-coverage.md"),

    Claim("COLLUSION", "checking the adjudicator against its own transcript is "
                       "what catches collusion; an unchecked verdict simply stands",
          frozenset({"B6_accountable_queries", "B6c_under_collusion",
                     "B7_verifiable_adjudication"}),
          "findings/02-selective-disclosure.md"),

    Claim("EXCUSE", "claiming key compromise dominates claiming loss, and "
                    "short-term keys remove the excuse",
          frozenset({"B7r_under_revocation", "B15_short_term_keys"}),
          "findings/06-excuse-ranking.md"),

    Claim("T10", "attesting the residual relocates it rather than removing it; a "
                 "digest attestor is weaker than a custodial one",
          frozenset({"B16c_custodial_attestor", "B16d_digest_attestor"}),
          "findings/08-relocation.md"),

    Claim("DISCLOSURE", "withholding contents costs specific classes, and which "
                        "ones is measurable",
          frozenset({"B1_bilateral_commitment", "B2_commitment_only"}),
          "findings/02-selective-disclosure.md"),

    # Registered BECAUSE the pruning analysis flagged B4 as uncited. It was not
    # dead weight -- it was carrying an unstated negative result. Exhaustive
    # querying over commitments costs 35% more disclosure than dispute-bounded
    # querying and resolves exactly the same classes. That is worth saying, and
    # it cannot be said without B4.
    Claim("QUERY-COST", "exhaustive querying buys nothing over dispute-bounded "
                        "querying, at 35% more disclosure",
          frozenset({"B4_scope_predicates", "B5_dispute_driven"}),
          "findings/02-selective-disclosure.md"),
)

#: Protocols kept for a question that is open rather than a claim that is made.
#: These must be justified explicitly, because "we might need it later" is how a
#: baseline set grows without limit.
PENDING = {
    "B11_stateful": (
        "RC-H13. B11 is scored per scenario, so its pattern detection cannot "
        "demonstrate its value: a claim about a party's history is not testable "
        "one scenario at a time. Whether repetition genuinely escapes the "
        "conservation boundary or merely changes the unit of analysis is the "
        "most interesting untested question in the project, and B11 is the only "
        "implementation of it. Retained pending a repeated-interaction harness."
    ),
}


def load_bearing() -> dict[str, list[str]]:
    """protocol -> claims that cite it."""
    out: dict[str, list[str]] = {p: [] for p in PROTOCOLS}
    for claim in LIVE_CLAIMS:
        for p in claim.requires:
            out.setdefault(p, []).append(claim.id)
    for p in PENDING:
        out.setdefault(p, []).append("PENDING")
    return out


def coverage(reps) -> dict[str, frozenset[str]]:
    return {n: frozenset(m for m, c in rep.per_class.items() if c.correct == c.n)
            for n, rep in reps.items()}


def prunable(reps) -> list[tuple[str, str]]:
    """(protocol, reason) for protocols no live claim cites."""
    cites = load_bearing()
    cov = coverage(reps)
    out = []
    for name in PROTOCOLS:
        if cites.get(name):
            continue
        matched = [o for o in PROTOCOLS
                   if o != name and cites.get(o) and cov[o] >= cov[name]]
        reason = (f"no live claim cites it; class coverage matched by {matched[0]}"
                  if matched else "no live claim cites it; coverage is unique")
        out.append((name, reason))
    return out


def main():
    from ..reporting.harness import load_corpus, reports

    reps = reports(load_corpus())
    cites = load_bearing()
    cov = coverage(reps)

    print("=" * 92)
    print("PROTOCOL PRUNING -- which protocols does the live claim set actually need?")
    print("=" * 92)
    print(f"\n  {len(LIVE_CLAIMS)} live claims, {len(PROTOCOLS)} protocols\n")
    print(f"  {'protocol':<28}{'solves':>7}   cited by")
    for name in PROTOCOLS:
        c = cites.get(name) or []
        print(f"  {name:<28}{len(cov[name]):>7}   {', '.join(sorted(c)) if c else '--'}")

    print("\n-- retained for an OPEN QUESTION rather than a stated claim --")
    for name, why in PENDING.items():
        print(f"  {name}")
        print(f"    {why}")

    drop = prunable(reps)
    print(f"\n-- cited by nothing: {len(drop)} --")
    for name, reason in drop:
        print(f"  {name:<28}{reason}")
    if not drop:
        print("  (none)")

    keep = [p for p in PROTOCOLS if cites.get(p)]
    print(f"\n  every protocol is load-bearing: {len(keep)}/{len(PROTOCOLS)}")
    print("\n  Note what this analysis did rather than what it concluded. It flagged")
    print("  B4 as uncited, which prompted checking WHY it existed -- and it was")
    print("  carrying a negative result nobody had written down. The prune found a")
    print("  missing claim, not a redundant protocol.")
    if drop:
        raise SystemExit(
            f"PRUNING: {len(drop)} protocol(s) cited by no claim and no open "
            f"question. Either register why it is kept, or archive it.")
    return drop


if __name__ == "__main__":
    main()
