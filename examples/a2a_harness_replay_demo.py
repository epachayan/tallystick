"""Replay live-shaped exchanges through existing, unmodified harness baselines."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.extensions.a2a_bilateral import project_scenario
from src.model.dispute import build_disputes
from src.model.evidence import DisclosurePolicy, build_view
from src.protocols.baselines import PROTOCOLS


SCOPE = ["deploy:staging", "read:logs"]


def exchange(*, principal_asserted_scope: list[str]) -> dict:
    return project_scenario(
        granted_scope=SCOPE,
        executed_actions=SCOPE,
        principal_asserted_scope=principal_asserted_scope,
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


def verdict_line(name: str, raw: dict) -> str:
    view, oracle = build_view(raw, DisclosurePolicy.FULL)
    disputes = build_disputes(view)
    verdict = PROTOCOLS[name].fn(view, disputes, oracle)
    reasons = "; ".join(verdict.reasons) if verdict.reasons else "none"
    return (
        f"{name:<30} status={verdict.status.value:<10} "
        f"blamed={verdict.blamed.value:<4} reasons={reasons}"
    )


def replay(label: str, raw: dict) -> None:
    print(f"\n{label}")
    for name in ("B0_bearer_executor_log", "B1_bilateral_commitment"):
        print(verdict_line(name, raw))


def main() -> None:
    replay("Honest exchange", exchange(principal_asserted_scope=SCOPE))
    replay(
        "M6-shaped dispute: principal later narrows the granted scope",
        exchange(principal_asserted_scope=["deploy:staging"]),
    )

    print(
        "\nThe dispute reproduces the mechanism shape discussed in "
        "docs/findings/01-baselines.md on live-shaped input, not corpus rows."
    )
    print(
        "results/canonical.txt remains the sole source of harness-pinned figures; "
        "this two-case replay is not a new measurement."
    )
    print(
        "The adapter requires the actual scope/action item lists to construct the "
        "existing ProofOracle; A2A roots alone are insufficient."
    )


if __name__ == "__main__":
    main()
