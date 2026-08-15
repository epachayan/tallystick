"""Project a live-shaped exchange into the existing EvidenceView pipeline.

The returned dictionary is the minimal scenario shape consumed by
``src.model.evidence.build_view``. It deliberately contains no corpus identity
or ground-truth fields and registers no protocol.

Callers must hold the actual granted-scope and executed-action item lists to
build the existing ProofOracle. Roots carried in A2A metadata alone are not
enough. This models a party checking a counterparty's claim against its own
known set, or an adjudicator to whom both sides disclosed; it adds no new
zero-knowledge capability.
"""

from __future__ import annotations

from typing import Sequence


def project_scenario(
    *,
    granted_scope: Sequence[str],
    executed_actions: Sequence[str],
    principal_asserted_scope: Sequence[str] | None,
    principal_asserted_actions: Sequence[str] | None,
    principal_asserted_auth_issued: bool,
    principal_asserted_result_received: bool,
    principal_record_available: bool,
    principal_record_intact: bool,
    principal_disputed_action: str | None,
    executor_asserted_scope: Sequence[str] | None,
    executor_asserted_actions: Sequence[str] | None,
    executor_asserted_auth_issued: bool,
    executor_asserted_result_received: bool,
    executor_record_available: bool,
    executor_record_intact: bool,
    executor_disputed_action: str | None,
    authorization_issued: bool = True,
    authorization_committed: bool = True,
    exec_receipt_sent: bool = True,
    delivery_ack_sent: bool = True,
    result_delivered: bool = True,
) -> dict:
    """Build only the fields required by ``build_view``.

    The committed item lists describe what the parties' systems actually
    granted and recorded. The asserted lists describe what each party claims
    at dispute time. Keeping those inputs separate is the mechanism under test.
    All sequences are copied so later caller mutation cannot alter the result.
    """
    return {
        "authorization": {
            "auth_id": "live",
            "issued": authorization_issued,
            "committed": authorization_committed,
            "scope": list(granted_scope),
            "constraints": {},
        },
        "execution": {
            "actions": list(executed_actions),
            "result_delivered": result_delivered,
        },
        "chain": {
            "exec_receipt_sent": exec_receipt_sent,
            "delivery_ack_sent": delivery_ack_sent,
        },
        "p_view": {
            "asserted_scope": (
                list(principal_asserted_scope)
                if principal_asserted_scope is not None else None
            ),
            "asserted_actions": (
                list(principal_asserted_actions)
                if principal_asserted_actions is not None else None
            ),
            "asserted_auth_issued": principal_asserted_auth_issued,
            "asserted_result_received": principal_asserted_result_received,
            "record_available": principal_record_available,
            "record_intact": principal_record_intact,
            "disputed_action": principal_disputed_action,
        },
        "e_view": {
            "asserted_scope": (
                list(executor_asserted_scope)
                if executor_asserted_scope is not None else None
            ),
            "asserted_actions": (
                list(executor_asserted_actions)
                if executor_asserted_actions is not None else None
            ),
            "asserted_auth_issued": executor_asserted_auth_issued,
            "asserted_result_received": executor_asserted_result_received,
            "record_available": executor_record_available,
            "record_intact": executor_record_intact,
            "disputed_action": executor_disputed_action,
        },
    }
