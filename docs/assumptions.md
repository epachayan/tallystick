# Tallystick — Assumption Ledger

> **HISTORICAL RECORD — intentionally frozen.** This document records an earlier
> phase of the project. Embedded counts, "current" wording, open items, and some reasoning may have
> been superseded by later findings; they are preserved to keep the correction history intact.
> For current figures use [`../results/canonical.txt`](../results/canonical.txt), and for current
> claim status use [`what-is-established.md`](what-is-established.md).


> **Partially superseded.** `p₀` has since been swept (robust, E13) and the scorer audited and fixed.
> Newer assumptions — A12 channel model, A13 rational self-interest, A14 key ≡ party, A15 the audit
> properties themselves — are summarized in [`../RESEARCH.md`](../RESEARCH.md#8-limitations).

Every assumption the harness rests on, with status. Discharged means tested and
either confirmed or corrected. Live means still load-bearing and untested.

| # | Assumption | Status | What happened |
|---|---|---|---|
| A1 | Mistake and malice occur at comparable rates | **LIVE — and it decides everything** | E7: at 5% mistakes, B7 makes one wrongful attribution per 13 correct. At 25%, one per three. **No published figure exists for how often a principal misremembers a delegation.** The parameter that determines whether these systems are safe to deploy has never been measured. |
| A2 | Uniform M-class sampling is a fair metric | **DISCHARGED — false** | [RESEARCH §3.5](../RESEARCH.md#35-adversarial-scoring): under adversarial class selection every baseline through B6 scores 0.00. Coverage, not accuracy, is the correct metric. |
| A3 | `record_intact` and `record_available` are independent | **DISCHARGED — false, and it was a bug** | Availability *gates* intactness: you cannot fail verification on a record never produced. Every baseline had this backwards, and fixing it produced T5 below. |
| A4 | The adjudicator is a pure function of the presented view | **LIVE — internally inconsistent** | B6's oracle defence assumes the adjudicator remembers prior disputes, i.e. it is stateful. The model says otherwise. Unresolved contradiction. |
| A5 | Signatures can be accounted rather than computed | **LIVE, low risk** | 96 B per signature, never executed. Matters for a systems paper, not for the claims made. |
| A6 | Scope is a flat set of opaque labels | **LIVE** | No hierarchy, so semantic ambiguity (`write:records` ⊂ `write:*`) is untestable. Blocks the semantic-authorization vector entirely. |
| A7 | One authorization, one execution, no clock | **LIVE** | Revocation, staleness and ordering are absent. Parakhin's result on TTL revocation was in the first sweep and is still unmodelled. |
| A8 | Two parties, one adjudicator | **LIVE** | Equivocation degenerate; T2's bound is two-party and will change shape under colluding complainants. |
| A9 | Detection and attribution are the same act | **DISCHARGED — false** | [T4 in finding 03](findings/03-mistake-vs-malice.md). Evidence establishes contradiction; culpability is a separate inference cryptography cannot make. |
| A10 | A more capable scheme is a better scheme | **DISCHARGED — false** | E8: every attributive baseline is Pareto-dominated. See below. |
| A11 | The mistake classes reflect real behaviour | **LIVE** | Constructed, not observed. Plausible and matches ordinary experience; still an assumption and labelled as one. |

---

# Findings 04 — Outliers Pursued

**Corpus:** v0.6, 500 scenarios, 20 classes, 0 validator violations

## T5 — The suspicion state is a strategic refuge

T1 established that an adjudicator needs a third verdict state, because loss and concealment
are indistinguishable. **M19 shows that third state is itself an attack surface.**

M19: the executor tampers with its record *and then claims it is simply unavailable*.

| baseline | M4 (tamper, record produced) | M19 (tamper, claim lost) |
|---|---|---|
| B3 suspected/exposed | correct blame 25/25 | **missed 25/25** |
| B7 verifiable adjudication | correct blame 25/25 | **missed 25/25** |
| B10 composed | correct contradiction 25/25 | **missed 25/25** |

Every scheme. Universally.

> **Claiming unavailability strictly dominates tampering.** A tamperer who produces the altered
> record fails verification and is exposed. A tamperer who claims loss receives a suspicion,
> which by construction carries no consequence. A rational adversary always claims loss.

This is a genuine tension with T1, not a patch on it. T1 says the third state is *necessary* to
avoid false accusation. T5 says the third state is *exploitable* precisely because it is
consequence-free. Both are true, and together they say something stronger than either:

> **Within a purely evidential framework, avoiding false accusation and deterring concealment
> are incompatible.** Any state that safely absorbs honest failure will be occupied by
> dishonest failure.

### What this demands

An escape has to come from outside the evidence. Make unavailability *costly* rather than
provable — bonded collateral forfeited on unresolved suspicion, or a reputation cost that
accrues to repeated suspension. That is the incentive-based vector the initial internal review
listed as merely missing. **The data now demands it**: T5 is the argument for economic mechanisms, and it
was produced rather than assumed.

## T6 — Attribution is Pareto-dominated

Outlier O2 asked why B2, a strictly weaker scheme, over-attributes four times less than B7.
The answer generalises:

| baseline | classes handled (of 20) | over-attributions | dominated by |
|---|---|---|---|
| B0 bearer + executor log | 7 | 0 | B9, B10 |
| B2 commitment-only | 11 | 25 | B9, B10 |
| B3 / B4 / B5 | 13 | 100 | B6, B7, B9, B10 |
| B7 verifiable adjudication | 15 | 100 | B9, B10 |
| B9 non-attributive | 16 | 0 | B10 |
| **B10 composed** | **17** | **0** | **— PARETO —** |

**Every attributive scheme is dominated.** B10 handles more classes than B7 with zero wrongful
accusations. In this data the attributive step buys nothing and costs 100 wrongful accusations.

That inverts the assumption the whole project ran on for two days — that a more capable scheme
is a better one. Capability here means *willingness to assert culpability*, and that willingness
is pure downside.

## Outlier O1 — the worst scheme was accidentally right

B0's 50 "spurious" verdicts were, on inspection, exactly M15 and M17 — the mistake classes. B0
flagged the conflict and blamed nobody, which is the *correct* behaviour. It reached that
behaviour not by design but by incapacity: it cannot attribute, so it cannot over-attribute.

The scorer was penalising it. Fixed: detecting a conflict without attributing fault now scores
`correct_contradiction` whether reached by design (B9, B10) or by incapacity (B0).

A small thing, but it is the second time an outlier turned out to be the harness being wrong
rather than a baseline being interesting. Both were found by chasing anomalies rather than by
reading summaries.

---

## What now drives further experiments

1. **Bonded suspicion (B11).** T5 demands it. Attach a forfeitable stake to the suspicion state
   and measure at what stake level claiming loss stops dominating tampering. This is the first
   experiment in this project where the *mechanism* is economic rather than cryptographic, and
   T5 is the reason.
2. **Measure A1, or say loudly that nobody has.** The mistake-rate parameter decides deployment
   safety and is unmeasured. Even a crude survey figure would be a contribution; failing that,
   the absence itself is worth stating in the paper.
3. **Resolve A4.** The adjudicator is modelled as stateless and argued about as stateful. Pick
   one — statefulness is required for T2's defence, so probably that, and then re-examine what
   a stateful adjudicator leaks across disputes.
4. **A7, time.** Revocation and staleness are a whole missing dimension, and M16 (good-faith
   stale grant) already gestures at it without modelling a clock.
