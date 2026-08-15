"""Explicit dispute semantics (step 8).

The v0.9 baselines decided for themselves what was in dispute, and did it by
comparing the TRUE authorization against the TRUE execution:

    disputed_actions = [a for a in true_actions if a not in true_scope]

That is a second oracle. A real adjudicator receives a complaint. The
complainant can only name what it knows, which is what the other side asserted
plus what it explicitly disputed -- never the action the counterparty concealed.

Disputes here are built from the EvidenceView alone. This materially changes
what dispute-driven protocols can reach, and it should: a principal cannot
complain about an action it was never told about.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .evidence import EvidenceView
from .types import Party


class ClaimType(str, Enum):
    UNAUTHORIZED_EXECUTION = "unauthorized_execution"
    AUTHORIZATION_DENIED = "authorization_denied"
    EXECUTION_DENIED = "execution_denied"
    RECEIPT_DENIED = "receipt_denied"
    SCOPE_VIOLATION = "scope_violation"
    EQUIVOCATION = "equivocation"


class PredicateKind(str, Enum):
    IN_SCOPE = "in_scope"
    NOT_IN_SCOPE = "not_in_scope"
    IN_RECORD = "in_record"
    NOT_IN_RECORD = "not_in_record"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


@dataclass(frozen=True)
class Predicate:
    kind: PredicateKind
    value: str = ""


@dataclass(frozen=True)
class Dispute:
    claimant: Party
    claim_type: ClaimType
    subject: str
    predicate: Predicate

    def __post_init__(self) -> None:
        if self.claimant is Party.NONE:
            raise ValueError("a dispute needs a real claimant")


def build_disputes(view: EvidenceView) -> tuple[Dispute, ...]:
    """Every complaint the two parties can actually raise from what they see."""
    out: list[Dispute] = []
    p, e = view.p, view.e

    # -- principal-side complaints ------------------------------------------
    if p.disputed_action is not None:
        out.append(Dispute(Party.P, ClaimType.UNAUTHORIZED_EXECUTION,
                           p.disputed_action,
                           Predicate(PredicateKind.NOT_IN_SCOPE, p.disputed_action)))

    if not p.asserted_auth_issued:
        out.append(Dispute(Party.P, ClaimType.AUTHORIZATION_DENIED, "authorization",
                           Predicate(PredicateKind.NOT_EXISTS)))

    if not p.asserted_result_received:
        out.append(Dispute(Party.P, ClaimType.RECEIPT_DENIED, "delivery",
                           Predicate(PredicateKind.NOT_EXISTS)))

    # The principal can only challenge actions the executor ADMITTED to.
    if e.asserted_actions is not None and p.asserted_scope is not None:
        for a in e.asserted_actions:
            if a not in p.asserted_scope:
                out.append(Dispute(Party.P, ClaimType.UNAUTHORIZED_EXECUTION, a,
                                   Predicate(PredicateKind.NOT_IN_SCOPE, a)))

    if not e.record_available:
        out.append(Dispute(Party.P, ClaimType.EXECUTION_DENIED, "execution_record",
                           Predicate(PredicateKind.EXISTS)))

    # -- executor-side complaints -------------------------------------------
    if e.asserted_scope is not None and p.asserted_scope is not None:
        for a in e.asserted_scope:
            if a not in p.asserted_scope:
                out.append(Dispute(Party.E, ClaimType.SCOPE_VIOLATION, a,
                                   Predicate(PredicateKind.IN_SCOPE, a)))

    if e.asserted_auth_issued and not p.asserted_auth_issued:
        out.append(Dispute(Party.E, ClaimType.AUTHORIZATION_DENIED, "authorization",
                           Predicate(PredicateKind.EXISTS)))

    # -- structural equivocation --------------------------------------------
    if (p.asserted_scope is not None and e.asserted_scope is not None
            and sorted(p.asserted_scope) != sorted(e.asserted_scope)):
        out.append(Dispute(Party.P, ClaimType.EQUIVOCATION, "scope",
                           Predicate(PredicateKind.EXISTS)))

    # dedupe, preserve order
    seen, uniq = set(), []
    for d in out:
        k = (d.claimant, d.claim_type, d.subject, d.predicate)
        if k not in seen:
            seen.add(k)
            uniq.append(d)
    return tuple(uniq)


def subjects(disputes, claim_type: ClaimType, claimant: Party | None = None) -> tuple[str, ...]:
    return tuple(d.subject for d in disputes
                 if d.claim_type is claim_type
                 and (claimant is None or d.claimant is claimant))
