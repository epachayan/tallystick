"""Standalone corpus parity check for the A2A scenario adapter.

This module does not register a protocol or generate a research score. It
projects each existing corpus row through ``project_scenario`` and requires the
existing B1 baseline to return the exact same Verdict as it does on the row's
canonical projection. Equality here tests adapter fidelity, not protocol
quality or an independent implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.model.dispute import build_disputes
from src.model.evidence import build_view
from src.model.types import Verdict
from src.protocols.baselines import PROTOCOLS
from src.reporting.harness import load_corpus

from .adapter import project_scenario


@dataclass(frozen=True)
class ParityMismatch:
    scenario_id: str
    m_class: str
    canonical: Verdict
    projected: Verdict


def project_corpus_row(scenario: dict) -> dict:
    """Map one existing corpus row through the public live-input adapter."""
    authorization = scenario["authorization"]
    execution = scenario["execution"]
    chain = scenario.get("chain", {})
    principal = scenario["p_view"]
    executor = scenario["e_view"]

    return project_scenario(
        granted_scope=authorization.get("scope", []),
        executed_actions=execution.get("actions", []),
        principal_asserted_scope=principal.get("asserted_scope"),
        principal_asserted_actions=principal.get("asserted_actions"),
        principal_asserted_auth_issued=bool(
            principal.get("asserted_auth_issued", True)
        ),
        principal_asserted_result_received=bool(
            principal.get("asserted_result_received", True)
        ),
        principal_record_available=bool(principal.get("record_available", True)),
        principal_record_intact=bool(principal.get("record_intact", True)),
        principal_disputed_action=principal.get("disputed_action"),
        executor_asserted_scope=executor.get("asserted_scope"),
        executor_asserted_actions=executor.get("asserted_actions"),
        executor_asserted_auth_issued=bool(executor.get("asserted_auth_issued", True)),
        executor_asserted_result_received=bool(
            executor.get("asserted_result_received", True)
        ),
        executor_record_available=bool(executor.get("record_available", True)),
        executor_record_intact=bool(executor.get("record_intact", True)),
        executor_disputed_action=executor.get("disputed_action"),
        authorization_issued=bool(authorization.get("issued", True)),
        authorization_committed=bool(authorization.get("committed", True)),
        exec_receipt_sent=bool(chain.get("exec_receipt_sent", True)),
        delivery_ack_sent=bool(chain.get("delivery_ack_sent", True)),
        result_delivered=bool(execution.get("result_delivered", True)),
    )


def evaluate_b1(scenario: dict) -> Verdict:
    protocol = PROTOCOLS["B1_bilateral_commitment"]
    view, oracle = build_view(scenario, protocol.policy, protocol.entitlements)
    return protocol.fn(view, build_disputes(view), oracle)


def parity_mismatches(scenarios: Iterable[dict]) -> tuple[int, list[ParityMismatch]]:
    total = 0
    mismatches: list[ParityMismatch] = []
    for scenario in scenarios:
        total += 1
        canonical = evaluate_b1(scenario)
        projected = evaluate_b1(project_corpus_row(scenario))
        if canonical != projected:
            mismatches.append(ParityMismatch(
                scenario_id=scenario.get("scenario_id", "<unknown>"),
                m_class=scenario.get("m_class", "<unknown>"),
                canonical=canonical,
                projected=projected,
            ))
    return total, mismatches


def main() -> None:
    total, mismatches = parity_mismatches(load_corpus())
    if mismatches:
        print(f"B1 adapter parity: {total - len(mismatches)}/{total} exact verdicts match")
        for mismatch in mismatches[:20]:
            print(
                f"  {mismatch.scenario_id} ({mismatch.m_class}): "
                f"canonical={mismatch.canonical.key()} projected={mismatch.projected.key()}"
            )
        raise SystemExit(f"adapter parity failed for {len(mismatches)} scenario(s)")

    print(f"B1 adapter parity: {total}/{total} exact verdicts match")
    print("adapter fidelity check only; no protocol registered and no new score produced")


if __name__ == "__main__":
    main()
