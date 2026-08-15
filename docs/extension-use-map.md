# Extension use inside Tallystick

**Status:** current integration map. The A2A package is a reference transport and projection layer,
not a separately scored protocol and not evidence of deployment adoption.

The extension is useful inside this repository wherever a harness mechanism needs a concrete
principal/executor message exchange. It gives the abstract commitment fields a place to travel,
while the harness continues to decide what those fields can and cannot establish.

## Where it fits now

| repository area | use of the extension | boundary |
|---|---|---|
| `B1_bilateral_commitment` | concrete A2A carriage for the signed authorization, receipt, execution record, and acknowledgement | transport mapping only; B1 remains the scored mechanism |
| `B13_witness_messages` | the four metadata artifacts correspond to the counterparty-held witnesses B13 reasons from | the package does not yet project every B13 availability/withholding state |
| `B17_duty_to_answer` | a witnessed commitment can identify which party has an obligation to answer a later challenge | the duty is policy, not supplied by A2A or by the commitment code |
| M30-M33 abort/loss classes | the three-message exchange is a concrete fixture for testing which receipt each party holds when a leg aborts or is lost | the demo currently follows the completed path; it has no channel scheduler |
| `EvidenceView` / `ProofOracle` | `adapter.py` turns validated, already-extracted exchange facts into the existing adjudicator input | roots alone cannot reconstruct the private sets required by the current oracle |
| corpus development | future real A2A traces can motivate new channel, replay, expiry, and retransmission classes | traces must be converted into scenario facts; they must never be read as ground truth by a protocol |

The first row is implemented and checked by exact B1 adapter parity. The remaining rows are
well-scoped reuse opportunities, not completed integrations or measured results.

## Recommended next internal integration

Extend the adapter to project the receipt-availability states already represented by B13 and the
M30-M33 classes. Add dependency-free fixtures for completed exchange, executor abort, lost execution
receipt, principal abort, and lost acknowledgement. Evaluate those projections through the existing
B13 and B17 functions rather than registering an `A2A_*` copy of either protocol.

A new scored protocol is warranted only if the transport introduces a materially different evidence
projection or trust assumption. If it merely carries the same roots, signatures, and receipts, the
correct result is parity with the existing baseline.

## What should remain separate

- `make check` is the correctness gate for the corpus and scored protocols.
- `make ext-check` tests the standalone extension API and metadata shapes.
- `make ext-experiments` checks adapter fidelity against B1; it creates no new score.
- Vendor-SDK parsing, network transport, key discovery, persistence, and A2A header negotiation are
  deployment adapters, not harness responsibilities.

## Before using it outside the repository

The current URI is a placeholder and the demo uses symmetric HMAC. A deployable profile needs a
governed versioned URI, schema validation, A2A extension negotiation, asymmetric signatures and key
rotation, and a canonical signed envelope binding message purpose, task and authorization IDs,
parties, algorithm, time/expiry/nonce, root, and cardinality. Signing only a bare root is not enough
to prevent cross-task or cross-purpose replay.

Commitments are not encryption or zero knowledge. They reveal cardinality unless padded, and small
or predictable sets may be dictionary-guessed. Durable retention and incomplete-handshake semantics
also have to be specified before the exchange can support an operational dispute process.

See the [implementation README](../src/extensions/a2a_bilateral/README.md), the
[A2A transport sketch](prior-art/a2a-extension-sketch.md), and the
[harness architecture](architecture.md).
