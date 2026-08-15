# Pruning pass

**Date:** 11 August 2026
**Criterion:** a thing stays if removing it makes some live claim unstatable, or
if it is the only implementation of a registered open question.
**Result:** one module deleted, six result files archived, **zero protocols removed**.

---

## The criterion

"Solves fewest classes" is the wrong test. B0 solves the fewest of all eighteen
protocols and is the entire point of the project; B10, B15 and B16d solve an
identical class set and exist to test three different things.

The right test is citation. `src/validation/pruning.py` lists every live claim
with the protocols it cannot be stated without, then reports anything cited by
nothing. Two roles keep a protocol its own numbers would not justify:

- **control** — the thing another protocol is measured against. Without B0, F01
  is a number with no baseline.
- **contrast** — it differs from another in exactly one dimension and the claim
  *is* the difference. B6 and B6c differ only in whether the adjudicator is
  checked; delete either and the collusion result becomes an assertion.

`make check` now fails if any protocol is cited by neither a claim nor a
registered open question. Registering "we might want it later" is not
permitted — an open question must be named, with its blocker.

## Deleted

**`src/experiments/legacy_experiments.py`** — 707 lines. Broken (imports the
pre-refactor flat module layout and raises `ModuleNotFoundError`), referenced by
nothing, and superseded by `run.py` / `sweep.py` / `regression.py`. Its E1–E12
results are recorded in the findings documents, which is where a result belongs;
the code that produced them was replaced wholesale by the hardening refactor.

This is the only genuine throwaway found. It had been dead since the refactor
and nothing noticed, because nothing imports it and no test touches it.

## Archived, not deleted

Six result files moved to `results/archive-v0.9/` with provenance
(`results/archive-v0.9/README.md`). These were outputs of code that no longer
exists, sitting in `results/` alongside current figures with nothing marking the
difference.

One of them matters more than the rest. **`audit.txt` is the leak check that
reported every baseline "clean" while `B7_verifiable_adjudication` was reading
`adjudicator.colluding`.** It looked for suspicious reads rather than making
them impossible, and a reader finding it in `results/` would reasonably conclude
the visibility question had been settled. It is retained precisely because it is
instructive: it is what a passing audit looks like when the audit is the wrong
shape.

## Kept, with a reason now written down

**B4_scope_predicates.** Flagged by the audit as cited by no live claim — and
that flag was correct, but the conclusion would have been wrong. B4 was carrying
an unstated negative result:

> Exhaustive querying resolves exactly the same classes as
> dispute-bounded querying, at 383 bytes against 284. **35% more disclosure for
> nothing.**

That is the result which justifies the dispute-bounded design, and it had been
sitting in the results table since the selective-disclosure line was built,
unwritten. Now registered as claim `QUERY-COST` and documented in finding 02.

**B11_stateful.** Registered as `PENDING` against RC-H13. It is scored per
scenario, so its pattern detection cannot demonstrate its value — a claim about
a party's history is not testable one scenario at a time. Whether repetition
genuinely escapes the conservation boundary or merely changes the unit of
analysis is the most interesting untested question in the project, and B11 is
the only implementation of it.

## Why nothing else went

Gate C recommended narrowing the selective-disclosure line, and that was read as
"stop developing it", not "delete it". B4–B7, B6c and B7r are the recorded
negative result for an approach that was tried and beaten: exhaustive querying,
dispute-bounded querying, adjudicator checking, and the revocation excuse, each
with its cost. Deleting them would leave the conclusion that witness-carrying
messages are better with nothing behind it.

The standing project constraint applies here too: nothing produced becomes a
throwaway artifact. A negative result is still a result, and it is worth more
than the attention it costs on a results table.

## What the audit actually did

It did not find redundancy. It found a **missing claim** — a protocol whose
justification existed in the numbers but not in any document. That is the fourth
time in this project that deriving a structure and diffing it against the
declaration has surfaced something no amount of re-reading would have (after
F-H3, RC-H9 and RC-H10).

The pattern is now consistent enough to state as a method: **anything
hand-maintained should be recomputed against the code, and the recomputation
should fail the build when they disagree.**
