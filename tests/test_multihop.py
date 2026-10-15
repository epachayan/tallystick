"""Three-party phase: specifications, projection, scoring, and the headline claims."""

from __future__ import annotations

import pytest

from src.multihop import boundary, conformance, freeze
from src.multihop.evidence import Disclosure, build_view
from src.multihop.generator import H_CLASSES, generate, load_corpus
from src.multihop.harness import reports
from src.multihop.model import Party3, State, Status3, Truth3, Verdict3, score3
from src.multihop.spec import Message, Spec, holdings, load, precondition_failures
from src.model.types import Outcome


@pytest.fixture(scope="module")
def scs():
    return load_corpus()


@pytest.fixture(scope="module")
def reps(scs):
    return reports(scs)


def _first(scs, h):
    return next(s for s in scs if s["h_class"] == h)


# -- corpus -------------------------------------------------------------------

def test_corpus_on_disk_is_the_generator_output(scs):
    import json
    regenerated = [json.loads(json.dumps(r, sort_keys=True)) for r in generate()]
    assert scs == regenerated


def test_ground_truth_is_constant_within_each_class(scs):
    for h in H_CLASSES:
        assert len({Truth3.from_scenario(s) for s in scs if s["h_class"] == h}) == 1


# -- specifications -----------------------------------------------------------

def test_a_spec_cannot_forward_what_the_sender_never_holds():
    bad = Spec("bad", ("P", "I", "E"), ("G",), (
        Message("grant", "P", "I", True, ("G",), (), (), ()),
        Message("leak", "E", "P", True, ("G",), ("grant",), (), ()),
    ))
    with pytest.raises(ValueError, match="never holds"):
        bad.validate()


def test_only_chain3_puts_executor_signatures_in_principal_hands():
    sent = {m: True for m in ("grant", "grant_ack", "subgrant", "subgrant_ack",
                              "exec_receipt", "report", "report_ack")}
    for name, expected in (("hop3", set()), ("chain3", {"subgrant_ack", "exec_receipt"})):
        at_p = {c.message for c in holdings(load(name), sent)
                if c.holder == "P" and c.signer == "E"}
        assert at_p == expected, name


def test_bearer3_yields_no_signed_copies(scs):
    assert holdings(load("bearer3"), _first(scs, "H1")["sent"]) == ()


def test_chain3_checks_refuse_widening_only_with_an_honest_receiver(scs):
    h2 = _first(scs, "H2")
    assert precondition_failures(load("chain3"), h2["objects"], h2["sent"])
    assert not precondition_failures(load("chain3"), h2["objects"], h2["sent"],
                                     honest=frozenset({"P", "I"}))


# -- projection ---------------------------------------------------------------

def test_cover_story_agreed_before_the_report_reaches_every_copy(scs):
    """H6: I and E re-sign before P sees anything, so even P's own report_ack
    signs the cover version. (The rule that missed this was found by the twin
    audit; this pins the correction.)"""
    h6 = _first(scs, "H6")
    view, _ = build_view(load("hop3"), h6, Disclosure.FULL)
    ack = next(c for c in view.copies if c.message == "report_ack")
    assert h6["disputed"] not in ack.binding("R").contents


def test_after_the_fact_collusion_cannot_touch_an_honest_holders_copy(scs):
    h8 = _first(scs, "H8")
    view, _ = build_view(load("chain3"), h8, Disclosure.FULL)
    at_e = next(c for c in view.copies if c.id == "grant@E")
    at_i = next(c for c in view.copies if c.id == "grant@I")
    assert h8["disputed"] in at_e.binding("G").contents
    assert h8["disputed"] not in at_i.binding("G").contents


# -- scorer -------------------------------------------------------------------

def _truth(**states):
    return Truth3(tuple((p, State(states.get(p.value, "honest"))) for p in Party3))


def test_contradicting_part_of_a_collusion_is_correct_but_blaming_part_is_not():
    t = _truth(P="dishonest", I="dishonest")
    assert score3(t, Verdict3(detected=True, contradicted=frozenset({Party3.I}),
                              attributes_fault=False, status=Status3.CONTRADICTED)
                  ) is Outcome.CORRECT_CONTRADICTION
    assert score3(t, Verdict3(detected=True, blamed=frozenset({Party3.I}),
                              status=Status3.EXPOSED)) is Outcome.FALSE_ACCUSATION


def test_naming_a_mistaken_intermediary_is_over_attribution():
    t = _truth(I="mistaken")
    assert score3(t, Verdict3(detected=True, blamed=frozenset({Party3.I}),
                              status=Status3.EXPOSED)) is Outcome.OVER_ATTRIBUTION


# -- headline claims (finding 14) ---------------------------------------------

def _all(reps, proto, h, outcome=None):
    c = reps[proto][0].per_class[h]
    if outcome is None:
        return c.correct == c.n
    return c.counts.get(outcome, 0) == c.n


def test_re_signing_cannot_localise_and_forwarding_can(reps):
    for h in ("H4", "H5"):
        assert _all(reps, "B13_hop3", h, Outcome.MISSED)
        assert _all(reps, "B13_chain3", h, Outcome.CORRECT_CONTRADICTION)
        assert reps["B13_chain3"][1][h] == 25


def test_upstream_collusion_is_caught_but_only_fully_named_under_chain3(reps):
    assert _all(reps, "B13_hop3", "H8", Outcome.CORRECT_CONTRADICTION)
    assert reps["B13_hop3"][1].get("H8", 0) == 0
    assert reps["B13_chain3"][1]["H8"] == 25


def test_downstream_collusion_resists_every_protocol(reps):
    for name in reps:
        assert _all(reps, name, "H6", Outcome.MISSED), name


def test_extended_duty_frames_an_honest_party_in_both_who_twins(scs):
    from src.multihop.harness import evaluate
    from src.multihop.protocols import PROTOCOLS3
    b17 = PROTOCOLS3["B17_chain3"]
    assert Party3.I in evaluate(b17, _first(scs, "H4")).contradicted   # I honestly lost its copy
    assert Party3.E in evaluate(b17, _first(scs, "H5")).contradicted   # E is honest, unreachable


def test_no_false_attribution_from_any_non_attributive_protocol(reps):
    for name in ("B13_hop3", "B13_chain3", "B17_chain3"):
        assert reps[name][0].false_attribution_rate == 0.0


# -- boundary and gate --------------------------------------------------------

def test_intersection_rule_reproduces_brute_force_and_equality_does_not(scs):
    rows = boundary.classify(scs)
    assert all(inter == brute for _a, _b, _p, brute, inter, _e, _da, _db in rows)
    disagree = {(a, b) for a, b, _p, brute, _i, eq, _da, _db in rows if eq != brute}
    assert disagree == {("H8", "H9")}


def test_intersection_rule_agrees_with_the_published_two_party_boundary():
    assert boundary.two_party_rule_check() == []


def test_multihop_gate_stages_pass(scs, reps):
    _rows, errs = boundary.check(scs, reps)
    assert errs == []
    assert conformance.run(scs) == []
    assert freeze.check() == []
