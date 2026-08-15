"""Runnable walkthrough of the standalone A2A bilateral extension."""

from __future__ import annotations

import hashlib
import hmac
import json
from pprint import pprint

from src.extensions.a2a_bilateral import (
    attach_authorization,
    attach_authorization_receipt,
    attach_execution,
    attach_execution_ack,
    check_assertion,
    commit,
    extension_descriptor,
)


class ToyHmacSigner:
    """Demo only: symmetric HMAC cannot provide third-party non-repudiation.

    Replace this with a real COSE, JWS, or Ed25519 signer before using the
    reference library for anything that must survive an actual dispute.
    """

    def __init__(self, key: bytes):
        self.key = key

    def sign(self, payload: bytes) -> str:
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()


class ToyHmacVerifier:
    """Demo only: HMAC verification uses the same shared secret as signing."""

    def __init__(self, key: bytes):
        self.key = key

    def verify(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(self.key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


def show_metadata(label: str, message: dict) -> None:
    print(f"\n{label}")
    pprint(message["metadata"], sort_dicts=False)


def main() -> None:
    print("AgentCard.capabilities.extensions entry:")
    print(json.dumps(extension_descriptor(), indent=2))

    principal = ToyHmacSigner(b"principal-demo-key")
    executor = ToyHmacSigner(b"executor-demo-key")
    scope = ["deploy:staging", "read:logs"]
    actions = ["deploy:staging", "read:logs"]

    authorization = commit(scope, signer=principal, signer_id="principal-1")
    request = attach_authorization(
        {"role": "user", "parts": [{"text": "Deploy and inspect logs"}]},
        authorization,
    )
    show_metadata("1. Principal sends authorization commitment:", request)

    execution = commit(actions, signer=executor, signer_id="executor-1")
    result = attach_authorization_receipt(
        {"role": "agent", "parts": [{"text": "Completed"}]},
        executor_signature=executor.sign(authorization.root.encode("utf-8")),
        signer_id="executor-1",
    )
    result = attach_execution(result, execution)
    show_metadata("2. Executor countersigns authorization and commits execution:", result)

    acknowledgement = attach_execution_ack(
        {"role": "user", "parts": [{"text": "Result received"}]},
        principal_signature=principal.sign(execution.root.encode("utf-8")),
        signer_id="principal-1",
    )
    show_metadata("3. Principal acknowledges the execution commitment:", acknowledgement)

    consistent = check_assertion(["deploy:staging"], authorization)
    print("\nLater narrower assertion matches authorization commitment:", consistent)
    print("False means it contradicts the earlier signed commitment;")
    print("it does not, by itself, establish why the accounts differ.")

    print("\nRead next:")
    print("  src/extensions/a2a_bilateral/README.md")
    print("  docs/prior-art/a2a-extension-sketch.md")


if __name__ == "__main__":
    main()
