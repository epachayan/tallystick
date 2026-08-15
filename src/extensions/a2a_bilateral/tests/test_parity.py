"""Full-corpus fidelity check for the standalone adapter experiment."""

from src.extensions.a2a_bilateral.parity import parity_mismatches
from src.reporting.harness import load_corpus


def test_adapter_preserves_every_canonical_b1_verdict():
    scenarios = load_corpus()
    total, mismatches = parity_mismatches(scenarios)

    assert total == len(scenarios)
    assert total > 0
    assert mismatches == []
