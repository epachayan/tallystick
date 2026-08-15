# A2A bilateral-delegation-commitment extension

**Status: reference library, not part of the research harness.** It is not scored by `make check`.
The Merkle commitment implementation it calls is covered by the project's existing test suite;
this extension and metadata layer has separate tests under this directory.

This is the working code for the design in
[`docs/prior-art/a2a-extension-sketch.md`](../../../docs/prior-art/a2a-extension-sketch.md) and
[`ARTICLE-MEDIUM.md`](../../../ARTICLE-MEDIUM.md). Both parties commit to authorization scope and
execution records before either can later deny them. The commitments travel through A2A's own
extension mechanism—`AgentCard.capabilities.extensions` and namespaced message `metadata`—rather
than a bespoke channel.

## What it resolves and what it does not

This primitive addresses **assertional** disputes: a later claim can be checked against an earlier
signed commitment without opening the original set. It does not resolve **non-assertional**
misconduct such as silence, withholding an own-copy, or abort before acknowledgement, because no
signed proposition exists to check. The [A2A sketch](../../../docs/prior-art/a2a-extension-sketch.md)
maps those limits to the research classes. Exact harness results remain solely in
[`results/canonical.txt`](../../../results/canonical.txt); this library does not generate or alter
them.

## Uses inside this repository

The implemented use is concrete A2A-shaped carriage and replay for `B1_bilateral_commitment`.
The same artifact chain can next be used as a fixture for `B13_witness_messages`,
`B17_duty_to_answer`, and the M30-M33 abort/loss classes. That work should extend the adapter's
receipt-availability projection and reuse the existing scored functions, not create A2A-labelled
copies of them. The [extension use map](../../../docs/extension-use-map.md) distinguishes completed
integration from proposed reuse.

## Quick start

```python
from src.extensions.a2a_bilateral import (
    attach_authorization,
    check_assertion,
    commit,
)

# Supply a real Signer with .sign(payload: bytes) -> str.
authorization = commit(
    ["deploy:staging", "read:logs"],
    signer=my_signer,
    signer_id="principal-1",
)

request = attach_authorization({"role": "user", "parts": []}, authorization)

check_assertion(["deploy:staging", "read:logs"], authorization)  # True
check_assertion(["deploy:staging"], authorization)               # False
```

Inputs are set-shaped: duplicate strings are normalized to one member before the existing
cardinality-bound [Merkle implementation](../../crypto/merkle.py) is called.

## Bring your own signer

`Signer` and `Verifier` in `commitment.py` are structural-typing protocols with `.sign()` and
`.verify()` methods. No signature scheme is bundled. Use a real COSE, JWS, or Ed25519 implementation
for deployment. `ToyHmacSigner` and `ToyHmacVerifier` in
[`examples/a2a_bilateral_demo.py`](../../../examples/a2a_bilateral_demo.py) exist only to keep the
walkthrough dependency-free. HMAC is symmetric and cannot provide non-repudiation between principal
and executor to a third-party adjudicator.

Run the standalone checks and demonstration from the repository root:

```bash
python3 -m pytest src/extensions/a2a_bilateral/tests -q
python3 examples/a2a_bilateral_demo.py
python3 -m src.extensions.a2a_bilateral.parity
```

These tests intentionally live outside `tests/`, so the library remains separate from the corpus
correctness gate.

## Optional harness replay adapter

[`adapter.py`](adapter.py) builds the minimal scenario-shaped dictionary accepted by the existing
`src.model.evidence.build_view()` pipeline. It does not modify or register a protocol, add corpus
rows, or create a new scored result. The accompanying
[`a2a_harness_replay_demo.py`](../../../examples/a2a_harness_replay_demo.py) sends one honest and one
M6-shaped exchange through the existing B0 and B1 functions:

```bash
python3 examples/a2a_harness_replay_demo.py
```

This boundary is intentionally plain about what it requires. The caller must hold the actual scope
and action item lists—not only the Merkle roots carried in A2A metadata—so the existing
`ProofOracle` can be constructed. That models a party checking a counterparty's claim against its
own known set, or a neutral adjudicator to whom both sides disclosed. It does not add a new
zero-knowledge capability. The adapter also accepts already-extracted live signals; parsing and
validating a vendor SDK's concrete A2A message/task history remains deployment-specific.

The standalone parity command projects every checked-in corpus row through the adapter and compares
the resulting B1 `Verdict` with the canonical B1 projection. Exact equality demonstrates that the
adapter preserves the existing model; it is not an independent implementation, protocol
registration, or new research score. `make ext-experiments` is a convenience alias and remains
separate from both `make check` and `make experiments`.

## Extension URI

`card.EXTENSION_URI` is a placeholder under `https://example.org/`. Mint a URI you control before
deployment. An A2A extension URI must be unique; it does not need to resolve.

## Deployment gaps

This package does not implement `A2A-Extensions` header negotiation, vendor-SDK parsing, persistent
receipt storage, or key discovery. Before deployment, replace bare-root signatures with a canonical
signed envelope that binds purpose, task and authorization IDs, both parties, extension version,
algorithm, timestamp/expiry/nonce, root, and cardinality. Otherwise a valid signature may be replayed
across tasks or message purposes. Commitments also do not hide cardinality or protect predictable
sets from guessing; they are neither encryption nor zero knowledge.
