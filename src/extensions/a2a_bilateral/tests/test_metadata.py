"""Tests for immutable A2A metadata carriage."""

from __future__ import annotations

from src.extensions.a2a_bilateral import (
    Commitment,
    attach_authorization,
    attach_authorization_receipt,
    attach_execution,
    attach_execution_ack,
    extract,
)


AUTHORIZATION = Commitment(
    root="auth-root", cardinality=2, signature="principal-signature", signer_id="principal-1"
)
EXECUTION = Commitment(
    root="exec-root", cardinality=1, signature="executor-signature", signer_id="executor-1"
)


def test_attach_authorization_returns_a_new_message_without_mutation():
    original = {"role": "user", "parts": []}
    result = attach_authorization(original, AUTHORIZATION)

    assert result is not original
    assert original == {"role": "user", "parts": []}
    assert "metadata" not in original


def test_authorization_round_trip_matches_the_commitment():
    payload = extract(attach_authorization({}, AUTHORIZATION), "authorization")

    assert payload == {
        "scopeRoot": AUTHORIZATION.root,
        "cardinality": AUTHORIZATION.cardinality,
        "principalSignature": AUTHORIZATION.signature,
        "signerId": AUTHORIZATION.signer_id,
    }


def test_unrelated_metadata_is_preserved_without_mutating_the_original():
    original = {"metadata": {"other-extension/foo": "bar"}}
    result = attach_authorization(original, AUTHORIZATION)

    assert result["metadata"]["other-extension/foo"] == "bar"
    assert original == {"metadata": {"other-extension/foo": "bar"}}
    assert result["metadata"] is not original["metadata"]


def test_all_four_extension_fields_round_trip():
    message = attach_authorization({}, AUTHORIZATION)
    message = attach_authorization_receipt(
        message, executor_signature="authorization-receipt-signature", signer_id="executor-1"
    )
    message = attach_execution(message, EXECUTION)
    message = attach_execution_ack(
        message, principal_signature="execution-ack-signature", signer_id="principal-1"
    )

    assert extract(message, "authorization")["scopeRoot"] == "auth-root"
    assert extract(message, "authorization-receipt") == {
        "executorSignature": "authorization-receipt-signature",
        "signerId": "executor-1",
    }
    assert extract(message, "execution")["actionsRoot"] == "exec-root"
    assert extract(message, "execution-ack") == {
        "principalSignature": "execution-ack-signature",
        "signerId": "principal-1",
    }


def test_extract_returns_none_when_the_field_is_absent():
    assert extract({}, "authorization") is None
    assert extract({"metadata": {}}, "execution") is None
