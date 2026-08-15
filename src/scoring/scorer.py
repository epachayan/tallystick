"""Canonical scorer (P0-2).

Classifies the WORLD first, then evaluates the verdict. The v0.9 scorer branched
on the verdict's VOCABULARY first -- `if verdict.get("attributes_fault") is False`
was the opening test -- so the style of the mechanism decided the label before
adjudicability was ever considered. That is what produced `missed` for
non-attributive mechanisms in unadjudicable worlds, and `correct_contradiction`
from `sorted([]) == sorted([])` in honest ones.

Order (fixed; changing it must be a recorded decision):

    1. unadjudicable world
    2. no-divergence world
    3. verdict attributes fault
    4. verdict asserts contradiction
    5. otherwise MISSED

The distinctive Tallystick semantics are preserved: a MISTAKEN party diverges
from the record but is not culpable, so naming it is `over_attribution`, not
`correct_blame`. That distinction is the project's own finding and it survives
the reordering intact.
"""

from __future__ import annotations

from ..model.types import GroundTruth, Outcome, Party, Verdict, VerdictStatus


def score(truth: GroundTruth, verdict: Verdict) -> Outcome:
    # -- 1. nothing could settle it -----------------------------------------
    if not truth.adjudicable:
        if verdict.abstains:
            return Outcome.CORRECT_ABSTAIN_AMB
        if verdict.names_a_party:
            return Outcome.UNSUPPORTED_BLAME
        return Outcome.FALSE_CONTRADICTION

    diverges = set(truth.diverges)
    mistaken = set(truth.mistaken)

    # -- 2. honest world, nothing diverged ----------------------------------
    if not diverges:
        if verdict.names_a_party:
            return Outcome.FALSE_ACCUSATION
        if verdict.contradicted:
            # P7: an empty divergence set can never yield correct_contradiction.
            return Outcome.FALSE_CONTRADICTION
        # A withdrawable suspicion names no wrongdoer; only an unexplained hard
        # flag is spurious.
        if verdict.detected and verdict.status not in (
            VerdictStatus.SUSPECTED, VerdictStatus.UNRESOLVED, VerdictStatus.EVIDENCE_VOIDED
        ):
            return Outcome.SPURIOUS
        return Outcome.CORRECT_ABSTAIN

    # -- 3. attribution: the stronger act, judged first ----------------------
    if verdict.names_a_party:
        named = _named(verdict.blamed)
        if named & mistaken:
            # Blamed someone who diverged by mistake. The evidence supports
            # "your account contradicts the record"; it does not support "you
            # lied". This is the project's own T4 boundary.
            return Outcome.OVER_ATTRIBUTION
        if truth.dishonest_party is Party.BOTH:
            return (Outcome.CORRECT_BLAME if verdict.blamed is Party.BOTH
                    else Outcome.FALSE_ACCUSATION)
        if verdict.blamed is Party.BOTH:
            # Named the guilty party but smeared the other one too.
            return Outcome.FALSE_ACCUSATION
        return (Outcome.CORRECT_BLAME if verdict.blamed is truth.dishonest_party
                else Outcome.FALSE_ACCUSATION)

    # -- 4. non-attributive resolution --------------------------------------
    if verdict.contradicted:
        claimed = set(verdict.contradicted)
        if claimed <= diverges:
            # Naming a contradiction is a claim about the RECORD, so pointing at
            # a mistaken party is correct here where blaming it would not be.
            return Outcome.CORRECT_CONTRADICTION
        return Outcome.FALSE_CONTRADICTION

    # -- 5. resolvable, unresolved ------------------------------------------
    if diverges <= mistaken and truth.dishonest_party is Party.NONE:
        # Everyone who diverged did so by mistake and nobody was dishonest;
        # abstaining from blame is the right answer, not a miss.
        return Outcome.CORRECT_ABSTAIN
    return Outcome.MISSED


def _named(blamed: Party) -> set[Party]:
    if blamed is Party.BOTH:
        return {Party.P, Party.E}
    if blamed is Party.NONE:
        return set()
    return {blamed}


def explain(truth: GroundTruth, verdict: Verdict) -> str:
    reasons = {
        Outcome.CORRECT_ABSTAIN_AMB: "unadjudicable world; abstained",
        Outcome.UNSUPPORTED_BLAME: "unadjudicable world; named a party anyway",
        Outcome.FALSE_CONTRADICTION: "asserted a contradiction ground truth does not support",
        Outcome.CORRECT_ABSTAIN: "no culpable divergence; withheld blame",
        Outcome.SPURIOUS: "hard flag with nothing to settle",
        Outcome.FALSE_ACCUSATION: "named a party who is not the dishonest one",
        Outcome.OVER_ATTRIBUTION: "named a party that was mistaken, not dishonest",
        Outcome.CORRECT_BLAME: "named the dishonest party",
        Outcome.CORRECT_CONTRADICTION: "proved divergence without attributing fault",
        Outcome.MISSED: "adjudicable misconduct left unresolved",
    }
    o = score(truth, verdict)
    return f"{o.value}: {reasons[o]}"
