"""
Minimal commitment sets -- T4 inverted into a construction.

T4 was used as a diagnostic: given a protocol, which dishonest acts are
attributable? Inverting it makes it a design problem.

  A dishonest act is BINDABLE iff performing it requires contradicting a
  commitment the party made at or before the act -- turning an assertion
  ("I only granted X") into a concealment ("this signed record says otherwise").

  A dishonest act is RESIDUAL iff no commitment can do this.

CORRECTION (RC-H12, 11 August 2026). That criterion was evaluated PER CLASS,
and it is wrong per class. C_retain -- "produce your record on demand" -- does
force M19 and M20 into contradiction, and B17 implements exactly that. Measured
one class at a time, they are bindable and the residual claim below was false.

But B17 pays for M19 with M10, and for M20 with M21: it contradicts the honest
twin at the same rate, because non-production is a one-bit signal that both
worlds emit. Bindability has to be evaluated on the TWIN PAIR:

  BINDABLE     some commitment forces the act into contradiction WITHOUT
               contradicting its evidentially identical honest twin
  RESIDUAL     no commitment does

Under the pairwise criterion the residual entries below are correct again, and
for a sharper reason than the one originally given. This is the conservation
boundary of docs/findings/12-conservation-boundary.md arriving from the other
direction: a class is bindable exactly when its pair is ESCAPABLE, i.e. when
D(guilty) == D(honest). The minimal-commitment-set analysis and the conservation
boundary are the same result stated in two vocabularies.

The question this module answers:

  Given a set of dishonest behaviours, what is the SMALLEST set of commitments
  such that every one becomes concealment-requiring rather than assertional?

And the conjecture it tests:

  Is the residual empty? If not, attribution has a floor independent of
  protocol design -- a stronger impossibility than T1.
"""

# ---------------------------------------------------------------------------
# Commitment vocabulary. Each entry: what the party binds itself to, and WHEN
# it can be made. The "when" is the crux: a commitment can only bind facts
# that exist, or are foreseeable, at commitment time.
# ---------------------------------------------------------------------------

COMMITMENTS = {
    "C_auth":    ("principal signs the granted scope",              "at grant"),
    "C_exec":    ("executor signs its execution record",            "at execution"),
    "C_recv":    ("principal signs acknowledgement of delivery",    "at delivery"),
    "C_retain":  ("executor commits to producing its record on demand", "at grant"),
    "C_key":     ("per-run short-term irrevocable key certificate", "at grant"),
    # NOTE: C_hist is NOT a commitment in the T4 sense. It is an ADJUDICATOR-side
    # observation, not something the party bound itself to. A party cannot
    # contradict a record it never made. Retained for contrast; see T10.
    "C_hist":    ("adjudicator retains cross-dispute history",      "continuous (not party-made)"),
    "C_witness": ("messages carry public correctness witnesses",    "per message"),
}

# ---------------------------------------------------------------------------
# For each dishonest act: which commitment, if held, forces the liar to
# CONTRADICT it rather than merely assert. None => residual under this
# vocabulary.
# ---------------------------------------------------------------------------

BINDING = {
    "M1":  (["C_exec", "C_auth"], "overreach contradicts the signed scope + signed record"),
    "M2":  (["C_exec"],           "claimed action absent from its own signed record"),
    "M3":  (["C_auth"],           "altered authorization fails the principal's signature"),
    "M4":  (["C_exec"],           "altered record fails its own signature"),
    "M5":  (["C_auth"],           "repudiation contradicts a signature it made"),
    "M6":  (["C_auth"],           "narrowed scope contradicts the signed grant"),
    "M7":  (["C_recv"],           "denial contradicts its own acknowledgement"),
    "M8":  (["C_auth"],           "fabricated grant carries no valid signature"),
    "M9":  (["C_auth"],           "altered copy fails verification"),
    "M11": (["C_auth"],           "both assertions contradict the same signed grant"),
    "M12": (["C_auth"],           "the missing commitment IS the problem; adding it resolves"),
    "M13": (["C_auth"],           "baseless probe refuted by the committed scope"),
    "M14": (["C_witness"],        "public transcript recomputes against the verdict"),
    "M18": (["C_auth", "C_exec"], "mixed case; both commitments needed"),


    # --- residual: no party-made commitment can bind these -------------------
    # Residual PAIRWISE: a commitment reaches the act, but only by convicting
    # the honest twin with it. See the correction in the module docstring.
    "M20": (None, "claims a RATE of misfortune. C_retain forces the claim into "
                  "contradiction (B17 does this), but contradicts M21 -- genuine "
                  "repeated loss -- at the same rate. No single commitment fixes a "
                  "statistical property of a party's own future behaviour, and "
                  "the adjudicator's retained history is its own observation, "
                  "not something the party bound itself to. Confirmed by T7: "
                  "statefulness converts the miss into a false accusation "
                  "rather than binding anything."),
    "M19": (None, "claims the record is UNAVAILABLE. C_retain forces this into "
                  "contradiction -- non-production of a commitment the "
                  "counterparty holds is itself observable, and B17 exploits it. "
                  "But the same act convicts M10, where the loss is genuine. "
                  "Bindable per class, residual per pair."),
    "M24": (None, "executor guilty, attestor's own record unavailable. C_retain "
                  "reaches it (B17) at the cost of M25, the genuine outage. "
                  "Relocating the commitment to a third party relocates the pair "
                  "with it; see findings/08-relocation.md."),
    "M26": (None, "principal-side mirror of M19: alters its stored authorization, "
                  "then declines to produce it. C_retain applies symmetrically and "
                  "so does the cost -- M27, genuine loss, is convicted with it."),
    "M28": (None, "principal-side mirror of M20. Same pairwise structure as "
                  "M20/M21, with M29 as the twin that pays."),
    "M30": (None, "executor acts, then ABORTS before sending the execution "
                  "receipt. C_witness binds messages that are SENT; a message "
                  "never sent carries no witness, so the principal holds no "
                  "commitment over the execution at all. Reachable only by "
                  "disclosing the record itself -- an abort hides the "
                  "commitment, not the contents -- and its twin M31 (lost in "
                  "transit) is convicted with it under commitment-only "
                  "adjudication. This is the fairness gap C_witness leaves open "
                  "and is what a fair-exchange protocol exists to close."),
    "M32": (None, "principal receives, then ABORTS before acknowledging. Mirror "
                  "of M30 on the delivery leg: the executor holds no receipt. "
                  "B13 and B17 reach it, at the cost of M33."),
    "M22": (None, "claims KEY COMPROMISE. A party cannot pre-commit that its key "
                  "will not be stolen -- the event postdates all commitments. "
                  "C_key bounds the WINDOW but does not make the claim false."),
}

# Honest / control classes: nothing to bind.
NON_ADVERSARIAL = {"M0", "M10", "M15", "M16", "M17", "M21", "M23", "M25",
                   "M27", "M29", "M31", "M33"}


def minimal_cover():
    """Smallest commitment set covering every bindable act (greedy set cover;
    the instance is small enough that greedy is exact here)."""
    need = {m: set(v[0]) for m, v in BINDING.items() if v[0]}
    chosen, remaining = [], dict(need)
    while remaining:
        counts = {}
        for reqs in remaining.values():
            for c in reqs:
                counts[c] = counts.get(c, 0) + 1
        # pick the commitment closing the most acts outright
        best = max(counts, key=lambda c: (
            sum(1 for r in remaining.values() if r <= set(chosen) | {c}), counts[c]))
        chosen.append(best)
        remaining = {m: r for m, r in remaining.items() if not r <= set(chosen)}
    return chosen


def residual():
    """Classes no commitment binds WITHOUT convicting the honest twin.

    Pairwise, not per class -- see the correction in the module docstring.
    """
    return {m: v[1] for m, v in BINDING.items() if v[0] is None}


def bindable_per_class():
    """Classes some commitment reaches when the twin is ignored. Strictly larger
    than the bindable set, and the difference IS the conservation cost."""
    from .validation.conservation import PAIRS  # noqa: F401  (documentation link)
    return set(BINDING) - set(residual())
