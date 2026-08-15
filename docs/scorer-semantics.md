# Scorer semantics

Canonical branch order, fixed:

1. world unadjudicable
2. world has no divergence
3. verdict attributes fault
4. verdict asserts contradiction
5. otherwise `missed`

The world is classified before the verdict is read. `src/scoring/scorer.py` is a
pure function of `(GroundTruth, Verdict)`; its signature admits no protocol
argument, which is how property P8 is enforced rather than asserted.

The enumerated state space is pinned by a SHA-256 snapshot in
`tests/test_scorer.py`. Changing any cell breaks that test on purpose.

## Label set

| reality | verdict | outcome |
|---|---|---|
| dishonest party, adjudicable | names that party | `correct_blame` |
| dishonest party, adjudicable | names another party, or `both` when one is guilty | `false_accusation` |
| party diverged by MISTAKE | names that party | `over_attribution` |
| divergence present | contradiction ⊆ divergence, no attribution | `correct_contradiction` |
| no divergence | abstains | `correct_abstain` |
| no divergence | unexplained hard flag | `spurious` |
| unadjudicable | abstains | `correct_abstain_amb` |
| unadjudicable | names a party | `unsupported_blame` |
| any | asserts a contradiction ground truth does not support | `false_contradiction` |
| adjudicable misconduct | abstains | `missed` |

`over_attribution` and `spurious` are the project's own labels, carried forward.
`unsupported_blame` and `false_contradiction` are additions covering
combinations the findings table leaves undefined — see OPEN-1 and OPEN-2.

## Precedence

A verdict that both names a party and asserts a contradiction is judged on the
naming. Attribution is the act that carries false-accusation risk, so a
mechanism cannot hedge by attaching a correct contradiction to a wrong blame.

Contradiction is scored on subset, not equality: `contradicted ⊆ diverges` and
non-empty. Proving one divergence is a real result even when several exist.

## Masking guard

A mistaken co-party must not mask a genuine wrongdoer. In a mixed world
(principal misremembers, executor actually cheats — M18's structure) a mechanism
that blames nobody scores `missed`, not `correct_abstain`. This was found by the
v0.9 scorer audit's property P3 and is preserved;
`test_mixed_world_masking_guard` pins it.

---

## Open decisions — your call

### OPEN-1 — unadjudicable world, mechanism names a party

Chosen: `unsupported_blame`, aggregated into the false-attribution rate.

In an unadjudicable world no attribution is evidence-supported, so naming a
party is a failure even when the guess happens to be right. Calling it
`false_accusation` is factually wrong on a lucky guess; calling it
`correct_blame` rewards guessing.

### OPEN-2 — contradiction asserted where ground truth has none

Chosen: `false_contradiction`, tracked separately from false attribution.

Without it, a non-attributive mechanism has no way to be wrong except by
abstaining — which would quietly rig T6 (non-attributive dominance) in its own
favour. Rolling it into `false_accusation` overstates the harm, since nobody was
named.

### OPEN-3 — RESOLVED 11 August 2026

Resolved as a **coherence invariant, not a new label.** A dishonest party that
leaves no observable divergence produces a world where abstaining is correct, so
the corpus must mark it unadjudicable and it scores `correct_abstain_amb`. No
world can now score as a success merely because it was invisible.

Adding the rule immediately found two gaps in the divergence model itself: a
baseless complaint (M13) and an unsigned fabricated grant (M8) are both
observable, and neither was being counted. Enforced by
`src/validation/coherence.py`.

Original wording follows.

### OPEN-3 — dishonest party, zero divergence, adjudicable

The findings table says `no divergence → abstain → correct_abstain`, and that is
what the code does. But this is a party that behaved dishonestly and produced no
observable divergence, which is arguably `missed`.

This bears directly on T8: if these count as successes, ambiguity is scored as
resolved when it was merely invisible. The cardinality result (F-H1) sharpens
the question — some worlds previously assumed to produce no observable
divergence do produce one, in the committed leaf count.

I followed your document rather than overriding it. Flagging because the miss
rate of every class modelling undetectable misconduct turns on it.
