# Tallystick — Formal Results (T1–T4)

> **T4 SUBSUMED, 11 August 2026.** T4's concealment criterion is the same statement as the
> conservation boundary's D-condition: a concealing act is precisely what creates a divergence the
> honest twin does not have. The boundary states it more generally and is checked as a build stage.
> See [`findings/12-conservation-boundary.md`](findings/12-conservation-boundary.md). The proof
> below stands; its scope is now a corollary rather than a separate result.
>
> **Covers T1–T4 only.** T5–T12 postdate this document and live in `findings/` and `../RESEARCH.md`:
> T5 the suspicion refuge, T6 attribution dominance, T7 scale invariance, T8 conservation (now bounded — see findings/12),
> T9 key ≡ party, T10 the residual, T11 relocation, T12 level invariance.

**Date:** 8 August 2026 · **Verified by:** `experiments.py` (E1, E2, E3)

Three claims that generalise beyond the measurements. Stated formally, tested empirically,
with an explicit prior-art position on each. One is a reduction, one is novel, one is
arithmetic — and they are labelled accordingly.

---

## T1. Two-valued adjudication cannot be both accurate and complete

### Statement

Let an adjudicator be a deterministic function `V : views → {blame, no-blame}` over what the
parties present. Then no `V` is simultaneously

- **accurate** — never returns `blame` for an honest party, and
- **complete** — always returns `blame` for a dishonest one.

### Proof

Construct two worlds with identical adjudicator views.

- **World A.** The executor is honest. Its execution record is genuinely lost.
- **World B.** The executor exceeded its scope and is withholding the record.

In both, the adjudicator receives: a committed authorization, a principal asserting the
truth, and no execution record. The views are byte-identical (**E1 verifies this
mechanically**). Since `V` is a function of the view, `V(A) = V(B)`.

If `V(A) = blame`, accuracy fails in A. If `V(A) = no-blame`, then `V(B) = no-blame` and
completeness fails in B. ∎

### The escape, and what it does not buy

Widen the codomain to `{exposed, suspected, clear}` and map both worlds to `suspected` —
neither blame nor clearance, withdrawn when the record appears.

**E1 confirms this, and corrects an earlier claim of mine.** Every three-state baseline
(B3–B7) returns `suspected` in *both* worlds, not `exposed` in B. The escape does **not**
recover completeness. It converts a forced error into an honest abstention. That is a
weaker and more accurate reading than I gave previously.

*(Finding that required fixing a real bug: the baselines were reading ground-truth actions
even when the record was unavailable — the adjudicator was consulting evidence it could not
have had. E1 surfaced it; the fix is in `baselines.py`.)*

### Prior art — this is a reduction, not a new theorem

The accuracy/completeness pair is Chandra & Toueg's, and the indistinguishability argument
is theirs: in an asynchronous system a crashed process cannot be told from a slow one, so
accuracy cannot be guaranteed. **Do not claim T1 as novel.**

The contribution is the *transfer*, and one structural difference worth stating:

| | failure detectors | delegation accountability |
|---|---|---|
| indistinguishable pair | crashed vs. slow | record lost vs. record withheld |
| nature of ambiguity | **temporal** | **adversarial** |
| resolves with time? | yes — hence ◇S, eventual accuracy | **no** — withholding can persist forever |

Chandra–Toueg's useful classes are the *eventual* ones: wait long enough and accuracy is
recovered. That escape is unavailable here. A rational adversary withholds indefinitely, so
there is no ◇-variant of this problem.

**Consequence:** the three-state output is not a design convenience borrowed from PeerReview.
It is the *only* available escape, because the one that makes failure detectors tractable is
closed. Every single-state agentic audit proposal surveyed — hash-chained logs, delegation
receipts — inherits the dichotomy with no way out.

---

## T2. Query leakage is bounded by grievance supply, not by query budget

### Statement

Let the committed set have `k` items drawn from a vocabulary of `V`. Under accountable
queries (B6), where a probe is staked as a claim of non-membership and a refuted claim
exposes the prober, the expected number of probes an adversary completes before exposure is

$$ \mathbb{E}[\text{probes}] = \frac{V+1}{k+1} $$

### Proof sketch

Each probe names an item and claims it is *not* in the committed set. A probe on an
out-of-scope item returns non-membership: the claim stands, the adversary learns one bit,
and nothing is refuted. A probe on an in-scope item returns membership: the adversary's own
staked claim is contradicted, and it is exposed.

Probing a shuffled vocabulary, exposure occurs at the first in-scope item. The expected
position of the first of `k` marked items in a uniformly random permutation of `V` is
`(V+1)/(k+1)`. ∎

### Verification

**E2**, 2000 trials, `V = 64`, `k = 8`:

| scheme | mean bits learned | max | as % of vocabulary |
|---|---|---|---|
| B5 dispute-driven | 64.0 | 64 | **100%** |
| B6 accountable queries | **7.2** | 35 | 11.3% |

Predicted `(V+1)/(k+1) = 7.22`; measured `7.21`.

Under B5 a baseless probe is free, so the adversary enumerates the entire vocabulary. Under
B6 it stops after ~7 probes.

### Why this is the interesting one

The bound is **not** the query budget — that was the loose framing in the earlier notes.
It is the adversary's **supply of truthful grievances**. A party with many genuine complaints
legitimately learns more; a party with none is exposed almost immediately.

Two consequences that are not obvious from the measurement alone:

1. **Denser scopes are cheaper to protect.** Leakage scales as `V/k`. A narrow authorization
   in a large vocabulary leaks proportionally more before refutation, which is the opposite
   of the usual least-privilege intuition.
2. The tail is long — max observed 35 of 64 — so the guarantee is in expectation, not
   worst case. A high-percentile bound would need rate limiting on top.

**Prior art position:** I have not found this in the fair-exchange or non-repudiation
literature, which treats the adjudicator as a trusted oracle rather than as a leaky one.
Check Rial & Preneel's priced-OT before claiming it, since disclosure-constrained dispute
resolution is their territory.

---

## T3. The disclosure crossover, in closed form

### Statement

Both schemes carry the same two signatures, so those cancel. Let `L` be mean item length,
`M` fixed metadata, `R` a commitment root, `q` the number of queries, and `P(n)` the size of
one non-membership proof over `n` items:

$$ P(n) = 2 + L + \lceil \log_2 n \rceil \cdot 32 + \lceil \log_2 n \rceil / 8 $$

Selective adjudication is cheaper than full disclosure exactly when

$$ 2nL + M \;>\; 2R + q \cdot P(n) $$

### Verification

**E3**, with `L = 13.9 B`, `M = 40 B`, `2R = 64 B`, `q = 1`:

| n | full `2nL+M` | selective | winner |
|---|---|---|---|
| 2 | 96 | 124 | full |
| 4 | 151 | 155 | full |
| **8** | **263** | **187** | **selective** |
| 32 | 931 | 429 | selective |
| 64 | 1,821 | 496 | selective |

Predicted `n* = 8`. The empirical sweep placed it between 4 and 8 (1.06× at scope 4, 0.90×
at scope 8). **The closed form and the measurement agree.**

*(An earlier version of this model predicted `n* = 64` and contradicted the sweep. It counted
only the scope, not the execution record, and charged the signatures to the selective scheme
while leaving them out of full disclosure. Both errors are fixed above.)*

### Reading

The threshold is set by the **fixed commitment overhead `2R`**, not by the logarithmic factor.
The log term is nearly free; the roots are what you pay for. And the cost degrades **linearly
in `q`** — so the design rule is to bound the number of queries, which is exactly what B5
does and B4 does not.

This is arithmetic, not a theorem. It is worth stating because it converts an empirical curve
into a formula a designer can evaluate against their own parameters.

---

## Summary of standing

| result | status | claim to make |
|---|---|---|
| **T1** accuracy/completeness dichotomy | proved; reduces to Chandra–Toueg | *"an instance of, with the eventual-accuracy escape closed"* — not a new theorem |
| **T2** leakage bound `(V+1)/(k+1)` | proved, verified to 0.01 | novel as far as swept; verify against Rial & Preneel first |
| **T3** crossover closed form | derived, matches measurement | a design formula, not a result |

## What would strengthen this further

1. **A worst-case leakage bound for T2.** The expectation is tight; the tail is not bounded.
   Rate limiting or a per-party query budget would give a high-percentile guarantee, and the
   harness can measure whichever is proposed.
2. **Formalise the adjudicator in T1 as randomised.** The proof assumes `V` deterministic. A
   randomised adjudicator escapes the strict dichotomy at the cost of a per-decision error
   rate — worth stating, because it is the standard objection.
3. **Multi-party.** All three results are two-party. Equivocation is degenerate at two
   parties, and T2's bound almost certainly changes shape when several parties can probe.

---

## T2 addendum — worst case, and the prior-art verdict

### The expectation bound is not deployable on its own

**E4**, 20,000 trials, `V = 64`, `k = 8`:

| quantile | probes before exposure | closed-form P(>t) |
|---|---|---|
| p50 | 5 | 0.501 |
| p90 | 16 | 0.085 |
| p95 | 19 | 0.049 |
| p99 | **27** | 0.009 |
| max | 47 | — |

The mean is 7.2 but the p99 is **27 probes — 42% of the vocabulary**. The distribution is
negative-hypergeometric, so a high-percentile bound follows in closed form: the smallest `t`
with `C(V−k, t) / C(V, t) ≤ 1−p`.

**An expectation guarantee is the wrong guarantee here.** A patient adversary sits in the
tail.

### B8 — a per-epoch query budget converts it to a hard cap

| budget `b` | mean leaked | p99 leaked | % of vocabulary |
|---|---|---|---|
| 1 | 1.00 | 1 | 1.6% |
| 2 | 1.87 | 2 | 3.1% |
| 4 | 3.28 | 4 | 6.2% |
| 8 | 5.14 | 8 | 12.5% |

Leakage is capped at `min(b, first-hit)` regardless of the tail. And the cost to honest use is
close to nil: a legitimate complainant needs one query per real grievance, so `b` can be small
without impeding genuine disputes. **B8 should be built.**

### Prior-art verdict — partially anticipated, and I have to say so

Rial & Preneel (AFRICACRYPT 2010) motivate their work with, among other things, the case
where **a malicious buyer accuses an honest vendor of misbehaviour without the vendor being
able to prove the accusation untrue.** Their construction lets a neutral, dispute-only
adjudicator handle complaints from either side while learning neither the vendor's item list
nor which item the buyer chose.

So the *concept* T2 addresses — abuse of the dispute mechanism, and the accused party's
ability to refute — is present in 2010. Do not present it as newly identified.

What I still do not find anywhere is the **quantification**: expected and high-percentile
probes before refutation as a function of `V` and `k`. Their guarantee is that the
*adjudicator* learns nothing; T2 bounds what the *complainant* learns from the outcomes of
its own complaints. Those are different quantities.

**Revised claim for T2:** not a new problem, and not a new defence — a **measured bound on a
known leak**, plus the observation that the expectation is insufficient and a budget is
required. That is a modest contribution honestly stated, and it is defensible.

**It also strengthens the main thesis.** Rial & Preneel is now a *fourth* pre-2011 line
carrying the accused-party defence that the 2024–26 agentic stack lacks: PeerReview 2007,
ASW 1998, Zhou–Gollmann from 1996, and priced OT 2010. The regression is broader than first
mapped.

---

## T1 addendum — the randomised adjudicator objection fails

**E5**, 20,000 trials over the E1 world pair:

| blame probability `p` | detection rate (world B) | false-accusation rate (world A) | difference |
|---|---|---|---|
| 0.10 | 0.100 | 0.099 | +0.001 |
| 0.50 | 0.499 | 0.500 | −0.000 |
| 0.90 | 0.901 | 0.900 | +0.001 |

Detection minus false accusation is zero at every `p`, to sampling error. **On an
indistinguishable view class the adjudicator's ROC curve is exactly the diagonal.**

A randomised adjudicator can trade the two error types against each other but cannot reduce
both. T1 survives the objection, and the third output state remains the only escape.


---

## T4 addendum — prior-art verdict on the concealment criterion

**Checked, and the impossibility half is not claimable.**

The arbitrary (Byzantine) fault model states the point outright as a standard modelling
assumption: in that model it is impossible for a process to decide whether another is behaving
arbitrarily *intentionally* or not. Byzantine models cover mistake and malice by refusing to
distinguish them — which is exactly T4's impossibility, and it predates this work by decades.

**Do not claim T4's impossibility as novel.** What survives:

1. **The concealment criterion as a design rule.** BFT does not attempt separation, so it has no
   occasion to state *when* separation is possible. The criterion — mistake is separable from
   malice exactly when malice requires an additional concealing act — appears to be new, and it is
   actionable: structure the protocol so lying requires concealment rather than mere assertion.
2. **The observation that the agentic-delegation literature promises what the fault model forbids.**
   Systems advertising irrefutable attribution are promising something the arbitrary fault model
   has said is unavailable since 1982. That gap between promise and possibility is the
   contribution, and it is a matter of record rather than of theory.

Framing for the paper: not *"we prove attribution is impossible"* but *"the fault model has always
said so, and the systems being deployed do not act as if they know it."*
