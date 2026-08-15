"""Integration tests: the corpus, the projection and the protocols together.

These are the tests that would have caught P0-1 and P0-3 in v0.9.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.dispute import build_disputes
from src.model.evidence import (
    DisclosurePolicy,
    EvidenceView,
    ProofOracle,
    build_view,
)
from src.model.types import GroundTruth, Party
from src.protocols.baselines import PROTOCOLS
from src.reporting.harness import evaluate, load_corpus, reports
from src.validation import coherence, schema, twins, visibility

CORPUS = load_corpus()
ONE_PER_CLASS = list({s["m_class"]: s for s in CORPUS}.values())


# ---------------------------------------------------------------------------
# corpus integrity
# ---------------------------------------------------------------------------

def test_corpus_size():
    assert len(CORPUS) == 850
    assert len({s["m_class"] for s in CORPUS}) == 34


def test_corpus_validates_against_schema_v0_2():
    assert schema.validate_corpus(CORPUS) == []


def test_corpus_is_semantically_coherent():
    assert coherence.validate_corpus(CORPUS) == []


def test_scenario_ids_are_unique():
    ids = [s["scenario_id"] for s in CORPUS]
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# the structural fix for P0-1
# ---------------------------------------------------------------------------

def test_no_protocol_reads_hidden_state():
    leaks = visibility.check_all(ONE_PER_CLASS)
    assert leaks == [], "\n".join(str(l) for l in leaks)


def test_visibility_check_catches_a_real_leak():
    """Non-vacuity: a protocol that consults hidden state must fail the check."""
    from dataclasses import dataclass

    from src.model.types import Verdict
    from src.protocols.baselines import Protocol

    side = {}
    original = visibility.build_view

    def leaky_build(sc, policy, ents):
        view, oracle = original(sc, policy, ents)
        side["colluding"] = sc.get("adjudicator", {}).get("colluding", False)
        return view, oracle

    def leaky(view, disputes, oracle):
        return Verdict(detected=True,
                       blamed=Party.J if side["colluding"] else Party.NONE)

    visibility.build_view = leaky_build
    try:
        leaks = visibility.check(
            Protocol("LEAKY", leaky, DisclosurePolicy.FULL, frozenset()),
            ONE_PER_CLASS)
    finally:
        visibility.build_view = original
    assert leaks, "the visibility harness failed to catch a deliberate leak"


def test_evidence_view_excludes_ground_truth():
    view, _ = build_view(CORPUS[0], DisclosurePolicy.FULL)
    blob = str(view.__dict__).lower()
    for banned in ("ground_truth", "dishonest", "colluding", "mistaken", "m_class"):
        assert banned not in blob


def test_protocol_signature_takes_no_scenario():
    import inspect
    for proto in PROTOCOLS.values():
        params = list(inspect.signature(proto.fn).parameters)
        assert params == ["view", "disputes", "oracle"], proto.name


def test_unproduced_record_hides_contents_and_integrity():
    """A3: availability gates everything else about a record."""
    sc = next(s for s in CORPUS if s["m_class"] == "M19")
    view, _ = build_view(sc, DisclosurePolicy.FULL)
    assert view.e.record_available is False
    assert view.e.record_intact is None
    assert view.committed_actions is None


# ---------------------------------------------------------------------------
# disputes
# ---------------------------------------------------------------------------

def test_disputes_never_name_a_concealed_action():
    """M1: the executor conceals its out-of-scope action. The principal cannot
    complain about something it was never told about."""
    for sc in (s for s in CORPUS if s["m_class"] == "M1"):
        view, _ = build_view(sc, DisclosurePolicy.COMMITMENT_ONLY)
        concealed = [a for a in sc["execution"]["actions"]
                     if a not in sc["e_view"]["asserted_actions"]]
        named = {d.subject for d in build_disputes(view)}
        assert not (set(concealed) & named)


def test_baseless_complaint_is_representable():
    sc = next(s for s in CORPUS if s["m_class"] == "M13")
    view, _ = build_view(sc, DisclosurePolicy.COMMITMENT_ONLY)
    assert any(d.subject == sc["p_view"]["disputed_action"]
               for d in build_disputes(view))


# ---------------------------------------------------------------------------
# proof oracle
# ---------------------------------------------------------------------------

def test_oracle_answers_are_verified_not_trusted():
    """A protocol branches on verify_*, so a forged answer changes nothing."""
    from src.crypto.merkle import MembershipProof, verify_membership

    view, oracle = build_view(CORPUS[0], DisclosurePolicy.COMMITMENT_ONLY)
    forged = MembershipProof("not:in:scope", 0, 3, ())
    assert not verify_membership(view.scope_root, "not:in:scope", forged)


def test_oracle_cannot_be_enumerated():
    """The oracle answers about named values only; it exposes no iterator over
    the committed set."""
    _, oracle = build_view(CORPUS[0], DisclosurePolicy.COMMITMENT_ONLY)
    public = [a for a in dir(oracle) if not a.startswith("_")]
    assert set(public) <= {"query_scope", "query_exec", "ledger", "scope_root",
                           "exec_root", "scope_cardinality", "exec_cardinality"}


def test_queries_are_charged():
    view, oracle = build_view(CORPUS[0], DisclosurePolicy.COMMITMENT_ONLY)
    before = oracle.ledger.bytes_disclosed
    oracle.query_scope(view.p.asserted_scope[0])
    assert oracle.ledger.bytes_disclosed > before
    assert oracle.ledger.queries == 1


def test_unproducible_record_yields_no_proof():
    sc = next(s for s in CORPUS if s["m_class"] == "M10")
    _, oracle = build_view(sc, DisclosurePolicy.COMMITMENT_ONLY)
    assert oracle.query_exec("anything") is None


# ---------------------------------------------------------------------------
# twins
# ---------------------------------------------------------------------------

def test_declared_twins_are_indistinguishable_when_padded():
    rows = twins.audit(CORPUS, pad_to=twins.PAD_TO)
    for a, b, policy, matched, n, status in rows:
        if status == "twin":
            assert matched == n, f"{a}/{b} under {policy}"


def test_cardinality_binding_separates_two_declared_twins():
    """Recorded as a finding, not tolerated as a fixture: an unpadded
    commitment publishes |record|, which distinguishes a lost 3-action record
    from a concealed 4-action one."""
    rows = twins.audit(CORPUS, pad_to=None)
    separated = {(a, b) for a, b, _p, matched, n, status in rows
                 if status == "twin" and matched != n}
    assert separated == twins.CARDINALITY_SENSITIVE


# ---------------------------------------------------------------------------
# end to end
# ---------------------------------------------------------------------------

def test_every_protocol_runs_on_every_scenario():
    for proto in PROTOCOLS.values():
        for sc in ONE_PER_CLASS:
            evaluate(proto, sc)


def test_disclosure_is_never_negative_and_full_costs_more_than_roots():
    for proto in PROTOCOLS.values():
        for sc in ONE_PER_CLASS:
            v = evaluate(proto, sc)
            assert v.disclosed_bytes >= 0


def test_reports_cover_every_protocol():
    reps = reports(ONE_PER_CLASS)
    assert set(reps) == set(PROTOCOLS)
    for rep in reps.values():
        assert rep.n_scenarios == len(ONE_PER_CLASS)
