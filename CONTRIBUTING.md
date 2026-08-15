# Contributing

## The one design rule

**The generator knows nothing about cryptography.** It emits what each party did and what each
party claims. Whether a scheme detects the divergence is the scheme's problem, scored separately.

Break this and the corpus couples to whichever baseline you added, and stops being reusable.

## Layer stability

| layer | stability | notes |
|---|---|---|
| `schema/`, `corpus/` | **durable** | versioned; a new field is a new schema version |
| `src/scoring/scorer.py` | semi-durable | stable interface (`verdict → outcome`), churning internals |
| `src/protocols/baselines.py` | **disposable** | expect to rewrite; keep thin |

## Adding an M-class

1. Add to `M_CLASSES` in `src/generator.py` with its family and dishonest party.
2. If it is an evidential twin of an existing class, register it in `TWIN_OF` so both draw from the
   same random stream — otherwise the views will not be identical and the comparison is void.
3. Extend `src/validation/coherence.py` with a coherence rule for it.
4. Regenerate, run `make check`, then `make experiments`.

The M-class taxonomy versions **independently** of the schema, so adding a class is not a breaking
change.

## Adding a baseline

Return `{"detected": bool, "blamed": "P"|"E"|"J"|"both"|"none", "disclosed_bytes": int}`.
Optional: `status`, `attributes_fault`, `contradicted`, `queries`.

Two rules learned the hard way:

- **Availability gates intactness.** You cannot fail verification on a record that was never
  produced. Every baseline originally had this backwards.
- **Never read ground truth the adjudicator could not have.** If `record_available` is false, the
  execution actions are not yours to inspect.

## Reference extensions

Reference libraries under `src/extensions/` are outside the scored protocol registry. Keep their
tests beside the extension rather than under `tests/`, and give them separate Make targets so they
cannot silently broaden what `make check` claims to cover. For the A2A reference library, run:

```bash
make ext-check
make ext-experiments
```

The parity target checks that the adapter preserves B1 verdicts; it is not an independent protocol
implementation or a new corpus score.

## Before any commit

```bash
python3 -m pip install -e ".[dev]"
make check
make experiments
```

`make check` is the authoritative correctness gate. `make experiments` depends on it and
regenerates the checked-in result artifacts. CI runs the same gate on Python 3.12 and 3.13.

If a baseline legitimately sees more than the base adjudicator view, declare it in
`visibility.ENTITLEMENTS` — an entitlement is a **trust assumption**, and declaring it is what keeps
it from silently inflating a result. Two exist: `B11_stateful` (history) and
`B16c_custodial_attestor` (custodial copy).

## Reporting

Report **worst-class** alongside average. Uniform class sampling is not a security metric — an
adversary selects the class you are worst at.

---

## The second design rule (added 11 August 2026)

**Anything hand-maintained must be recomputed against the code, and the recomputation must fail
the build on disagreement.**

Six stated claims in this project turned out to be wrong. All six had the same shape - a universal
statement inferred from the subset in view - and all six were found by deriving the structure from
the code and diffing it against the declaration. None was found by re-reading prose, and none by
the tests in place at the time.

So: if you add a declaration (a class set, a twin pairing, an entitlement list, a claim about
which mechanisms reach what), add the derivation that checks it in the same change. Five of the
correctness-gate stages exist for exactly this reason:

| stage | exists because |
|---|---|
| `twins` | a twin declaration was wrong since the corpus was built (F-H3) |
| `coverage` | withholding was modelled for one party only (RC-H9) |
| `conservation` | a class was described as resisting every mechanism when it resisted one family (RC-H10) |
| `declarations` | the F01 denominator excluded its unflattering classes (RC-H12) |
| `pruning` | a protocol carried a negative result nobody had written down (RC-H14) |

Three further stages guard the documents:

- `docsync` - a document restating something the code already knows is generated from the code. A
  class table is a copy, not reasoning. Prose that reasons about the code stays hand-written.
- `links` - every local Markdown target and heading fragment resolves, and every retained Markdown
  document is reachable from `README.md`, `START-HERE.md`, or `INDEX.md`.
- `staleness` - verifies declared figures against live code **and** requires any document
  asserting the old form of a corrected claim to point at its correction. The second half exists
  because the numeric check passed cleanly while five documents carried refuted arguments.

A later reporting bug added the same rule for generated prose: numeric context such as corpus
size must be derived from the corpus rather than embedded as a literal.

Corollary worth internalising: **"checked" always needs "in what dimension, and does failure
propagate?" attached.**
