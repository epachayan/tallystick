# Harness architecture

```
                       Scenario (corpus row)
                                |
              +-----------------+-----------------+
              |                                   |
              v                                   v
       build_view(policy, entitlements)      GroundTruth.from_scenario
              |                                   |
      EvidenceView + ProofOracle                  |
              |                                   |
      build_disputes(view)                        |
              |                                   |
        Dispute tuple                             |
              |                                   |
              v                                   v
     protocol.fn(view, disputes, oracle) --> Verdict --> score(truth, verdict)
                                                              |
                                                           Outcome
                                                              |
                                                        metrics.Report
```

The left branch never touches the right one. `evaluate()` in
`src/reporting/harness.py` is the single place a protocol receives input, and
`score()` is the single place ground truth is read.

## Layout

```
tallystick/
    schema/scenario.v0.2.schema.json
    corpus/corpus.v0.9.jsonl
    src/
        model/      dispute.py  evidence.py  types.py
        crypto/     merkle.py
        protocols/  baselines.py   (B0-B17, evidence-only)
        scoring/    metrics.py  scorer.py
        validation/ coherence.py  conservation.py  coverage.py  declarations.py  pruning.py  schema.py  staleness.py  twins.py  visibility.py
        reporting/  harness.py  regression.py  run.py  sweep.py
        extensions/ a2a_bilateral/  (standalone reference library and adapter)
        generator.py  commitments.py
    tests/          test_scorer.py  test_merkle.py  test_metrics.py  test_integration.py
    examples/       a2a_bilateral_demo.py  a2a_harness_replay_demo.py
    results/
    docs/
```

## Command boundaries

```
make check         13-stage core correctness gate, including tests, structural
                   audits, document synchronization, links, and staleness
make experiments   depends on check; writes results/
make taxonomy      regenerates docs/taxonomy.md from M_CLASSES
make ext-check     runs isolated A2A reference-library tests
make ext-experiments  checks exact B1 adapter parity over the corpus
```

Five of those stages exist because a hand-maintained declaration was found
wrong: `twins` (F-H3), `coverage` (RC-H9), `conservation` (RC-H10),
`declarations` (RC-H12), `pruning` (RC-H14). Each recomputes something that used
to be asserted in prose.

`make experiments` will not run on a failed gate. A green experiment suite
therefore means the experiment ran on verified machinery, not that a script
exited zero.

The `ext-*` targets are intentionally independent. The A2A library can import the existing Merkle
and evidence machinery, but it does not register a protocol or contribute tests to `make check`.
Its parity command checks projection fidelity against B1; it does not create a new research score.

## Disclosure policies

| policy | what reaches the adjudicator |
|---|---|
| `FULL` | contents of committed artifacts that were actually produced, plus signatures |
| `COMMITMENT_ONLY` | roots and cardinalities; contents only via query + verified proof |

Availability gates everything (A3): an unproduced record yields neither contents
nor integrity status — `record_intact` is `None`, not `False`. What survives
non-production is the commitment made earlier: its root and, because a sound
root binds it, its cardinality.

## Entitlements

Every widening of the base view is a declared trust assumption:

| protocol | entitlement | what it assumes |
|---|---|---|
| `B11_stateful` | `history` | the adjudicator remembers prior disputes |
| `B16c_custodial_attestor` | `custodial_copy` | the third party holds the contents, making it a custodian rather than an attestor |

Anything not listed here is unavailable, structurally.

## Adding a protocol

```python
@register("B13_witness_messages", DisclosurePolicy.COMMITMENT_ONLY)
def b13_witness_messages(view, disputes, oracle):
    ...
    return Verdict(...)
```

Registration is all that is needed; `make check` will then run the visibility
mutation tests against it automatically. A protocol that reads hidden state
cannot be written, because there is no argument carrying it.
