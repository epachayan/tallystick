# Sketch: carrying bilateral delegation evidence as an A2A extension

**Status: reference layer and harness replay adapter implemented; not scored by the corpus.**
The standalone code lives in [`src/extensions/a2a_bilateral/`](../../src/extensions/a2a_bilateral/README.md).
It is not covered by `make check`, is not a `LIVE_DOCS` staleness target, and carries no new scored
claim. The boundary between the replay and a corpus-scored protocol is described under
[Turning this into a scored protocol](#turning-this-into-a-scored-protocol).
Repository-local reuse across B1, B13, B17, and the abort/loss classes is tracked separately in the
[extension use map](../extension-use-map.md).

**Dated:** 15 August 2026, against the A2A extension mechanism as documented at
[`docs/topics/extensions.md`](https://github.com/a2aproject/A2A/blob/main/docs/topics/extensions.md)
on that date. Extension mechanics can change between A2A revisions; re-check the field names below
against the current spec before relying on them.

## The gap this fills

[`ARTICLE-MEDIUM.md`](../../ARTICLE-MEDIUM.md) shows a minimal JSON shape for bilateral delegation
evidence — both parties commit to the authorization and the execution record before either can
later deny them — and [`2026-protocol-landscape.md`](2026-protocol-landscape.md) notes that A2A
leaves authorization *policy* agent-defined and does not itself define a counterparty-held
adjudication record. Neither document says how that JSON would actually travel over A2A. This
sketch closes that specific gap: where the fields go, using A2A's own extension mechanism rather
than an ad hoc side channel.

## How A2A extensions actually work

An A2A server declares an extension in its `AgentCard` under `capabilities.extensions`, as an
`AgentExtension` with four fields — `uri` (the extension's identifier), `description`, `required`,
and `params` (extension-specific configuration):

```json
{
  "capabilities": {
    "extensions": [
      {
        "uri": "https://example.org/ext/bilateral-delegation/v1",
        "description": "Countersigned commitments to authorization scope and execution record",
        "required": false,
        "params": { "hashAlg": "sha256" }
      }
    ]
  }
}
```

A client that wants the extension active sends the `A2A-Extensions` header with a comma-separated
list of URIs. Extension-specific data is then carried in a message's `metadata` field, namespaced
under the extension URI — A2A's own example is
`"metadata": {"https://example.com/ext/konami-code/v1/code": "motherlode"}`.

## The sketch

Reusing the extension URI as the namespace prefix, the bilateral-commitment record from the article
becomes metadata on the two messages that already exist in an A2A task exchange — the delegation
request and the result:

```json
// On the principal's initial message (the delegation request)
{
  "metadata": {
    "https://example.org/ext/bilateral-delegation/v1/authorization": {
      "scopeRoot": "sha256:9c41...",
      "principalSignature": "..."
    }
  }
}
```

```json
// On the executor's completing message (the result)
{
  "metadata": {
    "https://example.org/ext/bilateral-delegation/v1/authorization-receipt": {
      "executorReceipt": "..."
    },
    "https://example.org/ext/bilateral-delegation/v1/execution": {
      "actionsRoot": "sha256:4b7e...",
      "executorSignature": "..."
    }
  }
}
```

```json
// On the principal's acknowledgement message, closing the loop
{
  "metadata": {
    "https://example.org/ext/bilateral-delegation/v1/execution-ack": {
      "principalAck": "..."
    }
  }
}
```

Two structural points worth being explicit about:

1. **Each signature is held by the party who did not produce the claim it signs over** — the
   executor's receipt over the authorization lives with the principal's message history, and the
   principal's ack over the execution record lives with the executor's. That is the entire
   mechanism; A2A's `metadata` field is just where it rides. Using `metadata` on the standard
   request/result messages (rather than a bespoke endpoint) means the evidence is retained
   wherever the task's message history is retained, by construction.
2. **A2A's Traceability extension and this one answer different questions and can coexist.**
   Traceability correlates spans across a distributed call; nothing about it is countersigned or
   held by the counterparty. Declaring both extensions on the same `AgentCard` is consistent —
   one reconstructs, the other adjudicates. See the audit-vs-adjudication distinction in
   [`2026-protocol-landscape.md`](2026-protocol-landscape.md#where-this-work-is-different).

## What this would and would not resolve

The harness already scores the underlying mechanism as `B1_bilateral_commitment` — this sketch
changes only the transport, not the commitment scheme, so the existing scored result is the
relevant one rather than a new figure invented for this doc. Per
[`results/canonical.txt`](../../results/canonical.txt) (regenerate with `make experiments` for the
current numbers) and the F01 finding: bilateral commitment resolves the **assertional** classes,
where a party's claim contradicts a signed commitment (`M5`, `M6`, `M7`, `M9` in
[`taxonomy.md`](../taxonomy.md)). It does **not** resolve the **non-assertional** classes —
a baseless complaint, a withheld own-copy, an abort before acknowledgement (`M13`, `M26`, `M28`,
`M32`) — because there is no signed proposition to check the claim against. Carrying the same
fields over A2A metadata does not change which classes the scheme reaches; it only changes where
the bytes travel. Closing the non-assertional gap needs a different mechanism layered on top
(witness messages or a duty to answer — see [finding 10](../findings/10-duty-and-coverage.md) and
[finding 11](../findings/11-symmetric-withholding.md)), and the abort leg (`M30`) is unresolved by
any scored protocol in this corpus — see [finding 13](../findings/13-abort-and-declarations.md).

## Turning this into a scored protocol

The reference code now demonstrates the first step without changing any gated module:

1. [`adapter.py`](../../src/extensions/a2a_bilateral/adapter.py) projects already-extracted live
   signals into the minimal dictionary consumed by `EvidenceView`; the
   [replay demo](../../examples/a2a_harness_replay_demo.py) runs honest and M6-shaped exchanges
   through the existing B0 and B1 functions.
2. No new protocol is registered, no corpus row is created, and no score is produced. The caller
   must hold the actual scope/action lists to construct the existing `ProofOracle`; A2A roots alone
   are insufficient.
3. To make a new claim the gate can check, register a protocol per
   [`CONTRIBUTING.md`](../../CONTRIBUTING.md#adding-a-baseline) —
   `B1_bilateral_commitment` is the closest existing baseline and a reasonable starting point to
   copy from.
4. Run it against the corpus. If the numbers match `B1`'s, the transport mapping was faithful; if
   they don't, the sketch above lost something in translation and that's the interesting finding.

Before registering anything new, first project receipt availability through the existing B13 and
B17 functions. The metadata messages already correspond to their witness chain; only a transport
state that changes observable evidence or trust assumptions justifies a separate scored protocol.

[`src/extensions/a2a_bilateral/`](../../src/extensions/a2a_bilateral/README.md) now contains the
working commitment primitives and metadata carriage: `commit()`, `check_assertion()`, and the
`attach_*()`/`extract()` functions, plus the isolated replay adapter. Deliberately outside this
reference implementation's scope are a deployment-specific parser for concrete A2A SDK messages
and a corpus-registered mapping with ground truth suitable for scoring. The corpus therefore does
not claim to score A2A traffic.
