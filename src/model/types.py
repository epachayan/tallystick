"""Tallystick core model types.

Four concepts, separated so a protocol cannot reach hidden state (P0-1):

    Scenario      -- the generated corpus row (a dict; the only place with everything)
    GroundTruth   -- hidden reality; reaches the SCORER and nothing else
    EvidenceView  -- what a given protocol's adjudicator can actually see
    Dispute       -- what is being contested; supplied, never inferred from truth
    Verdict       -- the protocol's output

Party vocabulary is the repo's: P (principal), E (executor), J (adjudicator),
both, none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Party(str, Enum):
    P = "P"
    E = "E"
    J = "J"
    BOTH = "both"
    NONE = "none"


class PartyState(str, Enum):
    HONEST = "honest"
    MISTAKEN = "mistaken"       # diverges from the record, not culpable
    DISHONEST = "dishonest"


# ---------------------------------------------------------------------------
# Hidden truth
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GroundTruth:
    dishonest_party: Party = Party.NONE
    p_state: PartyState = PartyState.HONEST
    e_state: PartyState = PartyState.HONEST
    adjudicable: bool = True
    claim: str = ""

    @classmethod
    def from_scenario(cls, sc: dict) -> "GroundTruth":
        g = sc["ground_truth"]
        return cls(
            dishonest_party=Party(g.get("dishonest_party", "none")),
            p_state=PartyState(g.get("p_state", "honest")),
            e_state=PartyState(g.get("e_state", "honest")),
            adjudicable=bool(g.get("adjudicable", True)),
            claim=g.get("claim", ""),
        )

    @property
    def diverges(self) -> tuple[Party, ...]:
        """Parties whose account diverges from the record, culpably or not.
        This is what a non-attributive verdict is scored against."""
        out = []
        if self.p_state in (PartyState.MISTAKEN, PartyState.DISHONEST):
            out.append(Party.P)
        if self.e_state in (PartyState.MISTAKEN, PartyState.DISHONEST):
            out.append(Party.E)
        if self.dishonest_party is Party.J:
            out.append(Party.J)
        return tuple(out)

    @property
    def mistaken(self) -> tuple[Party, ...]:
        out = []
        if self.p_state is PartyState.MISTAKEN:
            out.append(Party.P)
        if self.e_state is PartyState.MISTAKEN:
            out.append(Party.E)
        return tuple(out)


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

class VerdictStatus(str, Enum):
    CLEAR = "clear"
    SUSPECTED = "suspected"          # withdrawable; not blame
    EXPOSED = "exposed"              # attributive
    CONTRADICTED = "contradicted"    # non-attributive
    UNRESOLVED = "unresolved"
    EVIDENCE_VOIDED = "evidence_voided"


@dataclass(frozen=True)
class Verdict:
    detected: bool = False
    blamed: Party = Party.NONE
    contradicted: tuple[Party, ...] = ()
    attributes_fault: bool = True
    status: VerdictStatus = VerdictStatus.CLEAR
    disclosed_bytes: int = 0
    disclosed_facts: tuple[str, ...] = ()
    queries: int = 0
    reasons: tuple[str, ...] = ()
    flags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.contradicted, tuple):
            raise TypeError("Verdict.contradicted must be a tuple")

    @property
    def names_a_party(self) -> bool:
        return self.attributes_fault and self.blamed is not Party.NONE

    @property
    def abstains(self) -> bool:
        return not self.names_a_party and not self.contradicted

    def key(self) -> tuple:
        """Comparison key for the visibility invariant. Deliberately EXCLUDES
        `reasons` (free text) but includes everything that carries a decision."""
        return (
            self.detected,
            self.blamed,
            tuple(sorted(self.contradicted)),
            self.attributes_fault,
            self.status,
            self.disclosed_bytes,
            self.queries,
            tuple(sorted(self.flags)),
        )


# ---------------------------------------------------------------------------
# Outcome labels
# ---------------------------------------------------------------------------

class Outcome(str, Enum):
    CORRECT_BLAME = "correct_blame"
    CORRECT_CONTRADICTION = "correct_contradiction"
    CORRECT_ABSTAIN = "correct_abstain"
    CORRECT_ABSTAIN_AMB = "correct_abstain_amb"
    MISSED = "missed"
    FALSE_ACCUSATION = "false_accusation"
    OVER_ATTRIBUTION = "over_attribution"      # named a MISTAKEN party as culpable
    SPURIOUS = "spurious"                      # hard flag with nothing to settle
    UNSUPPORTED_BLAME = "unsupported_blame"    # named a party in an unadjudicable world
    FALSE_CONTRADICTION = "false_contradiction"


OUTCOMES = tuple(o.value for o in Outcome)

SUCCESS_OUTCOMES = frozenset({
    Outcome.CORRECT_BLAME,
    Outcome.CORRECT_CONTRADICTION,
    Outcome.CORRECT_ABSTAIN,
    Outcome.CORRECT_ABSTAIN_AMB,
})

#: named or implicated a party the evidence does not support
FALSE_ATTRIBUTION_OUTCOMES = frozenset({
    Outcome.FALSE_ACCUSATION,
    Outcome.OVER_ATTRIBUTION,
    Outcome.UNSUPPORTED_BLAME,
})

FAILURE_OUTCOMES = frozenset(Outcome) - SUCCESS_OUTCOMES
