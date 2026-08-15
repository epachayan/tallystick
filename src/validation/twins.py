"""Twin audit.

An evidential twin pair is a mistake class and its malicious counterpart,
generated from the same underlying scope and actions so that the ONLY difference
is intent. The claim the whole mistake-vs-malice line rests on is that the two
are indistinguishable to the adjudicator.

That claim is now testable rather than asserted: project both under each
disclosure policy and compare fingerprints. If a pair diverges, the corpus is
not producing real twins and every conclusion drawn from the pair is void.
"""

from __future__ import annotations

from ..model.evidence import DisclosurePolicy, build_view

#: mistake class -> malicious class, with the status the audit must reproduce.
#:
#:   "twin"          indistinguishable; a divergence here is a corpus bug
#:   "not_twin"      known asymmetry, with the reason. Asserted as a twin by
#:                   generator.TWIN_OF, which is wrong and stays recorded here.
PAIRS = (
    ("M15", "M6",  "twin",     "principal misremembers scope / lies about scope"),
    ("M16", "M1",  "not_twin", "M1 CONCEALS the out-of-scope action, M16 admits it. "
                               "The evidence differs by construction, so this pair "
                               "never tested intent. generator.TWIN_OF still claims it."),
    ("M17", "M7",  "twin",     "misremembers delivery / denies receipt"),
    ("M10", "M19", "twin",     "genuine record loss / tamper-then-claim-loss"),
    ("M21", "M20", "twin",     "genuine repeated loss / repeated loss as cover"),
    ("M23", "M22", "twin",     "thief used the key / false compromise claim"),
    ("M25", "M24", "twin",     "genuine attestor outage / guilty executor, attestor down"),
    # symmetric-withholding twins (RC-H9): the principal-side mirrors of
    # M10/M19 and M21/M20.
    ("M27", "M26", "twin",     "principal genuinely loses its copy / tampers then claims loss"),
    ("M29", "M28", "twin",     "principal genuine repeated loss / repeated loss as cover"),
    # abort twins (RC-H7)
    # An abort denies the counterparty the COMMITMENT, not the contents. So the
    # pair is indistinguishable only where contents are withheld anyway. Under
    # full disclosure the overreach is plainly visible in the execution record:
    # aborting buys the executor nothing against an adjudicator who can read it.
    ("M31", "M30", "twin_commitment_only",
     "execution receipt lost in transit / executor aborts to hide overreach"),
    ("M33", "M32", "twin",     "acknowledgement lost in transit / principal aborts to deny receipt"),
)

#: Pairs indistinguishable ONLY under commitment-only disclosure with padding.
#: Not a weaker twin -- a precise one: the mechanism they probe (abort) hides a
#: commitment rather than a record.
COMMITMENT_ONLY_TWINS = {("M31", "M30")}

#: Pairs the cardinality-binding commitment separates, and which padding restores.
#: Recorded rather than silently tolerated: this is a finding, not a fixture.
CARDINALITY_SENSITIVE = {("M10", "M19"), ("M21", "M20")}

PAD_TO = 8


def audit(scenarios, policies=(DisclosurePolicy.FULL, DisclosurePolicy.COMMITMENT_ONLY),
          pad_to=None):
    """Returns [(mistake, malicious, policy, matched, total, status)] using the
    OBSERVABLE fingerprint: commitment roots redacted, because a root is opaque
    to the adjudicator and differing roots are not by themselves a distinguisher."""
    by_class: dict[str, list[dict]] = {}
    for s in scenarios:
        by_class.setdefault(s["m_class"], []).append(s)

    rows = []
    for a, b, status, _why in PAIRS:
        for policy in policies:
            xs, ys = by_class.get(a, []), by_class.get(b, [])
            n = min(len(xs), len(ys))
            matched = 0
            for i in range(n):
                va, _ = build_view(xs[i], policy, pad_to=pad_to)
                vb, _ = build_view(ys[i], policy, pad_to=pad_to)
                matched += va.observable_fingerprint() == vb.observable_fingerprint()
            rows.append((a, b, policy.value, matched, n, status))
    return rows


def main():
    from ..reporting.harness import load_corpus

    scs = load_corpus()
    width = 9
    failures = []

    for label, pad in (("unpadded commitments", None), (f"padded to {PAD_TO}", PAD_TO)):
        print(f"\n  -- {label} --")
        for a, b, policy, matched, n, status in audit(scs, pad_to=pad):
            indistinguishable = matched == n
            if status == "twin_commitment_only":
                expected_twin = (policy == "commitment_only" and pad is not None)
            else:
                expected_twin = status == "twin"
            note = ""
            if expected_twin and not indistinguishable:
                if (a, b) in CARDINALITY_SENSITIVE and pad is None:
                    note = "separated by committed cardinality"
                else:
                    note = "UNEXPECTED"
                    failures.append((a, b, policy, label))
            elif not expected_twin and indistinguishable:
                note = "UNEXPECTED: declared not-twin but indistinguishable"
                failures.append((a, b, policy, label))
            elif not expected_twin:
                note = ("contents visible: abort hides the commitment, not the record"
                        if status == "twin_commitment_only"
                        else "known asymmetry (concealment)")
            print(f"  {a + '/' + b:<{width}}  {policy:<17}  {matched}/{n}  {note}")

    if failures:
        for f in failures:
            print("  FAIL", f)
        raise SystemExit(f"TWINS: {len(failures)} unexpected result(s)")
    print("\ntwins: all pair/policy combinations match their recorded status")


if __name__ == "__main__":
    main()
