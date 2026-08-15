"""End-to-end A2A-shaped exchange using the standalone reference library."""

from __future__ import annotations

import hashlib
import hmac

from src.extensions.a2a_bilateral import (
    Commitment,
    attach_authorization,
    attach_authorization_receipt,
    attach_execution,
    attach_execution_ack,
    check_assertion,
    commit,
    extract,
)


class HmacFixture:
    """Symmetric test fixture, not a deployment signer."""

    def __init__(self, key: bytes):
        self.key = key

    def sign(self, payload: bytes) -> str:
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()


def _authorization_from(message: dict) -> Commitment:
    value = extract(message, "authorization")
    assert value is not None
    return Commitment(
        root=value["scopeRoot"],
        cardinality=value["cardinality"],
        signature=value["principalSignature"],
        signer_id=value["signerId"],
    )


def _execution_from(message: dict) -> Commitment:
    value = extract(message, "execution")
    assert value is not None
    return Commitment(
        root=value["actionsRoot"],
        cardinality=value["cardinality"],
        signature=value["executorSignature"],
        signer_id=value["signerId"],
    )


def test_three_message_exchange_and_later_contradictions():
    principal = HmacFixture(b"principal-demo-key")
    executor = HmacFixture(b"executor-demo-key")
    granted_scope = ["deploy:staging", "read:logs"]
    executed_actions = ["deploy:staging", "read:logs"]

    authorization = commit(granted_scope, signer=principal, signer_id="principal-1")
    request = attach_authorization({"role": "user", "parts": []}, authorization)

    received_authorization = _authorization_from(request)
    execution = commit(executed_actions, signer=executor, signer_id="executor-1")
    result = attach_authorization_receipt(
        {"role": "agent", "parts": []},
        executor_signature=executor.sign(received_authorization.root.encode("utf-8")),
        signer_id="executor-1",
    )
    result = attach_execution(result, execution)

    received_execution = _execution_from(result)
    acknowledgement = attach_execution_ack(
        {"role": "user", "parts": []},
        principal_signature=principal.sign(received_execution.root.encode("utf-8")),
        signer_id="principal-1",
    )

    assert extract(result, "authorization-receipt") is not None
    assert extract(acknowledgement, "execution-ack") is not None
    assert check_assertion(executed_actions, received_authorization)

    # src/commitments.py BINDING["M6"] and BINDING["M2"] are the source of
    # truth for the narrowing and omission cases demonstrated here.
    assert not check_assertion(["deploy:staging"], received_authorization)
    assert not check_assertion(["deploy:staging"], received_execution)
