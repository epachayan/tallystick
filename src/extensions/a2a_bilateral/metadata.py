"""Attach and extract commitment data using namespaced A2A metadata.

Messages are plain dictionaries because A2A messages are JSON. Attach helpers
return new dictionaries and never mutate the supplied message or metadata.
"""

from __future__ import annotations

from .card import EXTENSION_URI
from .commitment import Commitment

_AUTHORIZATION = "authorization"
_AUTHORIZATION_RECEIPT = "authorization-receipt"
_EXECUTION = "execution"
_EXECUTION_ACK = "execution-ack"


def _ns(key: str) -> str:
    return f"{EXTENSION_URI}/{key}"


def _with_metadata(message: dict, key: str, value: dict) -> dict:
    metadata = dict(message.get("metadata", {}))
    metadata[_ns(key)] = value
    return {**message, "metadata": metadata}


def attach_authorization(message: dict, commitment: Commitment) -> dict:
    """Attach the principal's commitment to the granted scope."""
    return _with_metadata(message, _AUTHORIZATION, {
        "scopeRoot": commitment.root,
        "cardinality": commitment.cardinality,
        "principalSignature": commitment.signature,
        "signerId": commitment.signer_id,
    })


def attach_authorization_receipt(
    message: dict, *, executor_signature: str, signer_id: str
) -> dict:
    """Attach the executor's countersignature of the authorization received."""
    return _with_metadata(message, _AUTHORIZATION_RECEIPT, {
        "executorSignature": executor_signature,
        "signerId": signer_id,
    })


def attach_execution(message: dict, commitment: Commitment) -> dict:
    """Attach the executor's commitment to the actions actually taken."""
    return _with_metadata(message, _EXECUTION, {
        "actionsRoot": commitment.root,
        "cardinality": commitment.cardinality,
        "executorSignature": commitment.signature,
        "signerId": commitment.signer_id,
    })


def attach_execution_ack(
    message: dict, *, principal_signature: str, signer_id: str
) -> dict:
    """Attach the principal's countersignature of the execution record."""
    return _with_metadata(message, _EXECUTION_ACK, {
        "principalSignature": principal_signature,
        "signerId": signer_id,
    })


def extract(message: dict, key: str) -> dict | None:
    """Extract one of the four extension fields by its unqualified key."""
    return message.get("metadata", {}).get(_ns(key))
