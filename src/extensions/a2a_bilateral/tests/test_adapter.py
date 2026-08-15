"""Tests for the optional bridge into the existing harness view pipeline."""

from __future__ import annotations

from src.extensions.a2a_bilateral import project_scenario
from src.model.dispute import build_disputes
from src.model.evidence import DisclosurePolicy, build_view
from src.model.types import Party, VerdictStatus
from src.protocols.baselines import PROTOCOLS


SCOPE = ["deploy:staging", "read:logs"]


def scenario(*, principal_scope=SCOPE) -> dict:
    return project_scenario(
        granted_scope=SCOPE,
        executed_actions=SCOPE,
        principal_asserted_scope=principal_scope,
        principal_asserted_actions=None,
        principal_asserted_auth_issued=True,
        principal_asserted_result_received=True,
        principal_record_available=True,
        principal_record_intact=True,
        principal_disputed_action=None,
        executor_asserted_scope=SCOPE,
        executor_asserted_actions=SCOPE,
        executor_asserted_auth_issued=True,
        executor_asserted_result_received=True,
        executor_record_available=True,
        executor_record_intact=True,
        executor_disputed_action=None,
    )


def evaluate(name: str, raw: dict):
    protocol = PROTOCOLS[name]
    view, oracle = build_view(raw, DisclosurePolicy.FULL)
    return protocol.fn(view, build_disputes(view), oracle)


def test_projection_is_minimal_and_copies_caller_sequences():
    granted = list(SCOPE)
    projected = project_scenario(
        granted_scope=granted,
        executed_actions=SCOPE,
        principal_asserted_scope=SCOPE,
        principal_asserted_actions=None,
        principal_asserted_auth_issued=True,
        principal_asserted_result_received=True,
        principal_record_available=True,
        principal_record_intact=True,
        principal_disputed_action=None,
        executor_asserted_scope=SCOPE,
        executor_asserted_actions=SCOPE,
        executor_asserted_auth_issued=True,
        executor_asserted_result_received=True,
        executor_record_available=True,
        executor_record_intact=True,
        executor_disputed_action=None,
    )
    granted.append("write:logs")

    assert set(projected) == {"authorization", "execution", "chain", "p_view", "e_view"}
    assert projected["authorization"]["scope"] == SCOPE
    assert "ground_truth" not in projected
    assert "m_class" not in projected


def test_honest_live_shaped_exchange_is_clear_for_b0_and_b1():
    raw = scenario()

    for name in ("B0_bearer_executor_log", "B1_bilateral_commitment"):
        verdict = evaluate(name, raw)
        assert verdict.status is VerdictStatus.CLEAR
        assert verdict.blamed is Party.NONE


def test_m6_shaped_narrowing_is_only_bound_by_bilateral_commitment():
    raw = scenario(principal_scope=["deploy:staging"])

    b0 = evaluate("B0_bearer_executor_log", raw)
    b1 = evaluate("B1_bilateral_commitment", raw)

    assert b0.status is VerdictStatus.SUSPECTED
    assert b0.blamed is Party.NONE
    assert b1.status is VerdictStatus.EXPOSED
    assert b1.blamed is Party.P
