# Test and result evidence map

**Date:** 15 August 2026  
**Corpus:** 850 deterministic scenarios, 34 adversarial classes, 25 instances per class  
**Protocols:** 18 adjudication baselines  
**Pytest suite:** 158 tests  
**Build:** `make check` adds structural validators and a gate-propagation self-test around the pytest suite

This document answers a narrower question than `RESEARCH.md`: **which executable checks support each
headline statement, and what would have to fail for the statement to stop being true?** It is not a
claim that 158 tests prove the corpus is complete. They prove specific invariants inside the modelled
world and are named below.

---

## 1. Corpus integrity and evidence isolation

**Claim.** Protocols adjudicate from observable evidence, not from the scenario's hidden answer key.

**Primary checks.**

- `tests/test_integration.py::test_corpus_size` pins 850 scenarios / 34 classes.
- `test_corpus_validates_against_schema_v0_2` checks structural validity.
- `test_corpus_is_semantically_coherent` checks cross-field invariants.
- `test_no_protocol_reads_hidden_state` runs the visibility mutation audit.
- `test_visibility_check_catches_a_real_leak` injects a deliberately leaking protocol and requires
  the visibility checker to reject it. This is the non-vacuity check for the visibility invariant.
- `test_evidence_view_excludes_ground_truth` and `test_protocol_signature_takes_no_scenario` pin the
  architectural boundary: protocol functions receive `EvidenceView`, disputes and a proof oracle,
  not the raw scenario.

**Current result.** All pass. The visibility mutation stage also mutates thousands of hidden fields
outside pytest and requires verdict stability.

**What this does not prove.** A shared modelling error in both the projection and its tests could
still survive. There is no independent implementation.

**And the gate itself is load-bearing.** With 11 validator stages behind one banner, a claim of
"gate passed" is only as good as the gate's own integration. RC-H15 is the demonstration that this
can fail silently: the validator was correct and its exit status was discarded. `gate-selftest`
pins that specific failure mode. It does not pin the next integration mistake of a different shape,
and a second such defect would look exactly as green as the first one did.

A worked example of the same blind spot, found while reviewing this document: the pytest suite size
is quoted in live documents, and the staleness checker parsed corpus size and class count but
not the suite size. An earlier report carried a figure from an earlier phase, roughly two-thirds
of the current one, and passed the numeric gate cleanly. The checker now derives the
count from `pytest --collect-only` and diffs it. **A check is only ever as wide as the forms it can
read.**

That fix has its own edge, worth naming rather than discovering later: a document *discussing* a
corrected figure looks identical to one *asserting* it. This paragraph originally quoted the stale
number verbatim and tripped the new check on its first run. Descriptions of past figures are
therefore written without the bare numeral. The alternative — teaching the checker to distinguish
narrative from claim — is a heuristic that would fail quietly in the other direction, which is the
worse failure for a gate.

---

## 2. F01: assertional principal-side dishonesty

**Question.** Can a correct executor defend itself when the principal makes a false assertion about a
committed authorization or delivery fact?

**Population.** `M5 M6 M7 M9`, 25 instances each, 100 total.

**Primary regression.** `tests/test_claim_regressions.py::test_f01_assertional_result_is_exactly_zero_vs_one_hundred`.

| protocol | result |
|---|---:|
| B0 bearer token + executor log | **0/100** correct blame |
| B1 bilateral commitment | **100/100** correct blame |
| B13 witness messages | **100/100** handled |
| B17 duty to answer | **100/100** handled |

**Interpretation.** Bilateral commitment is sufficient on this population because each false account
contains an assertion that conflicts with a commitment/signature already held by the other side.

**Guard against denominator drift.** `test_principal_dishonesty_population_is_derived_and_complete`
derives all principal-dishonest classes from corpus ground truth and checks the declared partition.
`test_f01_denominators_are_not_assumed_to_be_25_per_class` derives the quoted denominator from the
corpus rather than trusting a hand-written `100`.

---

## 3. F01 limit: non-assertional principal-side misconduct

**Population.** `M13 M26 M28 M32`, 25 instances each, 100 total.

- M13: baseless complaint used to probe a committed set.
- M26: principal tampers with its stored authorization and withholds the record.
- M28: repeated principal-side withholding pattern.
- M32: principal aborts before acknowledging a delivered result.

**Primary regressions.**

- `test_non_assertional_population_includes_abort_after_delivery`
- `test_f01_non_assertional_result_pins_the_actual_limit`

| protocol | handled |
|---|---:|
| B0 bearer token + executor log | **0/100** |
| B1 bilateral commitment | **0/100** |
| B13 witness messages | **50/100** |
| B17 duty to answer | **100/100** |

**Interpretation.** A commitment cannot refute a proposition nobody made. B13 reaches the baseless
complaint and acknowledgement-abort cases because it carries/checks witness material; B17 additionally
turns non-production into an observable contradiction and therefore reaches the withholding cases.

**Why this test was added.** M32 was added after the original non-assertional F01 declaration. The
corpus changed while the declaration did not. The declaration audit caught the mismatch during the
publication review; this regression makes that exact drift a test failure in future.

---

## 4. Witness-message mechanism (B13)

**Claim.** Recomputing a root from a party's own volunteered assertion can detect contradiction
without opening the committed record, and its disclosure cost remains approximately flat with record
size.

**Primary checks in `tests/test_b13.py`.**

- `test_root_recomputation_detects_a_narrowed_assertion`: catches M6 without reading true scope.
- `test_root_recomputation_reaches_concealed_omission`: catches M1 even though no query can name the
  concealed action.
- `test_only_root_recomputation_survives_padding_on_M1`: distinguishes real root recomputation from a
  cardinality side channel.
- `test_recomputation_uses_only_the_assertion_and_the_root`: pins the inputs used by the check.
- `test_b13_never_attributes_fault` / `test_b13_names_no_party_ever`: a mismatch is stated as a
  contradiction, not culpability.
- `test_b13_false_contradictions_are_confined_to_the_abort_leg`: the only false contradiction is M33,
  the honest twin of M32.
- `test_b13_cannot_reach_an_executor_abort`: pins the fair-exchange gap at M30.
- `test_b13_disclosure_is_flat_in_record_size`: B13 grows less than 10% from scope 2 to 32 while the
  full-disclosure baseline grows by more than 2× under the stipulated encoder.

**Current aggregate.** B13 fully solves 26/34 classes. It misses M19, M20, M22, M24, M26, M28, M30
and false-contradicts M33.

---

## 5. Duty to answer (B17): the exact exchange

**Claim.** Making non-production itself contradictory changes who pays for indistinguishable
withholding/loss worlds; it does not create information that distinguishes them.

**Twin pairs exchanged.**

`M19/M10`, `M20/M21`, `M24/M25`, `M26/M27`, `M28/M29`.

**Primary checks in `tests/test_b17.py`.**

- `test_duty_resolves_the_guilty_classes`: all five guilty classes move from missed to correct
  contradiction.
- `test_duty_breaks_the_honest_twins`: all five honest twins move from correct abstention to false
  contradiction.
- `test_the_exchange_is_exactly_one_for_one`: B13 and B17 remain tied at 26/34 fully solved classes.
- `test_the_ambiguity_changes_denomination_not_quantity`: **125 misses removed = 125 false
  contradictions added**.
- `test_b17_never_attributes_fault`: the duty does not claim malicious intent.
- `test_b17_makes_no_false_ATTRIBUTION_despite_false_contradictions`: B17 has zero false-attribution
  rate despite 150 false contradictions overall; 125 are the duty exchange and 25 are the M33 abort
  leg shared with B13.
- `test_the_duty_attaches_to_both_parties`: prevents the original executor-only modelling asymmetry
  from returning.

**Interpretation.** Non-production is the same observable signal in a concealment world and a genuine
loss world. The duty changes the policy applied to that signal; it cannot reveal why the signal
occurred.

---

## 6. Conservation boundary

**Claim.** For evidence-identical twin worlds, the divergence signature predicts whether one verdict
can be correct in both.

**Population.** Ten verified twin pairs:

- escapable: `M6/M15`, `M7/M17`
- binding: `M19/M10`, `M20/M21`, `M22/M23`, `M24/M25`, `M26/M27`, `M28/M29`,
  `M30/M31`, `M32/M33`

**Primary checks in `tests/test_conservation.py`.**

- `test_the_boundary_predicts_every_pair`: every predicted binding pair is unsolved by every
  unentitled evidence-identical mechanism; every escapable pair has at least one mechanism solving
  both.
- `test_escapable_means_both_worlds_share_a_divergence_signature`: pins the rule to the derived
  divergence sets, not to class names.
- `test_the_escape_is_the_non_attributive_vocabulary`: demonstrates the same non-attributive verdict
  is correct in both mistake/malice worlds.
- `test_attributive_protocols_cannot_take_the_escape`: demonstrates the corresponding false
  attribution when a protocol insists on naming a culprit.
- `test_an_entitled_protocol_is_not_a_counterexample`: a protocol with a larger evidence view is not
  treated as escaping a bound defined for the smaller view.

**Current result.** The prediction holds for all ten pairs across the current 18-protocol family.
The one-line logical argument is stronger than this finite test; the finite test verifies that the
implemented corpus/protocol projections actually instantiate the claimed sides of the boundary.

---

## 7. Scorer semantics

**Claim.** The scoring layer does not quietly flatter a mechanism through ambiguous or overlapping
labels.

**Primary checks in `tests/test_scorer.py`.**

- reachable truth/verdict state enumeration is non-degenerate;
- every state has a defined outcome;
- labels are mutually exclusive;
- innocent attribution cannot become correct blame;
- mistaken-party blame is over-attribution while mistaken-party contradiction can be correct;
- abstention semantics are pinned for unadjudicable and no-divergence worlds;
- a truth-table snapshot catches accidental semantic drift.

`tests/test_metrics.py` separately pins full-class success, worst-class reporting and Pareto
selection so aggregate averages cannot hide a class that fails every instance.

---

## 8. Merkle/proof implementation

`tests/test_merkle.py` exercises membership and non-membership proofs across set sizes and malformed
inputs: wrong roots, edited leaves, sibling tampering, orientation changes, malformed brackets,
incorrect cardinality, duplicate values, domain separation and encoding-size monotonicity.

These tests establish internal correctness of this implementation under its encoding. They are **not**
third-party cryptographic test vectors and are not presented as such.

---

## 9. Declaration, documentation and build-gate checks

The pytest suite is not the whole correctness gate.

- `src.validation.declarations`: derives the principal-dishonesty partition, mutation-family
  semantics, protocol entitlements and commitment bindability, then diffs them against declarations.
- `src.validation.docsync`: generated documentation must match code-derived taxonomy.
- `src.validation.staleness`: live documents are checked for stale corpus/class counts and corrected
  reasoning markers; headline claims are recomputed.
- `src.validation.pruning`: every protocol must be justified by a written claim or research question.
- `src.validation.conservation`: recomputes the boundary report used by the tests.
- `gate-selftest`: deliberately executes `false | true`. With `pipefail`, the left-side failure is
  observable and the self-test passes. If pipeline failure propagation is removed, the self-test
  itself fails the build.

**RC-H15, publication review.** Before this self-test existed, `src.validation.declarations` returned
non-zero for the stale M32 declaration but `python ... | tail -4` returned `tail`'s successful status,
allowing `make check` to print a green banner. The validator was right; its build integration was
wrong. This is now a pinned failure mode rather than a cautionary anecdote.

---

## 10. Reading the results correctly

The numbers are **coverage over a constructed corpus**, not deployment frequencies. `0/100` means
zero correct outcomes over 100 generated instances in a named population. It says nothing about how
often that population occurs in the world. Likewise, byte counts compare schemes under one stipulated
encoder; they are not network cost estimates.

For the compact reproducible numbers, run:

```bash
make check
make experiments
cat results/canonical.txt
```

For claim strength and limitations, read `docs/what-is-established.md` before quoting a result.


## Reporting-derived context (RC-H17)

**Risk.** A generated report can contain a correct machine-derived header and a stale hand-written
explanatory sentence immediately below it. `results/summary.txt` once said 850/34 and then described
"26 adversarial structures" / "650 independent incidents."

**Regression.** `test_reporting_corpus_context_is_derived_not_hard_coded` derives the number of
classes, per-class multiplicity and total scenarios from the corpus, then requires the reporting
helper to produce exactly that narrative. The old 26/650 literals are explicitly rejected.

**Current result.** The context line is derived from live corpus structure; corpus growth cannot
leave the explanatory line behind without failing the test suite.
