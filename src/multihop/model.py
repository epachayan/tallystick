"""Three-party model: principal, intermediary, executor.

Kept separate from src/model so the two-party corpus, its figures and every
claim resting on them are untouched (the multi-hop phase may not move a
two-party number; `make check` enforces this in src/multihop/freeze.py).

What carries over unchanged from the two-party model:

  * Outcome labels, success/failure sets and the metrics module
  * the meaning of a MISTAKEN party: it diverges from the record and is not
    culpable, so naming it is over-attribution while contradicting it is not
  * the scorer's order: world first, then the verdict

What generalises:

  * Party.BOTH becomes a set. A verdict names or contradicts a SET of parties,
    and a world has a SET of dishonest parties (collusion classes have two).
  * D(w), the parties whose account diverges from the record, is a subset of
    {P, I, E} rather than of {P, E}. With three parties two worlds can have
    different, overlapping D -- which the two-party corpus could not express.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..model.types import Outcome


class Party3(str, Enum):
    P = "P"
    I = "I"  # noqa: E741 -- the intermediary; the letter is the protocol's
    E = "E"


PARTIES = (Party3.P, Party3.I, Party3.E)


class State(str, Enum):
    HONEST = "honest"
    MISTAKEN = "mistaken"
    DISHONEST = "dishonest"


def parties(xs) -> frozenset[Party3]:
    return frozenset(Party3(x) for x in xs)


def fmt(ps) -> str:
    order = {p: i for i, p in enumerate(PARTIES)}
    return "{" + ",".join(p.value for p in sorted(ps, key=order.get)) + "}"


# ---------------------------------------------------------------------------
# Hidden truth
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Truth3:
    states: tuple[tuple[Party3, State], ...]
    adjudicable: bool = True

    @classmethod
    def from_scenario(cls, sc: dict) -> "Truth3":
        g = sc["ground_truth"]
        st = tuple((p, State(g["states"][p.value])) for p in PARTIES)
        return cls(states=st, adjudicable=bool(g.get("adjudicable", True)))

    def state(self, p: Party3) -> State:
        return dict(self.states)[p]

    @property
    def diverges(self) -> frozenset[Party3]:
        """D(w): parties whose account diverges from the record, culpably or not."""
        return frozenset(p for p, s in self.states if s is not State.HONEST)

    @property
    def mistaken(self) -> frozenset[Party3]:
        return frozenset(p for p, s in self.states if s is State.MISTAKEN)

    @property
    def dishonest(self) -> frozenset[Party3]:
        return frozenset(p for p, s in self.states if s is State.DISHONEST)


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

class Status3(str, Enum):
    CLEAR = "clear"
    SUSPECTED = "suspected"
    EXPOSED = "exposed"
    CONTRADICTED = "contradicted"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class Verdict3:
    detected: bool = False
    blamed: frozenset[Party3] = frozenset()
    contradicted: frozenset[Party3] = frozenset()
    attributes_fault: bool = True
    status: Status3 = Status3.CLEAR
    disclosed_bytes: int = 0
    queries: int = 0
    reasons: tuple[str, ...] = ()
    flags: frozenset[str] = frozenset()

    @property
    def names_a_party(self) -> bool:
        return self.attributes_fault and bool(self.blamed)

    @property
    def abstains(self) -> bool:
        return not self.names_a_party and not self.contradicted

    def key(self) -> tuple:
        """Decision-carrying fields; excludes free-text reasons."""
        return (self.detected, fmt(self.blamed), fmt(self.contradicted),
                self.attributes_fault, self.status, self.disclosed_bytes,
                self.queries, tuple(sorted(self.flags)))


# ---------------------------------------------------------------------------
# Scorer -- the two-party scorer with sets in place of Party.BOTH
# ---------------------------------------------------------------------------

def score3(truth: Truth3, v: Verdict3) -> Outcome:
    if not truth.adjudicable:
        if v.abstains:
            return Outcome.CORRECT_ABSTAIN_AMB
        if v.names_a_party:
            return Outcome.UNSUPPORTED_BLAME
        return Outcome.FALSE_CONTRADICTION

    d, mistaken, dishonest = truth.diverges, truth.mistaken, truth.dishonest

    if not d:
        if v.names_a_party:
            return Outcome.FALSE_ACCUSATION
        if v.contradicted:
            return Outcome.FALSE_CONTRADICTION
        if v.detected and v.status not in (Status3.SUSPECTED, Status3.UNRESOLVED):
            return Outcome.SPURIOUS
        return Outcome.CORRECT_ABSTAIN

    if v.names_a_party:
        if v.blamed & mistaken:
            return Outcome.OVER_ATTRIBUTION
        # Exact: naming a subset of the colluders, or a superset of the guilty
        # party, is wrong. Same as the two-party rule for Party.BOTH.
        return Outcome.CORRECT_BLAME if v.blamed == dishonest else Outcome.FALSE_ACCUSATION

    if v.contradicted:
        return (Outcome.CORRECT_CONTRADICTION if v.contradicted <= d
                else Outcome.FALSE_CONTRADICTION)

    if d <= mistaken and not dishonest:
        return Outcome.CORRECT_ABSTAIN
    return Outcome.MISSED


def correct_in(truth: Truth3, v: Verdict3) -> bool:
    from ..model.types import SUCCESS_OUTCOMES
    return score3(truth, v) in SUCCESS_OUTCOMES


def localised(truth: Truth3, v: Verdict3) -> bool:
    """Stronger than correct: the verdict names EVERY diverging party.

    Correctness accepts any non-empty subset of D, which is right for a claim
    about the record -- each named contradiction is true. It is not the same as
    telling a principal where the fault in its chain lies. RQ2 is about this.
    """
    named = v.contradicted or (v.blamed if v.attributes_fault else frozenset())
    return bool(truth.diverges) and named == truth.diverges and correct_in(truth, v)
