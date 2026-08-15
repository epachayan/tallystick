# Accountability for Delegated Agentic Action: An Experimental Study

**Author:** Nitin Stephen Koshy · ORCID [0009-0009-2690-0588](https://orcid.org/0009-0009-2690-0588)
**Status:** working research record, August 2026 (revised after the hardening phase)
**Artifacts:** 850-scenario corpus, 34 adversarial classes, 18 adjudication baselines, 158 tests
**Canonical figures:** `results/canonical.txt` (regenerate with `make experiments`)
**Claim strength:** `docs/what-is-established.md` — three tiers; read it before quoting anything
**Reproducibility:** deterministic from seed `20260808`; Python 3.12+ runtime, standard library only; `pytest` is the test/development dependency

---

## Abstract

Systems that delegate authority to AI agents increasingly promise *accountability*: cryptographic
evidence tying an action to a responsible party. This study builds an adversarial harness to test
what evidence-based accountability can actually deliver in a two-party delegation dispute, and
finds the promise systematically overstated.

Eighteen adjudication schemes are measured against thirty-four adversarial scenario classes,
spanning executor misconduct, principal repudiation, benign failure, sincere mistake, abuse of
the dispute mechanism, adjudicator collusion, symmetric withholding, and protocol abort.

The central result is a **boundary** rather than a blanket conservation claim. Write D(w) for the
set of parties whose account diverges from the record in world w. For an evidentially
indistinguishable pair of worlds:

> D(guilty) = D(honest) → **escapable**: some verdict is true in both, and a non-attributive
> vocabulary resolves the pair at no cost.
> D(guilty) ≠ D(honest) → **binds**: no verdict is true in both, and every mechanism must be wrong
> about one of them.

Informally: twins differing only in *why* a divergence occurred are escapable; twins differing in
*whether* one occurred are not. The proof is immediate — identical evidence yields one verdict —
and the contribution is not the proof but the boundary's **predictive use**: it determines, for
every twin pair and every mechanism, which side of the line the pair falls on, and the harness
recomputes that prediction as a build stage.

An earlier version of this study stated the conservation unbounded. That was too strong: it was
implicitly restricted to binding pairs, and the escapable case explains — rather than merely
observes — why non-attributive vocabulary is worth adopting.

A second contribution is methodological, and negative. Six declaration defects found during the
hardening pass shared the same shape: a universal statement inferred from the subset in view. A
seventh declaration drift was found during the final publication review, together with a build
integration bug that masked the validator's failing exit status. The recurring countermeasure is
the same: derive structure from the code, diff it against declarations, and test that failures
actually propagate through the correctness gate. §9 records them.

A third contribution is historical and comparative. The property that a correct party can defend itself
against false accusation is present in at least four research lines from 1996–2010 —
non-repudiation protocols, optimistic fair exchange, PeerReview, and optimistic fair priced
oblivious transfer. The specific 2024–2026 identity/delegation proposals originally reviewed did
not cite those lines. Since then, adjacent 2026 work such as DRP, HDP, AP2/Verifiable Intent and
new standards initiatives has made verifiable authorization and provenance an active area. The
remaining claim is narrower: this harness evaluates those kinds of artifacts as evidence in an
adversarial disagreement model rather than claiming the field lacks delegation evidence.

---

## 1. Motivation

The initiating question was whether a novel cryptographic primitive was needed for trust in
agentic delegation. The historical tally stick — a split, bearer-verifiable, tamper-evident
record where neither half means anything alone — suggested a bilateral construction.

Four rounds of prior-art review established that the construction was already occupied
(§7), and the effort was redirected: rather than build a primitive, measure what the existing
ones can and cannot do, adversarially, and publish the harness.

**Design constraint, fixed at the outset:** the work must benefit the community even if the core
problem is never solved. This determined the sequencing — corpus and instrument before
construction — and it is why the effort has usable output despite producing no new primitive.

---

## 2. Model

**Parties.** A principal `P` grants an authorization; an executor `E` performs actions; an
adjudicator `J` resolves disputes.

**Adjudicator model.** Offline / optimistic, per Asokan–Shoup–Waidner: `J` exists only when a
dispute is raised, sees only what parties present, and has no independent view of the world.
Resolved as **stateful** in Experiment 05 (it retains cross-dispute history), which had been an
unacknowledged contradiction in the original model.

**Properties under test.**

| | property | short |
|---|---|---|
| P1 | principal non-repudiation | maps to non-repudiation of origin (ISO/IEC 13888) |
| P2 | executor non-repudiation | maps to non-repudiation of receipt |
| P3 | authorization integrity | |
| P4 | execution integrity | no direct analogue in message-exchange models |
| P5 | equivocation detection | **degenerate at two parties** — restated as fork-detectability |
| P6 | minimal disclosure | measured as bytes, later as entropy |

**Deliberate exclusions.** Multi-hop chains, federation, a clock (revocation, staleness,
ordering), scope hierarchies, and real signature computation. Each is recorded in the assumption
ledger with its status.

---

## 3. Method

### 3.1 The generator

Scenarios are emitted as seeded JSONL against a versioned schema. **The generator knows nothing
about cryptography** — no signatures, no hashes, no receipts. It records what each party did and
what each party claims; whether a scheme can detect the divergence is scored separately.

This decoupling is the reason the corpus survives every baseline change. Where a scenario and its
adversarial twin must differ only in intent, both are drawn from the same random stream (`TWIN_OF`),
making the resulting adjudicator views byte-identical.

### 3.2 Ground truth

Encoded as *who lied about what*, not as a boolean:

```json
{"dishonest_party": "P|E|both|J|none",
 "p_state": "honest|mistaken|dishonest",
 "e_state": "honest|mistaken|dishonest",
 "claim": "...", "actual": "...", "adjudicable": true}
```

The separation of `dishonest_party` from per-party *state* is what makes over-attribution
measurable, and it was added only after Experiment 03 showed it was needed.

### 3.3 Scoring

A verdict is scored on **who it blamed**, not on whether a conflict was noticed. Collapsing those
is what makes most audit-trail evaluations uninformative.

| outcome | meaning |
|---|---|
| `correct_blame` | dishonest party correctly identified |
| `false_accusation` | an honest party was blamed |
| `over_attribution` | a **mistaken** party was blamed as culpable |
| `correct_contradiction` | conflict flagged, no fault attributed |
| `missed` | someone was dishonest, nobody blamed |
| `correct_abstain` / `_amb` | correctly declined to blame |

### 3.4 Validation

`validate.py` enforces scenario coherence: a record flagged altered must actually differ; a
dishonest party must assert something false; a mistaken party must diverge without lying; an
unadjudicable scenario must genuinely lack a settling artifact.

**It caught three real modelling errors**, including one — the M13 procedural-falsehood case —
within seconds of the class being written. Its absence in the first experiment cost hours of
score archaeology.

### 3.5 Adversarial scoring

Uniform class sampling was used initially and is **wrong for a security property**. An adversary
selects the class a scheme is worst at. Reported worst-class alongside average throughout §5.

---

## 4. Baselines

| id | scheme | rationale |
|---|---|---|
| B0 | bearer authorization + executor-maintained log | the deployed 2026 default (OAuth + provider audit log) |
| B1 | bilateral commitment | PeerReview-style split tally |
| B2 | commitment-only disclosure | contents withheld from `J` |
| B3 | B1 + `suspected`/`exposed` | PeerReview's two-state output |
| B4 | scope-predicate commitments, exhaustive queries | Merkle membership over committed sets |
| B5 | dispute-driven bounded queries | queries bounded by the dispute, not the record |
| B6 | B5 + accountable complainant | a staked query that refutes itself exposes the prober |
| B6c | B6 as deployed under a colluding adjudicator | control |
| B7 | B6 + publicly verifiable adjudication | `J` publishes a recomputable transcript |
| B9 | non-attributive `{contradicted, unresolved, clear}` | claims about the record, not the person |
| B10 | B9 vocabulary + B7 transcript | **sole Pareto point** |
| B11 | stateful, binomial test on suspension rate | pattern evidence |
| B12 | bonded suspicion (analytic, E10) | economic rather than evidential |

---

## 5. Experiments and results

### E1 · Indistinguishability → **T1**

Two worlds with byte-identical adjudicator views: an honest executor whose record is genuinely
lost, and a dishonest one withholding an incriminating record.

> **T1.** No deterministic two-valued adjudicator `V : views → {blame, no-blame}` is both accurate
> (never blames the honest) and complete (always blames the dishonest).

Widening the codomain to `{exposed, suspected, clear}` maps both worlds to `suspected`. Verified:
every three-state baseline suspends in **both** worlds. **The escape does not recover
completeness** — it converts a forced error into an honest abstention.

*Standing:* a **reduction**, not a new theorem. The accuracy/completeness pair and the
indistinguishability argument are Chandra & Toueg's. The contribution is the transfer plus one
structural difference: their ambiguity is *temporal* (crashed vs. slow) and resolves with time,
which is what makes eventual-accuracy classes useful. Ours is *adversarial* — withholding persists
indefinitely — so **there is no ◇-variant of this problem**, and the third state is the only escape.

### E5 · The randomised objection → T1 survives

A randomised adjudicator blames with probability `p`. On an indistinguishable view class,
detection rate minus false-accusation rate is **zero at every `p`** (20,000 trials): the ROC is the
diagonal. Randomisation trades error types; it cannot reduce both.

### E2, E4 · Query leakage → **T2**

Under accountable queries (B6), a probe is staked as a claim of non-membership; a refuted claim
exposes the prober.

> **T2.** Expected probes before exposure = `(V+1)/(k+1)`.

Predicted 7.22, measured 7.21 (2,000 trials, V=64, k=8). Without accountability (B5) the adversary
enumerates the entire vocabulary — 64 of 64.

**The bound is not the query budget; it is the adversary's supply of truthful grievances.** Two
consequences: leakage scales as `V/k`, so a *narrow* authorization in a large vocabulary leaks
proportionally more — the opposite of least-privilege intuition; and the tail is long.

E4: mean 7.2 but **p99 = 27 probes, 42% of the vocabulary**. The distribution is
negative-hypergeometric; a high-percentile bound is the smallest `t` with
`C(V−k,t)/C(V,t) ≤ 1−p`. **An expectation guarantee is the wrong guarantee** — a patient adversary
sits in the tail. A per-epoch budget caps leakage at `min(b, first-hit)` and costs honest
complainants nothing.

*Standing:* Rial & Preneel (2010) motivate their work partly with a malicious buyer accusing an
honest vendor who cannot disprove it. **The concept is not new.** The quantification appears to be:
their guarantee is that the *adjudicator* learns nothing; T2 bounds what the *complainant* learns
from its own complaints.

### E3 · Disclosure crossover → **T3**

Both schemes carry the same signatures, which cancel. Selective adjudication is cheaper iff
`2nL + M > 2R + q·P(n)`, with `P(n) = 2 + L + ⌈log₂n⌉·32 + ⌈log₂n⌉/8`.

Predicted `n* = 8`; the empirical sweep placed it between 4 and 8. **The threshold is set by the
fixed commitment overhead, not the logarithmic factor**, and cost degrades linearly in `q` — which
is why bounding queries matters.

*An earlier model predicted n*=64 and contradicted the sweep.* It counted only the scope and
charged signatures asymmetrically. Both errors corrected.

### E6 · Mistake vs malice → **T4**

M15/M17 are evidential twins of M6/M7 — same seed stream, **25/25 byte-identical views** — differing
only in whether the principal lied or sincerely misremembered.

> **T4.** Evidence establishes *contradiction*, not *culpability*.

Every attributive baseline, **including B7 which was otherwise perfect**, accuses a sincerely
mistaken party wherever a mistake class appears. B9 (non-attributive) does so zero times.

**The boundary, from the M1/M16 row which does *not* match:**

> Mistake is separable from malice **exactly when malice requires an additional concealing act.**
> Where malice is purely assertional, no evidence-based scheme can attribute fault.

A liar and a forgetful principal perform the identical speech act. A lying executor must *omit*
the action from its record while a good-faith one on a stale grant reports it. Concealment leaves a
trace; belief does not.

*Standing (verified against the BFT literature):* the **impossibility is Byzantine-fault-model folklore** — the arbitrary fault model states outright that
it is impossible to decide whether a process is behaving arbitrarily *intentionally*, and covers
mistake and malice by refusing to distinguish them. What appears new is (a) the concealment
criterion as a *design rule*, and (b) the observation that the agentic-delegation literature
promises exactly the attribution the fault model says is unavailable.

### E7 · Sensitivity to mistake prevalence

| mistake rate | B7 wrongful : correct |
|---|---|
| 5% | 1 : 13 |
| 25% | 1 : 3 |

**No published figure exists for how often a principal misremembers a delegation.** The parameter
deciding whether these systems are safe to deploy has never been measured. Saying so plainly may be
worth as much as any theorem here.

### E8 · Capability vs harm → **T6**

| baseline | classes handled (of 20) | over-attributions | dominated by |
|---|---|---|---|
| B7 | 15 | 100 | B9, B10 |
| B9 | 16 | 0 | B10 |
| **B10** | **17** | **0** | **— Pareto —** |

> **T6.** Among schemes with the same entitlements, every attributive scheme is Pareto-dominated.
> The attributive step buys nothing and costs 100 wrongful accusations.

**Recomputed after hardening, and the qualifier matters.** B10 is no longer the sole Pareto
point: B16c leads on classes handled with 0 over-attributions, and B11 follows — but each does so
only by virtue of a declared entitlement, custodial access and retained history respectively. Those
are trust assumptions, not superior designs. Compared at equal entitlement, the ordering stands.
T6 must always be reported with entitlements attached; the unqualified form is wrong.

This inverts the assumption the project ran on for two days: capability, here meaning *willingness
to assert culpability*, is pure downside.

### M19 · The suspicion refuge → **T5**

M19: the executor tampers **and then claims the record is unavailable**.

| | M4 (tamper, record produced) | M19 (tamper, claim lost) |
|---|---|---|
| B3 / B7 / B10 | correct 25/25 | **missed 25/25** |

> **T5.** Claiming unavailability strictly dominates tampering. A produced-but-altered record fails
> verification; a withheld one earns a consequence-free suspicion. A rational adversary always
> claims loss.

T1 says the third state is *necessary*; T5 says it is *exploitable* precisely because it is
consequence-free.

*This was found by fixing a bug present in every baseline*: availability **gates** intactness — you
cannot fail verification on a record never produced. All schemes had it backwards.

### E9 · Statefulness → **T7**

M20 (repeat offender hiding behind loss) and M21 (genuine repeated loss) are pattern twins at
overlapping observed rates.

| class | B10 stateless | B11 stateful |
|---|---|---|
| M20 repeat offender | missed 25/25 | correct 18/25 |
| M21 unlucky honest | correct 25/25 | **false accusation 23/25** |

> **T7.** Pattern evidence does not escape the accuracy/completeness dichotomy. It reinstates it one
> level up. **T1 is scale-invariant.**

What statefulness *does* buy is a bound, not an escape. A greedy adversary at rate 0.60 is caught
with power 0.94 over 20 disputes; a disciplined one is not — but discipline caps its own misconduct,
converging on the honest base rate as the window grows (42% at n=20, 32% at n=100). **Not
attribution, not deterrence — rate limiting.** At α=0.05 roughly 3–4% of genuinely unlucky
executors are flagged permanently, and no α removes the trade.

*The through-line broke here informatively.* Every earlier fix worked by making a trusted party
accountable. This one failed because the thing being made accountable was **bad luck**, which has no
agent to hold responsible. The pattern works on parties, not on outcomes.

### E10 · Bonded suspicion → **T8**

T7 forced an economic mechanism: if no evidential response escapes T1, price the ambiguity instead
of resolving it. Executor posts stake `S`; exposure penalty `D`; honest loss rate `p₀`.

Claiming loss dominates iff `S < D`. Deterrence therefore requires `S ≥ D` — at which point the
honest executor pays `p₀·D` per dispute **purely for being unlucky** (25% of the penalty at
p₀ = 0.25).

> **T8 (Conservation of ambiguity).** Where evidence cannot separate honest failure from
> concealment, the cost of that ambiguity cannot be eliminated — only denominated.

| response | currency | who pays |
|---|---|---|
| single-state (B1) | false accusations | honest, wrongly blamed |
| three-state (B3–B10) | missed detections | victims of concealment |
| stateful (B11) | false accusations at rate | honest but unlucky |
| bonded (B12) | forfeited stake | honest, taxed `p₀·D` |

**The honest party pays in three of the four.**

### E11 · Disclosure as entropy

Bytes were a weak proxy, flagged twice and finally replaced. V=64, k=8, prior entropy 32.0 bits:

| scheme | bits leaked | % of H₀ |
|---|---|---|
| B5/B7 one query | 0.2 | 1% |
| B5/B7 three queries | 3.3 | 10% |
| B3 full record | 32.0 | 100% |

Byte counts said B5 leaks ~0.3× of B3. **Entropy says 3% versus 100%** — the byte proxy understated
selective adjudication by an order of magnitude. Conservative direction, but wrong.

### E12 · Steady-state economics

Disputes are rare; every measurement above concerns the dispute. At `N = 10⁶` delegations and a
1-in-10⁵ dispute rate, **adjudication is under 0.001% of total cost.** The deployed default is
~12× cheaper at idle.

> **A scheme is adopted on its idle cost, not its dispute cost.** That, not ignorance of the
> accountability literature, is why bearer tokens plus a log persist despite scoring 0.20.

Every optimisation in this project targeted that 0.001%.

---

## 6. Consolidated baseline results

**Regenerate rather than cite this table** — see `results/canonical.txt`.

| baseline | correct | false acc. | over-attrib. | missed | worst-class |
|---|---|---|---|---|---|
| B0 | 0 | 0 | 0 | 325 | 0.00 |
| B1 | 275 | 25 | 100 | 50 | 0.00 |
| B2 | 150 | 0 | 25 | 200 | 0.00 |
| B3 / B4 / B5 | 250 | 0 | 100 | 75 | 0.00 |
| B6 | 275 | 0 | 100 | 50 | 0.00 |
| B7 | 300 | 0 | 100 | 25 | 0.00 |
| B9 | 0 | 0 | 0 | 100 | — |
| **B10** | 0 | 0 | **0** | 75 | **1.00** |
| B11 | pattern | 23 (M21) | 0 | — | — |

Under **adversarial class selection**, every baseline through B6 scores 0.00. The ladder
0.80 → 0.87 → 0.93 reported under uniform sampling is an artifact. Coverage, not accuracy, is the
correct metric.

---

## 7. Prior art

> **Scope refreshed, 15 August 2026.** The surrounding field moved while this project was being
> hardened. In addition to A2A/MCP and protocol-gap analyses, current work now includes DRP's
> signed delegation receipts, HDP's signed delegation provenance, FIDO's AP2/Verifiable Intent
> work, and NIST's agent-standards initiative. See
> [`docs/prior-art/2026-protocol-landscape.md`](docs/prior-art/2026-protocol-landscape.md).
> The defensible claim is therefore not that verifiable authorization is absent. It is that
> **authorization/provenance evidence and adversarial adjudication are different questions**, and
> this harness measures the latter under repudiation, withholding, abort and sincere mistake.

Four rounds of review. The construction the project set out to build was occupied; the property it
set out to claim as novel was present in four pre-2011 lines.

**Occupied.** South et al. (arXiv 2501.09674) anchor authenticated delegation over OAuth/OIDC.
Prakash's invocation-bound capability tokens claim the attenuated-token lineage. Open Agent
Passport, PAuth and PCAS hold pre-action authorization. Parakhin proves TTL revocation fails at
agent execution speeds. AuditableLLM covers hash-chained audit. MCP-I → KYA-OS (DIF, March 2026),
the CSA Agentic Trust Framework, and IETF AIMS over SPIFFE/WIMSE hold the standards space.

**The accused party's defence, 1996–2010.** Zhou–Gollmann non-repudiation; Asokan–Shoup–Waidner
optimistic fair exchange; PeerReview's accuracy theorem (a correct node can always defend itself
against false accusation); Rial & Preneel's optimistic fair priced oblivious transfer. In the
specific 2024–26 identity/delegation proposals originally reviewed for this project, I found none
of those four lines cited. That observation is scoped to that reading, not to the whole 2026 field.

**Inference verification.** Cankaya (arXiv 2606.00279) establishes that LLM inference is bit-exactly
deterministic given five mostly-static recorded factors plus one integer per forward pass — so
recovering determinism does *not* cost disclosure. zkLLM (CCS 2024) hides **model weights, not
inputs**, and assumes a **semi-honest verifier** following the standard zkML framework; at ~13 min
proving per inference on a 13B model it is impractical at agent-trajectory scale. Neither verifies
that an action fell within a granted scope: **verifying `f(x)=y` is not verifying that `y` was
permitted.**

**What changed during 2026.** Otsuka, Toyoda & Leung (arXiv 2604.23280) prioritise recent sources
by methodology, but the practical gap around delegation evidence is now being attacked directly:
DRP signs and logs authorization before execution; HDP carries signed delegation provenance; and
FIDO's AP2/Verifiable Intent work treats user intent as portable cryptographic evidence. These do
not erase the fair-exchange comparison. They narrow it: the open question here is what such
artifacts can settle under adversarial disagreement, not whether verifiable authorization exists.

---

---

## A note on the unverified reading

The regression claim rests on reading PeerReview's accuracy theorem as protection against a
dishonest *principal*, not merely against a faulty peer. **The source does not explicitly confirm
that transfer**, so it is treated here as an extension rather than an endorsed interpretation.

What this means for how the claim should be phrased:

- **State it from the primary source.** PeerReview's accuracy property is proved in Appendix A of
  the technical report: no correct node is ever exposed by a correct node, and none is forever
  suspected. Cite the theorem, not an interpretation of it.
- **Do not claim the authors endorse the transfer.** The move from "correct node defends itself
  against a faulty peer" to "correct executor defends itself against a dishonest principal" is
  made here. It is well supported — the model explicitly spans mutually distrusting administrative
  domains — but it is an extension, and should read as one.
- **The regression claim does not depend on it alone.** Three further lines carry the accused
  party's defence independently: optimistic fair exchange (symmetric by construction), Zhou–Gollmann
  non-repudiation (evidence for both origin and receipt), and Rial & Preneel, whose stated motivation
  names a malicious buyer accusing an honest vendor who cannot disprove it. Even if the PeerReview
  reading were over-extended, the pattern survives on the other three.

The honest form of the historical claim is therefore scoped: **four research lines between 1996
and 2010 protect the accused party, and the specific identity/delegation proposals originally
reviewed here did not cite them.** The broader 2026 landscape now contains adjacent evidence and
provenance work, documented in `docs/prior-art/2026-protocol-landscape.md`; the comparison should
be maintained as a dated review rather than promoted to a universal absence claim.

## 8. Limitations

- **No cryptography is executed.** Merkle trees are real and measured; signatures are accounted at
  96 B and never computed.
- **The mistake classes are constructed, not observed.** Nothing here shows humans misremember
  authorizations at a meaningful rate. Plausible, matches ordinary experience, still an assumption.
- **`p₀ = 0.25`** (honest record-loss rate) is invented and determines E9's entire operating point.
- **Two parties, one adjudicator.** P5 degenerate; T2's bound will change shape under colluding
  complainants.
- **No clock.** Revocation, staleness and ordering are absent, though M16 gestures at them.
- **Flat scope labels.** Semantic ambiguity (`write:records ⊂ write:*`) is untestable.
- **Key ≡ party (A14).** Every baseline treats a signature as a statement by its key-holder. T9 shows
  this fails under compromise, and B10's Pareto dominance depends on it.
- **No channel model (A12).** Unreliable / resilient / operational assumptions are unstated, though
  every guarantee in the surveyed literature is conditional on them.
- **Rational self-interest assumed but never stated (A13).** An adversary indifferent to its own
  exposure breaks B6's query defence.
- **The M-class taxonomy is a reconstruction** pending reconciliation with the author's
  authoritative list. Every result is conditional on it.
- **Coverage is unproven.** That 34 classes span the adversarial space is an assumption, not a
  result. The coverage audit derives the assertion x withholding space and finds 8 of 106
  structurally possible cells occupied. One unoccupied cell turned out to matter (RC-H9); others
  may.
- **Every audit is self-audit**, including the audits of the audits. There is no independent
  implementation, no external review, and no third-party test vectors for the Merkle code. A
  shared misconception between implementation and tests would survive undetected.
- **The disclosure byte model is stipulated.** Protocols are comparable to one another under one
  encoder. The crossover point moves with the encoding; the existence of a crossover does not.
- **Static adversary in E9.** A rate-adaptive adversary tracking its own p-value would do better.
- **Independent disputes assumed.** Correlated failure would inflate false accusations further.

---

## 9. Corrections made during the study

Recorded because the pattern is instructive: every one was found by chasing an anomaly, not by
reading a summary.

### 9a. The six declaration defects

A second class of correction emerged during the hardening phase, and it is more instructive than
the first. Six **stated claims** were wrong, all with the same shape — a universal statement
inferred from the subset in view:

| | claimed | actually |
|---|---|---|
| F-H3 | M1/M16 is an evidential twin | M1 conceals, M16 admits; never a twin, and wrong since the corpus was built |
| RC-H9 | withholding is modelled | executor-only; the principal never withheld in the pre-fix corpus |
| RC-H10 | M22 resists every mechanism | resists the commitment-only family; full disclosure solves it at the cost of M23 |
| RC-H12a | PRINCIPAL_LIAR is the F01 denominator | it excluded three classes where bilateral commitment scores 0, exactly as the default does |
| RC-H12b | bindability is per class | per class it is false; the criterion is pairwise, and coincides exactly with the conservation boundary |
| RC-H14 | B4 is uncited and prunable | it carried an unwritten negative result: exhaustive querying costs 35% more for identical resolution |

None was found by re-reading. All six were found by **deriving the structure from the code and
diffing it against the declaration**. Each is now a stage in `make check`, so the corresponding
claim is recomputed on every run rather than trusted.

The generalisable lesson: *anything hand-maintained should be recomputed against the code, with
the recomputation failing the build on disagreement.* A closely related one: "checked" always
needs "in what dimension" attached — a numeric staleness checker passed cleanly while five
documents carried refuted **reasoning**.

#### RC-H15 — the publication review found the declaration checker was right and the build was wrong

After M32 (principal abort before acknowledging delivery) was added, the non-assertional F01 set
still named only M13/M26/M28. `src.validation.declarations` derived the principal-dishonesty
population from corpus ground truth and correctly returned non-zero on the mismatch. `make check`
nevertheless printed its success banner because the validator output was piped through `tail`; the
shell propagated `tail`'s zero status rather than the validator's failure.

The correction is intentionally redundant: M32 is now in the declared non-assertional population;
`tests/test_claim_regressions.py` independently derives the F01 populations and denominators; the
Makefile enables `pipefail`; and `gate-selftest` deliberately runs a failing left-hand pipeline and
requires the gate to observe it. The non-assertional result is now B0 0/100, B1 0/100, B13 50/100,
B17 100/100.

This adds a second clause to the methodological lesson: **recomputing a claim is insufficient if the
recomputation's failure is not wired to control the build.**

### 9b. Earlier corrections

1. **Analytic proof sizes** understated real Merkle proofs by 2–5× (hex + JSON framing).
2. **Measurement bias in my own favour** — records serialized as JSON while proofs were packed
   bytes, inflating the full-disclosure baselines. Fixed; the crossover moved from 0.20× to 0.34×.
3. **Evidence-availability leak** — baselines read ground-truth actions even when the record was
   unavailable, consulting evidence the adjudicator could not have had. Fixing it produced T5.
4. **M4 mutation never fired** — `rng.choice` re-evaluated inside a comprehension.
5. **B0's "spurious" verdicts were correct behaviour** reached by incapacity; the scorer was wrong.
6. **T1's escape overstated** — three-state schemes suspend in both worlds; they do not expose in
   the dishonest one.
7. **Paired test run on pairs that were not twins** — M19/M10 and M20/M21 were never seeded together,
   so the adversarial member carried an out-of-scope action its twin lacked. The test measured
   detection of the overreach, not of the ambiguity it was meant to isolate.
8. **The attestor was given custodial power** — B16 read execution contents from an unproduced
   record. Corrected by splitting into a digest-only attestor (closes nothing) and a custodian
   (closes the residual by relocating it).

9. **The scorer masked misses** — a mistaken co-party caused an unblamed wrongdoer to score as
   correct. Found by `scorer_audit.py` property P3, written because the scorer was the largest
   surface with no structural check.

**The pattern across all nine: errors flatter the hypothesis.** Every one made the scheme under test
look better than it was. The countermeasures that have actually worked are structural rather than
vigilant — the scenario validator, and `visibility.py`, which converts "remember not to read ground
truth" into something the code enforces. Anything relying on care alone has failed at least once.

---

## 9c. Results from the hardening phase (findings 09-13)

Five experiments postdate the original twelve. Each has a full write-up in `docs/findings/`.

**Witness-carrying messages (B13, finding 09).** A message chain where each party holds the
counterparty's signature over the same commitments. The decisive property was not the countersigned
chain but **root recomputation from a party's own assertion**: recompute the commitment root from
what a party claimed and compare. Every earlier baseline compared assertions to the *true* set,
which made commitment-only adjudication look semantically blind. It is blind only to facts nobody
asserted. Disclosure is flat in record size (354 B at scope 2, 360 B at scope 64, against
237 → 1374 B for full disclosure).

**The duty to answer (B17, finding 10).** B13's residual is exactly the classes where a party
asserts nothing, so the refuge is *silence, not loss*. Compelling an answer resolves the guilty
withholding classes and breaks their honest twins **one for one**: 125 misses become 125 false
contradictions. The cost does not shrink; it changes who bears it. B17's false-attribution rate
remains 0% because it never names anyone — an attributive version of the same mechanism would have
produced 125 false accusations, which is the concrete argument for the non-attributive vocabulary.

**Symmetric withholding (finding 11).** The exchange above was measured on a corpus where only the
executor ever withheld. Four principal-side mirror classes make the conservation exactly symmetric,
confirming it is a property of the structure rather than of the corpus.

**The conservation boundary (finding 12).** The central result, stated in the abstract. It refuted
RC-H10 and subsumed T4; it also makes B17's one-for-one exchange a *consequence* rather than a
discovery, since all the pairs it trades across are binding pairs.

**Abort (finding 13).** Every earlier class assumed the message chain completes. Four abort classes
show that B13 misses an executor abort outright — the principal never receives the execution
receipt, so it holds no commitment to check against — and that B13's "no false contradictions
anywhere" becomes "none except on the abort leg". An abort hides the **commitment**, not the
contents: under full disclosure the overreach is plainly visible. Fair exchange now has a concrete
target rather than a literature citation.

---

## 10. Reproduction

```bash
python3 -m pip install -e ".[dev]"
make check
make experiments
```

`make check` is the correctness gate; `make experiments` regenerates the checked-in result
artifacts only after that gate passes. Runtime code supports Python 3.12+ and uses the standard
library only; `pytest` is the development/test dependency. CI exercises Python 3.12 and 3.13.
Generation is deterministic in `(m_class, seed, index)` with seed `20260808`.

---

## 10a. Insights from the fair-exchange family (added after §7 reads)

Reading Rial & Preneel (2010) properly — see `docs/prior-art/rial-preneel-2010.md` — produced
three findings, one of which partly inverts a design conclusion here.

**Verifiability by construction dissolves the disclosure question.** Their adjudicator verifies
protocol messages, not records: request verification needs no vendor secret key, response
verification needs no buyer choice. Disclosure at adjudication is **zero by construction**.
Baselines B2–B6 treat disclosure as a dial turned at dispute time, and T3's crossover formula is
an artifact of that framing. T3 is not wrong; it answers a question a better protocol design does
not have to ask.

**Powerless beats accountable.** Their privacy holds *even if the adjudicator is corrupted*. B7
answers adjudicator collusion by making the adjudicator accountable; they make it incapable. This
inverts the through-line this project ran on — accountability is what you reach for when you
cannot achieve incapacity, and the second-best answer was treated here as the only one.

**T8 is confirmed from outside.** Their adjudicator can *compel* production, and the
fair-exchange family resolves non-response by timeout and ruling against the silent party — which
also rules against the genuinely unlucky. That is a T8 denomination, chosen deliberately, in a
different literature, twenty-five years earlier. It is the strongest external evidence that the
conservation property is real rather than an artifact of these baselines.

### From Kremer, Markowitch & Zhou (2002)

Read in full; see `docs/prior-art/kremer-markowitch-zhou-2002.md`. Six further findings.

**T8 gains a fifth currency, and is now the best-supported result here.** Probabilistic
fairness — a protocol is ε-fair if a fair outcome occurs with probability ≥ 1−ε — buys the
elimination of the trusted third party entirely, paid for in *probability of unfairness*. With
single-state, three-state, stateful and bonded, that is **five mechanism families across three
literatures, each paying the same conserved cost in a different currency, each having chosen its
currency deliberately.**

**T5 generalises into excuse-ranking.** Their §7 treats signature-key revocation: a compromised
key retroactively invalidates evidence already issued. Claiming *key compromise* dominates
claiming *record loss* — equally unprovable, and destructive of existing evidence rather than
merely absent. So: **a rational adversary occupies the excuse that is both indistinguishable from
honest misfortune and maximally destructive of evidence.** Any scheme must rank its available
excuses. Their countermeasure — short-term *irrevocable* keys — works by removing the excuse and
accepting a bounded compromise window, which is itself a T8 denomination.

**T4's criterion appears instantiated in 2001.** Their transparent-TTP protocol includes an *error
protocol*: Alice commits to `h(k)` but submits `E_TTP(k')` with `k' ≠ k`, and the TTP proves the
mismatch. Attribution works there for exactly the reason T4 predicts — the cheat is a *concealing
act*, not an assertion. The key hash was placed in the signed evidence specifically to make
substitution detectable. **Soften T4's novelty claim:** the criterion is implicit in protocol-design
practice even if unnamed.

**Weak fairness supplies a verdict state absent here** — `imbalance-proven`: a proof that one party
was disadvantaged, making no claim about cause. It sits between `contradicted` and `exposed`, and
unlike `suspected` it is **not consequence-free**, since the proof is actionable outside the
protocol. A candidate replacement for the refuge T5 exposed.

**Statefulness is mandatory, for a sharper reason than measured.** Timeliness requires an abort
protocol mutually exclusive with recovery, enforced by per-run TTP state. B11's cross-dispute
statefulness is optional; per-run statefulness is not.

**Two implicit assumptions surfaced.** A channel model (unreliable / resilient / operational —
every guarantee is conditional on it, and the harness has none) and *rational self-interest* (their
§2.2, assumed implicitly throughout here; an adversary indifferent to its own exposure breaks
B6's query defence).

**Retired:** the parked fingerprinting-as-disclosure observation. Transparent TTPs solve it, with a
definition, a named property, and an efficient construction from 2001, motivated by the same
concern.

**Suggested B13:** witness-carrying messages — grant and execution each bearing a publicly
verifiable correctness witness, with an adjudicator that checks witnesses and never inspects
records. If disclosure goes to zero at full coverage, B2–B6 are superseded rather than refined.

---

### M22/M23, B15 — excuse ranking and key compromise (Findings 06)

Built from K5. M22 and M23 are evidential twins, **25/25 byte-identical**: in both, the committed
record holds an out-of-scope action signed with the executor's key and the executor claims
compromise. In M22 the executor did it and lies; in M23 a thief with the stolen key did it and the
executor is honest. *Did you do it, or did the thief?* The evidence cannot say.

> **T9.** The non-attributive escape from T4 does not survive key compromise. `contradicted` is a
> claim about **the key**, not the person — and when the key is stolen, binding the key binds the
> wrong party. B10 and B15 both false-accuse on M23, 25/25.

**This qualifies T6.** B10's Pareto dominance holds only under an unstated assumption: that a
party's key is a faithful proxy for the party. State that wherever T6 is claimed.

**The excuse hierarchy is confirmed by measurement.** Tampering while producing the record is
provable and caught 25/25. Claiming record loss is unprovable and missed by every baseline.
Claiming key compromise is unprovable *and retroactively destructive*, and defeats B7 as deployed.

**B15 (short-term irrevocable keys) removes the excuse and hands the bill to the honest party.** It
recovers full adjudication on M22 — and false-accuses on M23 25/25, because a genuinely compromised
party is bound to every signature made inside the window, including the thief's. **T8 confirmed a
sixth time**, and the first case where the currency shift is documented by the original authors as
a deliberate choice: the short lifetime makes the residual risk *acceptable*, not absent.

---

### Minimal commitment sets — T4 inverted (Findings 07)

T4 was used as a diagnostic. Inverted it becomes a construction: **given a set of dishonest
behaviours, what is the smallest set of commitments that makes every one concealment-requiring
rather than assertional?**

For this corpus, **four commitments suffice** — signed grant, signed execution record, signed
delivery acknowledgement, and public message witnesses — covering all fourteen bindable adversarial
classes. Ablation confirms minimality: dropping any one leaves acts unbound, with the signed grant
carrying ten of them.

> **T10.** A dishonest act is bindable iff its false assertion concerns a *particular fact existing
> at commitment time*. It is **residual** iff the assertion concerns an *event postdating every
> commitment* (record loss, key compromise) or an *aggregate property of the party's own future
> behaviour* (a rate). **You cannot commit to a proposition about your own future misfortune.**

Three classes are residual — M19 (claimed loss), M22 (claimed compromise), M20 (claimed rate) — and
under the **paired test** (can any baseline catch the adversarial class *without* condemning its
honest twin?) every bindable class is separable and **no residual class is**, across twelve
baselines. The three commitments aimed at the residual — retention promises, short-term keys,
retained history — bind nothing.

This is a stronger impossibility than T1: T1 concerns a given indistinguishable pair; T10 says a
class of dishonest acts exists that **no protocol design can make attributable**, because the
binding commitments are unmakeable in principle rather than merely absent.

**It explains two earlier results.** The excuse hierarchy of Findings 06 *is* the residual set,
ordered by destructiveness — an adversary needs a claim about a fact postdating the commitments,
not a clever lie. And T8 follows: conservation holds *because* the residual is non-empty. Where
nothing can be bound, cost can only be moved. **T10 is the cause; T8 is the consequence.**

A failed prediction sharpened it. M20 was first classified bindable via retained history; the paired
test refuted it. **Adjudicator-held observation is not a party-made commitment** — a party cannot
contradict a record it never made — which is independently confirmed by T7, where statefulness
converted a miss into a false accusation rather than binding anything.

**Chief threat to T10:** external attestation. A hardware root of trust could testify that a record
existed or a key was uncompromised. The prediction is that this *relocates* the residual to the
attestor rather than closing it, since the attestor then becomes the unbindable party. Build as B16
before T10 is claimed in print.

---

### Attestation, relocation and level invariance (Findings 08)

**This section replaces an earlier version that over-claimed twice.** Both errors are recorded in
§9; both made attestation look like it worked.

T10's chief threat was external attestation: have someone *else* commit, since the residual argument
turns on a party's inability to commit about itself. Testing it required fixing two defects first —
pairs that were never seeded as twins, and an "attestor" that read execution contents from an
unproduced record, which makes it a custodian rather than an attestor. `src/visibility.py` now
enforces the visibility rule structurally: **availability gates everything else about a record.**
Under it, all six adversarial/honest pairs verify as genuine twins, 25/25.

**Corrected result.** A digest-only attestor — one that proves a record existed and was intact, but
cannot say what it contained — closes **none** of the three residual classes. Only *custody* closes
them, and custody relocates the whole residual to the custodian (M24: attestor outage with a guilty
executor, missed 25/25).

> **T11.** Attestation of existence and integrity closes nothing. Only custody closes the residual,
> and it relocates the residual wholesale to the custodian, which equally cannot commit that its own
> record will remain available. The choice is not *attest and be safe*; it is *move the problem to
> someone else*.

That is the trusted-third-party bargain the fair-exchange literature has always been explicit about,
and it explains why that literature works to **reduce** what a TTP must be trusted with rather than
adding attestors.

> **T12 (Level invariance).** The accuracy/completeness dichotomy recurs at every level — record
> (T1), rate (T7), commitment (T10), custodian (T11). Adding a level relocates it. Nothing removes
> it.

T12 supplies the derived characterisation of the commitment space that T10 had only enumerated:

> **A commitment binds iff breaching it is distinguishable from being unable to fulfil it.**

T1's structure applied to commitments rather than records. *"I will produce my record on demand"* is
well-formed and binds nothing, because breach and incapacity look identical. T10's original
criterion — *facts postdating commitment* — is a **consequence**, since future events are precisely
those whose non-occurrence cannot be demonstrated.

**The causal chain closes.** T12: the dichotomy exists at every level. T11: adding levels moves it.
T10: no commitment escapes it. **T8 is what that looks like from outside** — if it cannot be removed
anywhere, the only remaining freedom is who pays.

The project began looking for a primitive. It ends with a structural reason no primitive would have
helped.

---

### Scorer audit and p₀ sensitivity (required-before-publication checks)

**The scorer was wrong, and the bug was exactly where predicted.** `scorer_audit.py` enumerates the
full cross-product of ground-truth states and verdict shapes (450 combinations) and asserts seven
properties: totality, outcome reachability, no masked misses, party symmetry, blaming-an-honest-party,
non-attributive exactness, and unadjudicable handling.

Property 3 failed in 15 combinations. **A mistaken party masked a genuine wrongdoer:** in any mixed
scenario — principal misremembers *and* executor cheats — a scheme that flagged the conflict but
blamed nobody scored `correct_contradiction` instead of `missed`. The fix guards that branch on there
being no unblamed dishonest party. Impact: B0 loses 25 spurious credits on M18; other baselines are
unaffected on aggregate because they do blame someone there.

This was the ninth self-correction, and the first found by a structural check *written specifically
because no structural check existed* — rather than by chasing an anomaly after the fact.

**p₀ sensitivity (E13).** T7's operating point rested on an invented honest-failure rate of 0.25.
Swept from 0.05 to 0.50 at n = 20:

| p₀ | false accusation on honest | detection power at 2×p₀ | adversary ceiling |
|---|---|---|---|
| 0.05 | 0.016 | 0.13 | 0.18 |
| 0.15 | 0.022 | 0.39 | 0.32 |
| 0.25 | 0.041 | 0.75 | 0.42 |
| 0.50 | 0.021 | 1.00 | 0.72 |

**T7's qualitative claim is robust** — the false-accusation rate is above zero and detection power
below one at every value tested, so statefulness always trades a miss for a false accusation. It is
not an artifact of 0.25.

What *does* move is the adversary's misconduct ceiling, which tracks p₀ almost proportionally. That
is a new consequence not visible at a single value:

> **The tolerable rate of undetected concealment is set entirely by how often honest parties
> genuinely fail.** Reliable infrastructure bounds the adversary tightly; flaky infrastructure hands
> the adversary exactly the slack it gives the unlucky. **The price of unreliability is paid twice —
> once in honest failures, and again in the concealment those failures cover.**

---

## 11. Open questions

Renumbered and re-prioritised after the hardening phase. Items 7 (B13) and the channel model have
since been answered; what remains is ordered by what would change most.

1. **Prevalence of principal misremembering.** Unmeasured, unmeasurable inside this harness, and
   the parameter every deployment-safety argument turns on. **The single largest gap.** Needs real
   agent traces.
2. **Whether repetition escapes the conservation boundary.** `B11_stateful` is scored per scenario,
   so a claim about a party's history cannot demonstrate its value one scenario at a time. Whether
   repeated interaction genuinely escapes the boundary or merely changes the unit of analysis is
   the most interesting untested question here, and it needs a repeated-interaction harness.
3. **A faithful fair-exchange baseline.** Now with a concrete target: M30, the executor abort that
   B13 misses. This is also the only available test of T12 relocation, since no other mechanism in
   the set introduces a new trusted party except by declared entitlement.
4. **External validation.** No independent implementation, no external review, no third-party
   Merkle test vectors. Every result here is conditional on the harness being right about itself.
5. **Coverage of the class space.** 8 of 106 structurally possible cells are occupied. One
   unoccupied cell mattered; the audit cannot say whether others do.
6. **`key ≡ party` (T9)** as a separate line — the one impossibility here that attestation of
   *identity* rather than *records* might close.
7. **Cross-dispute profiling as a disclosure channel.** Invisible to every measurement taken here.
8. **Multi-party chains.** Equivocation stops being degenerate; T2's bound changes shape.
9. **Time and revocation** as a dimension; the compromise window measured against dispute arrival
   rate rather than scored as removed outright.
10. **Rate-adaptive adversaries** against the binomial test.
11. **Whether the T4 concealment criterion is novel** or folklore within the BFT community. Note
    that T4 is now subsumed by the conservation boundary, which may change the answer.
12. **Semantic scope.** Flat labels make `write:records ⊂ write:*` untestable.

---

## 12. Publication readiness

Stated plainly, because the honest answer is mixed and the distinction matters.

**What is publishable now.** The harness and corpus are a genuine artifact contribution: an
executable, deterministic, adversarially-structured benchmark for a question that authorization and
provenance artifacts do not answer by themselves — which account can be defended when the parties
disagree about the record. The negative results are real and reproducible. The historical observation
in §7 remains useful in scoped form: self-defence for a correct party is present in four research
lines from 1996-2010, and the specific identity/delegation proposals originally reviewed here did not
cite them. The broader 2026 field now includes adjacent DRP, HDP and AP2/Verifiable Intent work, so
absence from "the agentic literature" is no longer claimed. The record of six hardening-time
declaration defects plus later publication/freshness drifts, and the build stages written to catch
them, is a methodological contribution of the kind that is usually omitted from papers and shouldn't
be.

**What is not.** The conservation boundary, once stated, has a one-line proof. It is useful and it
is checkable, but a cryptography venue will correctly observe that "a function of X cannot
distinguish inputs identical in X" is not a deep theorem. The value is in the *framing* — that
accountability mechanisms are functions of an evidence projection, and that the projection's
fibres determine the achievable verdicts — not in the mathematics. Framing it as an impossibility
result would oversell it and invite a reviewer to say so.

**Where this fits.** An artifact/benchmark track, a systematisation or negative-results venue, or
a workshop on agentic security. Not a top-tier crypto venue: there is no new primitive, and none
was found. An arXiv preprint plus the repository would be a reasonable first move, and the
author's Medium outlet is a legitimate route for the historical argument, which is the part most
likely to change what practitioners do.

**Before submitting anywhere, three things are load-bearing:**

1. **Reconcile the M-class taxonomy** against the author's authoritative list. Every result is
   conditional on it and it is currently a reconstruction.
2. **Get one external reader** on the harness, ideally someone who will try to break the
   visibility invariant. Six self-corrections is evidence the method works, and also evidence that
   a single author misses things for weeks at a time.
3. **State prevalence as unmeasured in the abstract**, not only in the limitations. It is the
   parameter that decides whether any of this matters in deployment, and burying it invites the
   overclaim this study exists to criticise.
