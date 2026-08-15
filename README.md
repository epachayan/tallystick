# Tallystick

**An adversarial harness for accountability in delegated agentic action.**

850 scenarios · 34 adversarial classes · 18 adjudication baselines · 158 tests · 13 gate stages

New here? Start with [`START-HERE.md`](START-HERE.md), browse the complete
[`INDEX.md`](INDEX.md), or read [`CONTRIBUTING.md`](CONTRIBUTING.md) before making changes.

---

## What this is

Systems that delegate authority to AI agents increasingly promise *accountability* -
cryptographic evidence tying an action to a responsible party. This repository is a corpus and
harness for testing that promise adversarially, plus the record of what it found and what it got
wrong along the way.

It is a **measurement instrument and a negative-results record**, not a new cryptographic
primitive. No new primitive was found. What the work produced instead is a boundary on what any
evidence-based mechanism can do, an executable corpus that makes the boundary checkable, and a
documented account of six hardening-time declaration defects and a seventh declaration drift found during publication review.

### The headline result

> **The conservation boundary.** Where two worlds produce identical evidence **and differ in
> whether any account diverges from the record**, no evidence-determined mechanism resolves both.
> The cost can be denominated - as false accusation, as missed detection, as disclosure, as
> padding - but not removed. Where the worlds differ only in the *intent* behind a divergence both
> exhibit, a non-attributive vocabulary resolves both at no cost.

Plainly:

> Twins differing only in **why** a divergence occurred are escapable.
> Twins differing in **whether** one occurred are not.

The proof is one line - identical evidence yields one verdict, so the only question is whether one
verdict can be correct in both worlds. The useful part is not the proof but the **boundary**: it
predicts where a mechanism can win and where it cannot, across every twin pair and every protocol,
and `make check` recomputes that prediction on every run.

Full write-up: [`RESEARCH.md`](RESEARCH.md) · Claim strength:
[`docs/what-is-established.md`](docs/what-is-established.md)

---

## Selected findings

| | finding |
|---|---|
| **The deployed default provides no defence** | Bearer token + executor-maintained log scores **0 of 100** on assertional principal-side dishonesty. Bilateral commitment scores 100 of 100. |
| **...but only when there is an assertion to contradict** | On four non-assertional principal-side classes - baseless complaint, withheld records, and abort-before-ack - bilateral commitment scores **0/100, exactly as the default does**. Witness messages reach 50/100; duty-to-answer reaches 100/100. |
| **Evidence proves contradiction, not culpability** | A principal who *misremembers* and one who *lies* produce byte-identical evidence. An attributive baseline accuses the sincerely mistaken wherever a mistake class appears. |
| **A commitment can be checked without opening it** | Recomputing a commitment root from a party's *own assertion* costs no disclosure and reaches concealment no query can name. Disclosure stays flat in record size. |
| **The refuge is silence, not loss** | Mechanisms fail exactly where a party asserts nothing. Compelling an answer resolves those classes and breaks their honest twins one-for-one. |
| **An abort hides the commitment, not the contents** | An executor that acts then withholds the execution receipt leaves the principal with nothing to check against - and is fully visible to an adjudicator that can read the record. |
| **No mechanism is adversarially complete** | Every one of the 18 baselines has at least one class it fails on **every** instance. |

---

## What is *not* established

Stated up front because these are the tempting things to quote.

- **Prevalence.** How often a principal genuinely misremembers a delegation is unmeasured, and it
  is the parameter every deployment-safety argument turns on.
- **Absolute cost.** The disclosure byte model is stipulated, not a wire format. Protocols are
  comparable to each other; the numbers are not a cost model for anything real.
- **Coverage.** That the class set spans the adversarial space is unproven. The coverage audit
  finds 8 of 106 structurally possible cells occupied.
- **External validation.** Every audit here is self-audit, including the audits of the audits. No
  independent implementation, no external review, no third-party Merkle test vectors.

Full ledger, in three tiers: [`docs/what-is-established.md`](docs/what-is-established.md).

---

## Quick start

```bash
python3 -m pip install -e ".[dev]"   # installs the test dependency (pytest)
make check                         # 13-stage correctness gate
make experiments                   # depends on check; regenerates results/
make taxonomy                      # regenerates docs/taxonomy.md from the code
make ext-check                     # standalone A2A reference-library tests
make ext-experiments               # A2A adapter parity; does not add a protocol
```

**Runtime:** Python 3.12+, standard library only. **Development/test dependency:** `pytest`.
CI exercises Python 3.12 and 3.13. Deterministic from seed `20260808`.

`make experiments` will not run on a failed gate. Five of the gate stages exist because a
hand-maintained declaration was found to be wrong.

---

## Repository layout

```
corpus/     scenarios, one JSON object per line
schema/     scenario.v0.2.schema.json -- structural contract
src/
  model/      evidence projection, dispute construction, types
  protocols/  the baselines (evidence-only: no protocol can read ground truth)
  scoring/    scorer + metrics (single definition, single choke point)
  validation/ the gate stages
  reporting/  harness, run, sweep, regression
  extensions/ standalone reference libraries, outside corpus scoring
examples/    runnable reference-library and harness-replay walkthroughs
results/    canonical figures, regenerated by make experiments
docs/       research record, findings 01-13, proofs, prior art, and evidence maps
```

**Architectural invariant:** a protocol receives `(EvidenceView, disputes, ProofOracle)`. No
argument carries ground truth. This is enforced structurally and verified by mutation testing -
4,576+ hidden-field mutations, zero verdict changes, with a deliberately-leaking protocol used to
prove the check is not vacuous.

---

## On the corrections

Six declaration defects were documented during hardening, all with the same shape: a universal
statement inferred from the subset in view. They included a twin declaration wrong since the corpus
was built, withholding modelled for one party only, a class described as resisting every mechanism
when it resisted one family, an F01 denominator that excluded the classes where the headline
mechanism does no better than the baseline it beats, a bindability criterion evaluated per class
instead of per twin pair, and a protocol carrying a negative result nobody had written down.

A final publication review found a seventh declaration drift: M32 had been added to the corpus but
not to the non-assertional F01 population. The declaration auditor detected it, but a shell pipeline
masked the validator's non-zero exit code. `make check` now runs with `pipefail`, includes a gate
non-vacuity stage, and has dedicated headline-claim regressions. A later freshness pass also found a
stale `26 / 650` narrative literal in the generated summary; that line is now derived from the
corpus and pinned by a regression. See `docs/test-evidence-map.md`.

Every one was found by **deriving the structure from the code and diffing it against the
declaration** - never by re-reading the prose, and never by the tests that existed at the time.
Each one is now a gate stage. The supporting regressions are mapped in
[`docs/test-evidence-map.md`](docs/test-evidence-map.md).

---

## Citation

See [`CITATION.cff`](CITATION.cff). Author: Nitin Stephen Koshy
([ORCID 0009-0009-2690-0588](https://orcid.org/0009-0009-2690-0588)).

## License

See [`LICENSE`](LICENSE).
