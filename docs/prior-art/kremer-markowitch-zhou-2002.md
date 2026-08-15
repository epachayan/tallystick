# Reading Note — Kremer, Markowitch & Zhou, *An Intensive Survey of Fair Non-Repudiation Protocols* (Computer Communications 25(17), 2002)

**Read:** 8 August 2026, in full
**Verdict:** the richest of the four reads. Six insights: one retires a parked idea, one
generalises T5 into a stronger claim, one confirms T4's criterion from 2001, and one exposes an
assumption the harness never stated.

---

## K1 — Weak fairness is a verdict state the harness does not have

Their definition: weak fairness ensures that **if one party does not obtain its evidence while
the other did, the disadvantaged party receives a proof of that fact.**

That is a fourth outcome, and it is not in any vocabulary used here:

| vocabulary | states |
|---|---|
| B1 | `{blame, no-blame}` |
| B3–B7 | `{exposed, suspected, clear}` |
| B9–B10 | `{contradicted, unresolved, clear}` |
| **weak fairness** | adds **`imbalance-proven`** — *"I can prove I was disadvantaged"* |

The distinction matters because `imbalance-proven` makes a claim about **outcome asymmetry**
without any claim about **cause**. It sits between `contradicted` (something conflicts) and
`exposed` (someone is culpable), and it is exactly the register T4 says evidence can support.

**This may be a better third state than `suspected`.** T5 showed `suspected` is a
consequence-free refuge; `imbalance-proven` is not consequence-free, because the proof is
actionable outside the protocol — it is admissible to a court, an insurer, or a counterparty —
without requiring the adjudicator to attribute fault. Worth building as **B14**.

---

## K2 — Transparent TTP retires the fingerprinting idea

Their Definition 11: an offline TTP producing evidences **indistinguishable from those Alice and
Bob would have exchanged in a faultless case**. Definition 4 (true fairness) requires exactly
this — evidences independent of how the protocol executed. And the stated motivation is
commercial: TTP intervention may be due to network failure rather than cheating, so
distinguishable evidence causes unwarranted reputational damage.

Markowitch & Kremer (2001) achieve it concretely. A committed signature is convertible into a
final signature by **either** the signer **or** the TTP, using a GPS-derived scheme where the TTP
holds the conversion exponent. The recovered signature is the party's own, not a TTP affidavit,
and the two paths are indistinguishable.

**Drop the fingerprinting-as-disclosure observation.** It was parked as "possibly a workshop
paper." It is a solved problem with a named property, a definition, and an efficient construction
from 2001, motivated by precisely the concern raised. This is the correct outcome of the check
recommended in the closeout, and it is why the check was worth running.

---

## K3 — Statefulness is mandatory, and for a sharper reason than measured

Timeliness — the guarantee that honest parties can terminate in finite time while preserving
fairness — requires an **abort protocol mutually exclusive with recovery**, and the mutual
exclusion is enforced by the TTP holding per-run state (`aborted`, `recovered`).

Without it, the first protocol in their §6.1 is fair but not timely: Alice must hold an open
session indefinitely because Bob may recover at any later moment.

**A4 resolves more sharply than B11 concluded.** B11 made the adjudicator stateful across
disputes to test *rates*. This literature makes it stateful *per protocol run* because
**timeliness is otherwise impossible**. Two different kinds of state, and only the second is
mandatory. The harness models neither explicitly.

---

## K4 — The error protocol confirms T4's concealment criterion, from 2001

In the transparent-TTP protocol, Alice commits to `h(k)` in the evidence of origin but submits
`E_TTP(k')` with `k' ≠ k`. On recovery the TTP detects the mismatch and runs an **error
protocol**, informing both parties that Alice attempted to cheat.

This is attribution — and it works for exactly the reason T4 predicts. Alice's cheat is not an
assertion; it is a **concealing act**: committing to one value while submitting another. The two
artifacts must agree, and their disagreement is provable.

> **T4's criterion, independently instantiated: attribution became possible precisely where the
> protocol forced the liar to conceal rather than merely assert.**

Their design also shows the *rule* in use: they made the key hash part of the signed evidence
specifically so that substitution becomes detectable. That is the design criterion applied,
twenty-five years before it was named here. **Soften T4's novelty claim accordingly** — the
criterion is arguably implicit in protocol-design practice, even if unstated as a general rule.

---

## K5 — T5 generalises: key revocation is a better excuse than record loss

Their §7 treats a problem absent from the harness entirely: a signature key may be compromised and
its certificate revoked, and an adjudicator must then determine whether a signature predates
revocation. Countermeasures include time-stamping authorities, short-term **irrevocable** keys
issued by the signer under a long-term key, and signature chaining where revocation requires
counter-signature of the last signature in the chain.

**This is a strictly stronger version of M19.** T5 said claiming *record loss* dominates
tampering, because loss is unprovable while tampering is not. Claiming *key compromise* dominates
both — it is equally unprovable **and retroactively destroys evidence already issued.**

> **T5, generalised.** A rational adversary seeks the excuse that is (a) indistinguishable from
> honest misfortune and (b) maximally destructive of existing evidence. Record loss satisfies (a);
> key compromise satisfies both. Any accountability scheme must therefore rank its available
> excuses, because the adversary will occupy the best one.

The countermeasures are also informative: **irrevocable short-term keys work by removing the
excuse**, accepting a bounded compromise window instead. That is a T8 denomination — the
ambiguity paid for in accepted residual risk.

**Build M22 (repudiation-by-key-revocation) and B15 (short-term irrevocable keys).** This is the
most valuable concrete item the read produced.

---

## K6 — Two assumptions the harness never stated

**Channel model.** Their Table 1 has a channel-requirements column: unreliable (data may be lost),
resilient (arrives eventually), operational (arrives within a known bound). Every protocol's
guarantees are conditional on it, and operational channels are noted as unrealistic in
heterogeneous networks.

The harness has **no channel model at all**. M10 (benign record loss) is implicitly an unreliable
channel phenomenon and was never labelled as such. Add as assumption **A12**.

**Rational self-interest.** Their §2.2 assumes explicitly that *no party acts against its own
interests*, to avoid analysing self-harming deviations. The harness assumes this implicitly
throughout — T5's "always claim loss" is a pure rational-self-interest result — but never says so.
Add as **A13**. It matters: an irrational or externally-motivated adversary (a saboteur indifferent
to its own exposure) breaks several results here, including B6's query defence.

---

## K7 — A fifth currency for T8

Probabilistic fairness: a protocol is ε-fair if the probability of a fair outcome is at least
1−ε. Markowitch–Roggeman achieve non-repudiation with **no TTP at all** by having Alice secretly
choose the iteration count from a geometric distribution — chosen specifically for its non-aging
property, so no information about the remaining count leaks. Bob can only cheat by guessing when
to stop, with probability ε.

That is a **fifth denomination**: pay in *probability of unfairness* to eliminate the trusted third
party entirely.

| response | currency |
|---|---|
| single-state | false accusations |
| three-state | missed detections |
| stateful | false accusations at rate |
| bonded | tax on the honest |
| **probabilistic (no TTP)** | **ε chance of unfairness** |

**T8 now spans five mechanism families across three literatures.** Each pays the same conserved
cost in a different currency, and each chose its currency deliberately. This is the strongest
support the conservation property has.

---

## Consequences

| item | change |
|---|---|
| **T8** | **Strengthened again.** Five currencies, five families. Best-supported result in the project. |
| **T5** | **Generalise.** Excuse-ranking, with key compromise dominating record loss. |
| **T4** | **Soften the novelty claim.** The criterion is instantiated in 2001 protocol design, if not named. |
| **A4** | Resolve as per-run statefulness (mandatory for timeliness), distinct from cross-dispute statefulness. |
| **A12, A13** | New: channel model; rational self-interest. Both were implicit. |
| **Fingerprinting** | **Retire.** Solved by transparent TTPs, 2001. |
| **Verdict vocabulary** | Add `imbalance-proven` from weak fairness. |

## New work suggested

- **B14** — weak-fairness vocabulary: `{imbalance-proven, contradicted, unresolved, clear}`.
  Candidate replacement for `suspected`, and unlike it, not consequence-free.
- **M22 / B15** — repudiation by claimed key compromise, and short-term irrevocable keys as the
  countermeasure that removes the excuse.
- **A12** — an explicit channel model, so M10 and M19 are labelled rather than assumed.

## Standing after four reads

Every one of the four reads changed a conclusion. The pattern is now unmistakable: **this project
kept rediscovering, in a 2026 framing, results the non-repudiation and fair-exchange communities
established between 1996 and 2010.** That is not a failure — it is precisely the paper's thesis,
and having rediscovered them independently is what makes the mapping credible rather than
bibliographic.
