"""Protocol baselines, refactored onto evidence-only input (step 2).

Every protocol has the signature

    evaluate(view: EvidenceView, disputes: tuple[Dispute, ...],
             oracle: ProofOracle) -> Verdict

and receives no scenario, no ground truth, no party states, no
`adjudicator.colluding` and no `key_claim.genuine`. Where a v0.9 baseline read
the true scope or the true execution record, it now either

  * reads the COMMITTED artifact, when the disclosure policy transmits it
    and the record was actually produced, or
  * asks the oracle about a NAMED value and verifies the returned proof.

Two consequences of doing this honestly are worth stating up front, because
they move numbers:

1. `B7_verifiable_adjudication` no longer reads whether the adjudicator is
   colluding. It compares the verdict the adjudicator PUBLISHED against the one
   it recomputes from the transcript, and blames J only on a mismatch. That is
   the mechanism the baseline always claimed to be.

2. Dispute-driven protocols can only query values a party can NAME. A principal
   cannot dispute an action the executor concealed from it. Concealed overreach
   therefore stops being reachable by selective query, which is a real property
   of the mechanism and was previously hidden by the oracle.

Partially offsetting (2): a cardinality-binding commitment publishes |set| to
any verifier, so an executor that asserts fewer actions than its committed
record contains is contradicted at zero content disclosure. Every use of this
is flagged `cardinality_binding` so its contribution can be measured and, if
you decide it is too strong an assumption, subtracted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..model.dispute import ClaimType, Dispute
from ..model.evidence import (
    DisclosurePolicy,
    EvidenceView,
    ProofOracle,
    check_exec_membership,
    check_scope_membership,
)
from ..model.types import Party, Verdict, VerdictStatus

SIG_BYTES = 96
HASH_BYTES = 32
ROOT_BYTES = 32
SHORT_TERM_KEY_BYTES = 128
ATTESTATION_BYTES = 96


@dataclass(frozen=True)
class Protocol:
    name: str
    fn: Callable[[EvidenceView, tuple, ProofOracle], Verdict]
    policy: DisclosurePolicy
    entitlements: frozenset[str] = frozenset()


PROTOCOLS: dict[str, Protocol] = {}


def register(name, policy, entitlements=frozenset()):
    def deco(fn):
        PROTOCOLS[name] = Protocol(name, fn, policy, entitlements)
        return fn
    return deco


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _text_bytes(*items) -> int:
    total = 0
    for it in items:
        if it is None:
            continue
        if isinstance(it, (tuple, list)):
            total += sum(len(str(x).encode()) for x in it)
        elif isinstance(it, bool):
            total += 1
        elif isinstance(it, str):
            total += len(it.encode())
        else:
            total += 8
    return total


def _full_disclosure(view: EvidenceView) -> int:
    """Bytes actually transmitted under a full-disclosure protocol: the
    committed artifacts that were produced, plus both signatures."""
    return (_text_bytes(view.committed_scope, view.committed_actions,
                        view.auth_exists, view.delivery_ack_exists)
            + 2 * SIG_BYTES)


def _commitment_disclosure(view: EvidenceView, oracle: ProofOracle) -> int:
    """Roots and signatures, plus every proof the protocol actually asked for."""
    return 2 * ROOT_BYTES + 2 * SIG_BYTES + oracle.ledger.bytes_disclosed


def _blame(p_bad, e_bad) -> Party:
    if p_bad and e_bad:
        return Party.BOTH
    if p_bad:
        return Party.P
    if e_bad:
        return Party.E
    return Party.NONE


def _cardinality_mismatch(view: EvidenceView) -> bool:
    """The executor asserts a record whose size contradicts its own commitment.

    Available under commitment-only disclosure because a sound root binds |set|.
    Unavailable when commitments are padded to a fixed width: that is precisely
    what padding buys, and reading the padded width as if it were the real one
    would manufacture a contradiction in every scenario.
    """
    return (view.pad_to is None
            and view.exec_cardinality is not None
            and view.e.asserted_actions is not None
            and len(set(view.e.asserted_actions)) != view.exec_cardinality)


# ---------------------------------------------------------------------------
# B0 -- the deployed agentic default: bearer token + provider-side log.
# ---------------------------------------------------------------------------

@register("B0_bearer_executor_log", DisclosurePolicy.FULL)
def b0_bearer_executor_log(view, disputes, oracle):
    disclosed = _text_bytes(view.e.asserted_scope, view.e.asserted_actions,
                            view.e.asserted_auth_issued, view.e.asserted_result_received)
    conflict = bool(disputes)
    return Verdict(
        detected=conflict,
        blamed=Party.NONE,
        status=VerdictStatus.SUSPECTED if conflict else VerdictStatus.CLEAR,
        disclosed_bytes=disclosed,
        reasons=("divergence visible, nothing binds either party to a prior statement",)
        if conflict else (),
    )


# ---------------------------------------------------------------------------
# B1 -- PeerReview-style bilateral commitment (Haeberlen et al. 2007).
# ---------------------------------------------------------------------------

def _bilateral_findings(view: EvidenceView):
    """Shared body of B1/B3/B9. Returns (p_reasons, e_reasons, unproduced)."""
    p_bad: list[str] = []
    e_bad: list[str] = []
    unproduced: list[Party] = []

    if not view.auth_committed:
        return p_bad, e_bad, unproduced

    scope = view.committed_scope
    actions = view.committed_actions
    p, e = view.p, view.e

    # -- principal side ------------------------------------------------------
    if view.auth_exists and not p.asserted_auth_issued:
        p_bad.append("repudiated a signed authorization")
    if p.asserted_scope is not None and scope is not None and tuple(p.asserted_scope) != tuple(scope):
        p_bad.append("asserted scope contradicts the signed authorization")
    if view.delivery_ack_exists and not p.asserted_result_received:
        p_bad.append("denied a receipt it acknowledged")
    if p.record_intact is False:
        p_bad.append("stored copy fails signature verification")
    if not p.record_available:
        unproduced.append(Party.P)

    # -- executor side -------------------------------------------------------
    if not view.auth_exists and e.asserted_auth_issued and e.asserted_scope:
        e_bad.append("presented an authorization bearing no valid principal signature")
    if e.asserted_scope is not None and scope is not None and tuple(e.asserted_scope) != tuple(scope):
        e_bad.append("asserted scope contradicts the signed authorization")

    if not e.record_available:
        unproduced.append(Party.E)
    elif e.record_intact is False:
        e_bad.append("stored execution record fails signature verification")
    elif e.asserted_actions is not None and actions is not None \
            and sorted(e.asserted_actions) != sorted(actions):
        e_bad.append("asserted actions diverge from its own signed execution record")

    if scope is not None and actions is not None:
        overreach = [a for a in actions if a not in scope]
        if overreach and "asserted actions diverge from its own signed execution record" not in e_bad:
            e_bad.append("executed outside the granted scope")

    return p_bad, e_bad, unproduced


@register("B1_bilateral_commitment", DisclosurePolicy.FULL)
def b1_bilateral_commitment(view, disputes, oracle):
    disclosed = _full_disclosure(view)
    if not view.auth_committed:
        return Verdict(detected=True, blamed=Party.NONE,
                       status=VerdictStatus.UNRESOLVED, disclosed_bytes=disclosed,
                       reasons=("no commitment exists to reason from",))

    p_bad, e_bad, unproduced = _bilateral_findings(view)
    # B1 is the naive scheme: it cannot tell loss from concealment.
    if Party.E in unproduced:
        e_bad = e_bad + ["could not produce its execution record"]
    blamed = _blame(p_bad, e_bad)
    return Verdict(
        detected=blamed is not Party.NONE,
        blamed=blamed,
        status=VerdictStatus.EXPOSED if blamed is not Party.NONE else VerdictStatus.CLEAR,
        disclosed_bytes=disclosed,
        reasons=tuple(p_bad + e_bad),
    )


# ---------------------------------------------------------------------------
# B2 -- commitment-only adjudication. Integrity and existence survive;
# anything needing the adjudicator to read contents does not.
# ---------------------------------------------------------------------------

@register("B2_commitment_only", DisclosurePolicy.COMMITMENT_ONLY)
def b2_commitment_only(view, disputes, oracle):
    disclosed = 2 * HASH_BYTES + 2 * SIG_BYTES
    if not view.auth_committed:
        return Verdict(detected=True, blamed=Party.NONE,
                       status=VerdictStatus.UNRESOLVED, disclosed_bytes=disclosed,
                       reasons=("no commitment exists to reason from",))

    p, e = view.p, view.e
    p_bad, e_bad = [], []

    if p.record_intact is False:
        p_bad.append("stored copy does not match its commitment")
    if e.record_available and e.record_intact is False:
        e_bad.append("stored copy does not match its commitment")
    if view.auth_exists and not p.asserted_auth_issued:
        p_bad.append("repudiated an authorization with a live commitment")
    if not view.auth_exists and e.asserted_auth_issued and e.asserted_scope:
        e_bad.append("claims an authorization for which no commitment exists")
    if view.delivery_ack_exists and not p.asserted_result_received:
        p_bad.append("denied a receipt for which an acknowledgement exists")

    blamed = _blame(p_bad, e_bad)
    return Verdict(detected=blamed is not Party.NONE, blamed=blamed,
                   status=VerdictStatus.EXPOSED if blamed is not Party.NONE else VerdictStatus.CLEAR,
                   disclosed_bytes=disclosed, reasons=tuple(p_bad + e_bad))


# ---------------------------------------------------------------------------
# B3 -- B1 plus PeerReview's suspected / exposed distinction.
# ---------------------------------------------------------------------------

@register("B3_suspected_exposed", DisclosurePolicy.FULL)
def b3_suspected_exposed(view, disputes, oracle):
    disclosed = _full_disclosure(view)
    if not view.auth_committed:
        return Verdict(detected=True, blamed=Party.NONE,
                       status=VerdictStatus.SUSPECTED, disclosed_bytes=disclosed)

    p_bad, e_bad, unproduced = _bilateral_findings(view)
    blamed = _blame(p_bad, e_bad)
    status = (VerdictStatus.EXPOSED if blamed is not Party.NONE
              else (VerdictStatus.SUSPECTED if unproduced else VerdictStatus.CLEAR))
    return Verdict(detected=bool(p_bad or e_bad or unproduced), blamed=blamed,
                   status=status, disclosed_bytes=disclosed,
                   reasons=tuple(p_bad + e_bad))


# ---------------------------------------------------------------------------
# B4 -- selective disclosure by membership query over commitments.
#
# Exhaustive over every value a party NAMED. It cannot sweep the committed set,
# because a Merkle root is not enumerable: that is the whole point of it.
# ---------------------------------------------------------------------------

@register("B4_scope_predicates", DisclosurePolicy.COMMITMENT_ONLY)
def b4_scope_predicates(view, disputes, oracle):
    if not view.auth_committed:
        return Verdict(detected=True, blamed=Party.NONE, status=VerdictStatus.SUSPECTED,
                       disclosed_bytes=_commitment_disclosure(view, oracle))

    p, e = view.p, view.e
    p_bad, e_bad, flags = [], [], set()
    unproduced = not e.record_available

    if p.record_intact is False:
        p_bad.append("stored copy does not match its commitment")
    if view.auth_exists and not p.asserted_auth_issued:
        p_bad.append("repudiated an authorization with a live commitment")
    if view.delivery_ack_exists and not p.asserted_result_received:
        p_bad.append("denied a receipt it acknowledged")
    if not view.auth_exists and e.asserted_auth_issued and e.asserted_scope:
        e_bad.append("claims an authorization with no commitment")
    if e.record_available and e.record_intact is False:
        e_bad.append("stored record does not match its commitment")

    if _cardinality_mismatch(view):
        e_bad.append("committed record binds a different number of actions than asserted")
        flags.add("cardinality_binding")

    # every action the executor admits to, tested against the committed scope
    if e.asserted_actions is not None:
        for a in e.asserted_actions:
            if check_scope_membership(view, oracle, a) is False:
                e_bad.append(f"non-membership proof: '{a}' is not in the committed scope")
                break

    # every scope entry the two accounts disagree about. Both directions must be
    # queried: an entry E claims and P omits is either P dropping a real grant or
    # E inventing one, and only the proof says which. Stopping at the first
    # answer would let one party's lie mask the other's (M11).
    if p.asserted_scope is not None and e.asserted_scope is not None:
        contested = [a for a in e.asserted_scope if a not in p.asserted_scope]
        for a in contested:
            r = check_scope_membership(view, oracle, a)
            if r is True and not p_bad:
                p_bad.append(f"membership proof: '{a}' IS in the committed scope")
            elif r is False and not e_bad:
                e_bad.append(f"non-membership proof: '{a}' is not in the committed scope")

    blamed = _blame(p_bad, e_bad)
    status = (VerdictStatus.EXPOSED if blamed is not Party.NONE
              else (VerdictStatus.SUSPECTED if unproduced else VerdictStatus.CLEAR))
    return Verdict(detected=bool(p_bad or e_bad or unproduced), blamed=blamed,
                   status=status, disclosed_bytes=_commitment_disclosure(view, oracle),
                   queries=oracle.ledger.queries, reasons=tuple(p_bad + e_bad),
                   flags=frozenset(flags))


# ---------------------------------------------------------------------------
# B5 -- dispute-driven selective disclosure: queries bounded by the complaint.
# ---------------------------------------------------------------------------

def _b5_core(view, disputes, oracle):
    p, e = view.p, view.e
    p_bad, e_bad, flags = [], [], set()
    unproduced = not e.record_available

    if p.record_intact is False:
        p_bad.append("stored copy does not match its commitment")
    if view.auth_exists and not p.asserted_auth_issued:
        p_bad.append("repudiated an authorization with a live commitment")
    if view.delivery_ack_exists and not p.asserted_result_received:
        p_bad.append("denied a receipt it acknowledged")
    if not view.auth_exists and e.asserted_auth_issued and e.asserted_scope:
        e_bad.append("claims an authorization with no commitment")
    if e.record_available and e.record_intact is False:
        e_bad.append("stored record does not match its commitment")

    if _cardinality_mismatch(view):
        e_bad.append("committed record binds a different number of actions than asserted")
        flags.add("cardinality_binding")

    for d in disputes:
        if d.claim_type is ClaimType.UNAUTHORIZED_EXECUTION and d.claimant is Party.P:
            if check_scope_membership(view, oracle, d.subject) is False:
                e_bad.append(f"non-membership: '{d.subject}' not in committed scope")
        elif d.claim_type is ClaimType.SCOPE_VIOLATION and d.claimant is Party.E:
            r = check_scope_membership(view, oracle, d.subject)
            if r is True:
                p_bad.append(f"membership: '{d.subject}' IS in the committed scope")
            elif r is False:
                e_bad.append(f"non-membership: '{d.subject}' not in committed scope")

    return p_bad, e_bad, unproduced, flags


@register("B5_dispute_driven", DisclosurePolicy.COMMITMENT_ONLY)
def b5_dispute_driven(view, disputes, oracle):
    if not view.auth_committed:
        return Verdict(detected=True, blamed=Party.NONE, status=VerdictStatus.SUSPECTED,
                       disclosed_bytes=_commitment_disclosure(view, oracle))
    p_bad, e_bad, unproduced, flags = _b5_core(view, disputes, oracle)
    blamed = _blame(p_bad, e_bad)
    status = (VerdictStatus.EXPOSED if blamed is not Party.NONE
              else (VerdictStatus.SUSPECTED if unproduced else VerdictStatus.CLEAR))
    return Verdict(detected=bool(p_bad or e_bad or unproduced), blamed=blamed,
                   status=status, disclosed_bytes=_commitment_disclosure(view, oracle),
                   queries=oracle.ledger.queries, reasons=tuple(p_bad + e_bad),
                   flags=frozenset(flags))


# ---------------------------------------------------------------------------
# B6 -- B5 plus complainant accountability: a baseless probe exposes the prober.
# ---------------------------------------------------------------------------

def _b6_core(view, disputes, oracle):
    if not view.auth_committed:
        return [], [], False, set()
    p_bad, e_bad, unproduced, flags = _b5_core(view, disputes, oracle)
    named = view.p.disputed_action
    if named is not None and view.auth_exists:
        if check_scope_membership(view, oracle, named) is True:
            p_bad.append(f"baseless complaint: '{named}' IS in the committed scope")
            flags.add("baseless_complaint")
    return p_bad, e_bad, unproduced, flags


@register("B6_accountable_queries", DisclosurePolicy.COMMITMENT_ONLY)
def b6_accountable_queries(view, disputes, oracle):
    if not view.auth_committed:
        return Verdict(detected=True, blamed=Party.NONE, status=VerdictStatus.SUSPECTED,
                       disclosed_bytes=_commitment_disclosure(view, oracle))
    p_bad, e_bad, unproduced, flags = _b6_core(view, disputes, oracle)
    blamed = _blame(p_bad, e_bad)
    status = (VerdictStatus.EXPOSED if blamed is not Party.NONE
              else (VerdictStatus.SUSPECTED if unproduced else VerdictStatus.CLEAR))
    return Verdict(detected=bool(p_bad or e_bad or unproduced), blamed=blamed,
                   status=status, disclosed_bytes=_commitment_disclosure(view, oracle),
                   queries=oracle.ledger.queries, reasons=tuple(p_bad + e_bad),
                   flags=frozenset(flags))


# ---------------------------------------------------------------------------
# B7 -- publicly verifiable adjudication.
#
# The adjudicator must publish the proofs it relied on. Anyone can recompute the
# verdict from the transcript. A corrupt adjudicator must therefore either
# publish proofs that contradict its own verdict, or withhold the transcript.
#
# This is the de-oracled version: it compares the PUBLISHED verdict against the
# RECOMPUTED one, rather than reading whether the adjudicator is colluding.
# ---------------------------------------------------------------------------

@register("B7_verifiable_adjudication", DisclosurePolicy.COMMITMENT_ONLY)
def b7_verifiable_adjudication(view, disputes, oracle):
    base = b6_accountable_queries(view, disputes, oracle)
    published = view.adjudicator_published_blame
    if published is not None and published is not base.blamed:
        return Verdict(detected=True, blamed=Party.J,
                       status=VerdictStatus.EXPOSED,
                       disclosed_bytes=base.disclosed_bytes,
                       queries=base.queries,
                       reasons=base.reasons + (
                           f"published verdict '{published.value}' does not recompute "
                           f"from the transcript (recomputed '{base.blamed.value}')",),
                       flags=base.flags | {"transcript_mismatch"})
    return base


@register("B6c_under_collusion", DisclosurePolicy.COMMITMENT_ONLY)
def b6c_under_collusion(view, disputes, oracle):
    """B6 as actually deployed: nothing checks the adjudicator, so its published
    verdict simply stands."""
    base = b6_accountable_queries(view, disputes, oracle)
    published = view.adjudicator_published_blame
    if published is not None:
        return Verdict(detected=True, blamed=published,
                       status=VerdictStatus.EXPOSED if published is not Party.NONE
                       else VerdictStatus.CLEAR,
                       disclosed_bytes=base.disclosed_bytes, queries=base.queries,
                       reasons=base.reasons + ("adjudicator's published verdict accepted unchecked",),
                       flags=base.flags)
    return base


# ---------------------------------------------------------------------------
# B9 -- non-attributive adjudication.
#
# A principal who MISREMEMBERS and one who LIES produce identical evidence. B9
# changes the verdict vocabulary to make a claim about the RECORD rather than
# about the person.
# ---------------------------------------------------------------------------

def _contradicted_parties(view: EvidenceView) -> list[Party]:
    if not view.auth_committed or not view.auth_exists:
        return []
    p_bad, e_bad, _ = _bilateral_findings(view)
    out: list[Party] = []
    if p_bad or (view.p.disputed_action is not None and view.committed_scope is not None
                 and view.p.disputed_action in view.committed_scope):
        out.append(Party.P)
    if e_bad:
        out.append(Party.E)
    return out


@register("B9_non_attributive", DisclosurePolicy.FULL)
def b9_non_attributive(view, disputes, oracle):
    contradicted = tuple(_contradicted_parties(view))
    return Verdict(detected=bool(contradicted), blamed=Party.NONE,
                   contradicted=contradicted, attributes_fault=False,
                   status=VerdictStatus.CONTRADICTED if contradicted else VerdictStatus.CLEAR,
                   disclosed_bytes=_full_disclosure(view))


@register("B10_composed", DisclosurePolicy.FULL)
def b10_composed(view, disputes, oracle):
    base = b9_non_attributive(view, disputes, oracle)
    contradicted = list(base.contradicted)
    status, detected = base.status, base.detected
    published = view.adjudicator_published_blame
    recomputed = Party.NONE if not contradicted else (
        Party.BOTH if len(contradicted) > 1 else contradicted[0])
    if published is not None and published is not recomputed:
        contradicted.append(Party.J)
        detected, status = True, VerdictStatus.CONTRADICTED
    if not view.auth_committed:
        detected, status = True, VerdictStatus.UNRESOLVED
    return Verdict(detected=detected, blamed=Party.NONE,
                   contradicted=tuple(contradicted), attributes_fault=False,
                   status=status, disclosed_bytes=base.disclosed_bytes)


# ---------------------------------------------------------------------------
# B11 -- stateful adjudication. A single claim of loss is an assertion; a
# PATTERN of claimed losses is a behaviour, and T4 says behaviours separate.
# ---------------------------------------------------------------------------

BASE_FAILURE_RATE = 0.25
ALPHA = 0.05


def _binom_sf(k, n, p):
    from math import comb
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


@register("B11_stateful", DisclosurePolicy.FULL, frozenset({"history"}))
def b11_stateful(view, disputes, oracle):
    base = b10_composed(view, disputes, oracle)
    hist = dict(view.history or ())
    flagged = list(base.contradicted)
    hit = False
    # Both parties' histories, for the same reason the duty is symmetric: the
    # v1 detector read only e_disputes because only the executor ever had any.
    for party, dkey, skey in ((Party.E, "e_disputes", "e_suspensions"),
                              (Party.P, "p_disputes", "p_suspensions")):
        n, k = hist.get(dkey, 0), hist.get(skey, 0)
        if n >= 5 and _binom_sf(k, n, BASE_FAILURE_RATE) < ALPHA:
            hit = True
            if party not in flagged:
                flagged.append(party)
    if hit:
        return Verdict(detected=True, blamed=Party.NONE, contradicted=tuple(flagged),
                       attributes_fault=False, status=VerdictStatus.CONTRADICTED,
                       disclosed_bytes=base.disclosed_bytes,
                       flags=frozenset({"pattern_flagged"}))
    return base


# ---------------------------------------------------------------------------
# B7r / B15 -- the excuse-ranking pair (Kremer-Markowitch-Zhou 2002 sec. 7).
# ---------------------------------------------------------------------------

@register("B7r_under_revocation", DisclosurePolicy.COMMITMENT_ONLY)
def b7r_under_revocation(view, disputes, oracle):
    base = b7_verifiable_adjudication(view, disputes, oracle)
    if view.key_revocation_claimed:
        return Verdict(detected=True, blamed=Party.NONE,
                       status=VerdictStatus.EVIDENCE_VOIDED,
                       disclosed_bytes=base.disclosed_bytes, queries=base.queries,
                       reasons=("revocation claim voids the signatures already issued",))
    return base


@register("B15_short_term_keys", DisclosurePolicy.FULL)
def b15_short_term_keys(view, disputes, oracle):
    base = b10_composed(view, disputes, oracle)
    disclosed = base.disclosed_bytes + SHORT_TERM_KEY_BYTES
    if not view.key_revocation_claimed:
        return Verdict(detected=base.detected, blamed=base.blamed,
                       contradicted=base.contradicted, attributes_fault=False,
                       status=base.status, disclosed_bytes=disclosed)
    # The run's short-term key cannot be revoked, so the excuse is unavailable
    # and adjudication proceeds on the committed record regardless of the claim.
    contradicted = list(base.contradicted)
    if view.auth_exists and view.committed_scope is not None and view.committed_actions is not None:
        if [a for a in view.committed_actions if a not in view.committed_scope]:
            if Party.E not in contradicted:
                contradicted.append(Party.E)
    return Verdict(detected=bool(contradicted), blamed=Party.NONE,
                   contradicted=tuple(contradicted), attributes_fault=False,
                   status=VerdictStatus.CONTRADICTED if contradicted else VerdictStatus.CLEAR,
                   disclosed_bytes=disclosed, flags=frozenset({"excuse_removed"}))


# ---------------------------------------------------------------------------
# B16 -- external attestation, and the T10 relocation test.
# ---------------------------------------------------------------------------

@register("B16c_custodial_attestor", DisclosurePolicy.FULL, frozenset({"custodial_copy"}))
def b16c_custodial_attestor(view, disputes, oracle):
    """A custodian, not an attestor: it HOLDS the contents. Declared as an
    entitlement so the assumption is visible rather than assumed away."""
    base = b15_short_term_keys(view, disputes, oracle)
    if not view.attestor_present:
        return base
    disclosed = base.disclosed_bytes + ATTESTATION_BYTES
    contradicted = list(base.contradicted)

    if view.attestor_available:
        if view.auth_exists and view.committed_scope is not None \
                and view.custodial_actions is not None:
            if [a for a in view.custodial_actions if a not in view.committed_scope]:
                if Party.E not in contradicted:
                    contradicted.append(Party.E)
        return Verdict(detected=bool(contradicted), blamed=Party.NONE,
                       contradicted=tuple(contradicted), attributes_fault=False,
                       status=VerdictStatus.CONTRADICTED if contradicted else VerdictStatus.CLEAR,
                       disclosed_bytes=disclosed, flags=frozenset({"attested"}))
    # The attestor's own outage is indistinguishable from collusion with the
    # party it was meant to constrain: M19's structure, one level out.
    return Verdict(detected=True, blamed=Party.NONE,
                   contradicted=tuple(c for c in contradicted if c is not Party.E),
                   attributes_fault=False, status=VerdictStatus.UNRESOLVED,
                   disclosed_bytes=disclosed, flags=frozenset({"attestor_unavailable"}))


@register("B16d_digest_attestor", DisclosurePolicy.FULL)
def b16d_digest_attestor(view, disputes, oracle):
    """A realistic attestor holds a DIGEST. It can prove a record existed and was
    intact at time t. It cannot say what the record contained, so overreach --
    which needs contents -- stays unadjudicable."""
    base = b15_short_term_keys(view, disputes, oracle)
    if not view.attestor_present:
        return base
    disclosed = base.disclosed_bytes + ATTESTATION_BYTES
    contradicted = [c for c in base.contradicted if c is not Party.E]

    if view.attestor_available and view.e.record_available:
        return Verdict(detected=base.detected, blamed=Party.NONE,
                       contradicted=base.contradicted, attributes_fault=False,
                       status=base.status, disclosed_bytes=disclosed)
    flag = "attested_existence_only" if view.attestor_available else "attestor_unavailable"
    return Verdict(detected=True, blamed=Party.NONE, contradicted=tuple(contradicted),
                   attributes_fault=False, status=VerdictStatus.UNRESOLVED,
                   disclosed_bytes=disclosed, flags=frozenset({flag}))


# ---------------------------------------------------------------------------
# B13 -- witness-carrying / self-verifying protocol messages.
#
#     P -> E   authorization, authorization commitment, P's signature
#     E -> P   receipt, authorization commitment, E's signature
#     E executes
#     E -> P   execution receipt, authorization + execution commitment, E's signature
#
# Two things follow from that chain, and they are what this baseline exists to
# test.
#
# 1. EACH PARTY HOLDS THE COUNTERPARTY'S SIGNATURE over the same commitments.
#    A party losing its own log therefore destroys nothing: the other side can
#    still produce the artifact. "I lost my record" stops voiding the
#    commitment, though it still withholds the contents.
#
# 2. A COMMITMENT CAN BE TESTED AGAINST AN ASSERTION WITHOUT OPENING IT.
#    If a party asserts a scope, recompute the root from what it asserted and
#    compare. A mismatch contradicts the assertion, and the true set is never
#    disclosed -- the only input to the check is what the party volunteered.
#
#    Every baseline before this one compared an assertion against the TRUE set,
#    which is why commitment-only adjudication looked semantically blind. It is
#    not. It is blind to facts nobody asserted; assertions check themselves.
#
# The vocabulary is non-attributive, for the same reason as B9: a mismatch is a
# claim about the record and cannot separate misremembering from lying.
# ---------------------------------------------------------------------------

WITNESS_SIG_COUNT = 3        # P's grant, E's acknowledgement, E's execution receipt


def _root_of(values, view: EvidenceView) -> str | None:
    """Recompute a commitment root from an asserted set, padded the same way the
    committed one was. Returns None when the assertion cannot form a set."""
    from ..crypto.merkle import MerkleError, build_root
    from ..model.evidence import pad_set

    if values is None:
        return None
    try:
        return build_root(pad_set(list(values), view.pad_to))
    except (MerkleError, ValueError):
        # duplicates, or an assertion larger than the padded width. Either way
        # it cannot be the committed set.
        return "<unformable>"


@register("B13_witness_messages", DisclosurePolicy.COMMITMENT_ONLY)
def b13_witness_messages(view, disputes, oracle):
    disclosed = 2 * ROOT_BYTES + WITNESS_SIG_COUNT * SIG_BYTES
    p, e = view.p, view.e
    contradicted: list[Party] = []
    reasons: list[str] = []
    flags: set[str] = set()

    if not view.auth_committed:
        # No commitment was ever exchanged, so there is no witness to carry.
        return Verdict(detected=True, blamed=Party.NONE, attributes_fault=False,
                       status=VerdictStatus.UNRESOLVED, disclosed_bytes=disclosed,
                       reasons=("no committed message chain exists",))

    def contradict(party, why):
        if party not in contradicted:
            contradicted.append(party)
        reasons.append(why)

    # -- existence, from the counterparty's held signature -------------------
    if view.auth_exists and not p.asserted_auth_issued:
        contradict(Party.P, "repudiated a grant the executor holds signed")
    if not view.auth_exists and e.asserted_auth_issued and e.asserted_scope:
        contradict(Party.E, "claims a grant the principal never signed")
    if view.exec_receipt_held and not p.asserted_result_received:
        contradict(Party.P, "denied delivery it issued a signed receipt for")

    # -- assertions tested against the commitments, without opening them -----
    if view.scope_root is not None:
        if p.asserted_scope is not None and _root_of(p.asserted_scope, view) != view.scope_root:
            contradict(Party.P, "asserted scope does not recompute to the committed root")
            flags.add("root_recomputation")
        if e.asserted_scope is not None and _root_of(e.asserted_scope, view) != view.scope_root:
            contradict(Party.E, "asserted scope does not recompute to the committed root")
            flags.add("root_recomputation")

    if view.exec_root is not None and e.asserted_actions is not None:
        if _root_of(e.asserted_actions, view) != view.exec_root:
            contradict(Party.E, "asserted execution record does not recompute to "
                                "the committed root")
            flags.add("root_recomputation")

    # -- integrity ----------------------------------------------------------
    if p.record_intact is False:
        contradict(Party.P, "stored copy fails against the commitment it holds")
    if e.record_intact is False:
        contradict(Party.E, "stored copy fails against the commitment it holds")

    # -- one accountable query, and only for an explicitly named complaint ---
    # The complainant already disclosed this item by naming it, so answering
    # costs no privacy it had not already spent. Disclosure stays O(1) in the
    # size of the record: one query, bounded by the complaint.
    named = p.disputed_action
    if named is not None and view.auth_exists:
        if check_scope_membership(view, oracle, named) is True:
            contradict(Party.P, f"baseless complaint: '{named}' IS in the committed scope")
            flags.add("baseless_complaint")
        disclosed += oracle.ledger.bytes_disclosed

    # -- the adjudicator's own transcript -----------------------------------
    # C_witness: a published verdict must recompute from the published witnesses.
    published = view.adjudicator_published_blame
    recomputed = (Party.NONE if not contradicted
                  else (Party.BOTH if len(contradicted) > 1 else contradicted[0]))
    if published is not None and published is not recomputed:
        contradict(Party.J, f"published verdict '{published.value}' does not recompute "
                            f"from the witnesses")
        flags.add("transcript_mismatch")

    return Verdict(detected=bool(contradicted), blamed=Party.NONE,
                   contradicted=tuple(contradicted), attributes_fault=False,
                   status=VerdictStatus.CONTRADICTED if contradicted else VerdictStatus.CLEAR,
                   disclosed_bytes=disclosed, queries=oracle.ledger.queries,
                   reasons=tuple(reasons), flags=frozenset(flags))


# ---------------------------------------------------------------------------
# B17 -- B13 plus a DUTY TO ANSWER.
#
# B13's residual is exactly the four classes where the executor asserts nothing
# about its record (M19, M20, M22, M24). Recomputation needs an assertion to
# check, so silence is a refuge. This baseline tests whether closing that refuge
# resolves the classes or merely relocates the ambiguity.
#
# The rule: a party holding a commitment must, on demand, either open it or
# produce a proof about the specific item in question. Failing to do either is
# itself a contradiction -- not of what it said, but of the duty it accepted
# when it signed the commitment.
#
# The honest question this is designed to answer:
#
#     Does an obligation to speak buy resolution, or does it buy a new excuse?
#
# Note carefully what this baseline does NOT do. It does not read the withheld
# record. Non-production is treated as a first-class observable act, which it
# is: the counterparty holds E's signature over the execution commitment, so
# the record's EXISTENCE is established even when its contents are not.
# Refusing to open a commitment you demonstrably made is a different act from
# never having made one.
# ---------------------------------------------------------------------------

@register("B17_duty_to_answer", DisclosurePolicy.COMMITMENT_ONLY)
def b17_duty_to_answer(view, disputes, oracle):
    base = b13_witness_messages(view, disputes, oracle)
    if not view.auth_committed:
        return base

    contradicted = list(base.contradicted)
    reasons = list(base.reasons)
    flags = set(base.flags)

    # The duty attaches only where a commitment demonstrably exists. Without a
    # witnessed commitment there is nothing the party can be held to.
    #
    # It attaches SYMMETRICALLY. The v1 version of this baseline held only the
    # executor to it, because the corpus only ever asked the executor to produce
    # anything (RC-H9). That was inherited, not chosen.
    exec_duty = view.exec_root is not None and view.exec_receipt_held
    auth_duty = view.scope_root is not None and view.auth_receipt_held

    if exec_duty and not view.exec_record_produced:
        if Party.E not in contradicted:
            contradicted.append(Party.E)
        reasons.append("executor failed to answer for a commitment it signed and "
                       "the principal holds")
        flags.add("duty_breach")

    if auth_duty and not view.p.record_available:
        # The executor holds P's signature over the authorization commitment, so
        # the grant's existence is established even when P will not produce its
        # copy. Same duty, same breach, other party.
        if Party.P not in contradicted:
            contradicted.append(Party.P)
        reasons.append("principal failed to answer for a commitment it signed and "
                       "the executor holds")
        flags.add("duty_breach")

    # A party that answers nothing about the record ALSO answers nothing when
    # asked about a specific disputed item. The distinction matters: opening the
    # whole record is not required, only answering the question actually asked.
    if exec_duty and view.exec_record_produced and view.e.asserted_actions is None:
        named = view.p.disputed_action
        if named is not None and check_exec_membership(view, oracle, named) is None:
            if Party.E not in contradicted:
                contradicted.append(Party.E)
            reasons.append(f"declined to answer whether '{named}' is in its "
                           f"committed record")
            flags.add("duty_breach")

    return Verdict(detected=bool(contradicted), blamed=Party.NONE,
                   contradicted=tuple(contradicted), attributes_fault=False,
                   status=VerdictStatus.CONTRADICTED if contradicted
                   else VerdictStatus.CLEAR,
                   disclosed_bytes=base.disclosed_bytes,
                   queries=oracle.ledger.queries,
                   reasons=tuple(reasons), flags=frozenset(flags))
