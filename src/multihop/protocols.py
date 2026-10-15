"""Three-party adjudication protocols.

Every protocol here is a pair: an interaction-protocol SPECIFICATION (which
messages are signed, what they bind, who ends up holding what) and an
ADJUDICATOR (what it concludes from the copies produced). Keeping the two
apart is the point of the design:

    B13_hop and B13_chain run the SAME adjudicator over different
    specifications. Any difference between them is caused by what the
    protocol carries, not by how the evidence is read.

Registered protocols:

    B0_bearer3     bearer3   no counterparty signatures; suspicion only
    B1_hop3        hop3      per-hop bilateral, full disclosure, attributive;
                             treats non-production as guilt (the naive scheme)
    B13_hop3       hop3      witness recomputation, commitment-only,
                             non-attributive; the intermediary re-signs
    B13_chain3     chain3    the same adjudicator; the intermediary forwards
    B17_chain3     chain3    B13_chain3 plus a duty to answer, attached to
                             every party, including one outside the dispute

Inputs are the View3 and an Oracle3; nothing else. Ground truth never reaches
this module (src/multihop/conformance.py mutates it to check).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..protocols.baselines import ROOT_BYTES, SIG_BYTES
from .evidence import Disclosure, Oracle3, View3, recompute
from .model import Party3, Status3, Verdict3
from .spec import Spec, load


@dataclass(frozen=True)
class Protocol3:
    name: str
    spec_name: str
    disclosure: Disclosure
    fn: Callable[[View3, Oracle3], Verdict3]

    @property
    def spec(self) -> Spec:
        return load(self.spec_name)


PROTOCOLS3: dict[str, Protocol3] = {}


def register(name, spec_name, disclosure):
    def deco(fn):
        PROTOCOLS3[name] = Protocol3(name, spec_name, disclosure, fn)
        return fn
    return deco


def _P(xs) -> frozenset[Party3]:
    return frozenset(Party3(x) for x in xs)


# ---------------------------------------------------------------------------
# The shared reading of the evidence
# ---------------------------------------------------------------------------

@dataclass
class Findings:
    against: dict[str, list[str]]
    flags: set[str]

    def add(self, party: str, why: str, flag: str | None = None):
        self.against.setdefault(party, []).append(why)
        if flag:
            self.flags.add(flag)

    @property
    def parties(self) -> frozenset[str]:
        return frozenset(self.against)

    @property
    def reasons(self) -> tuple[str, ...]:
        return tuple(f"{p}: {w}" for p in sorted(self.against) for w in self.against[p])


def _member(view: View3, oracle: Oracle3, root: str, obj: str, value: str) -> bool | None:
    """Membership of a named value in a produced root. Under full disclosure
    the adjudicator reads the contents it was sent; otherwise it asks for a
    proof and verifies it."""
    if view.disclosure is Disclosure.FULL:
        for c in view.copies:
            b = c.binding(obj)
            if b is not None and b.root == root and b.contents is not None:
                return value in b.contents
        return None
    return oracle.member(root, value)


def read_evidence(view: View3, oracle: Oracle3) -> Findings:
    f = Findings({}, set())

    # 1. equivocation: one signer, two roots for the same object --------------
    for obj in ("G", "S", "X", "R"):
        for root_a, signers_a in view.roots(obj).items():
            for root_b, signers_b in view.roots(obj).items():
                if root_a < root_b:
                    for s in sorted(signers_a & signers_b):
                        f.add(s, f"signed two different versions of {obj}", "equivocation")

    # 2. recomputation: each party's assertion against what was signed ---------
    checks = {"P": ("G",), "I": ("G", "S", "X"), "E": ("S", "X")}
    for party, objs in checks.items():
        cl = view.claim(party)
        for obj in objs:
            asserted = cl.get(obj)
            roots = view.roots(obj)
            if asserted is None or not roots:
                continue
            if recompute(asserted) not in roots:
                f.add(party, f"asserted {obj} does not recompute to any signed root",
                      "root_recomputation")
        # I's account of the execution must also match what I itself reported.
        if party == "I" and cl.X is not None and view.roots("R"):
            if recompute(cl.X) not in view.roots("R"):
                f.add("I", "asserted execution does not recompute to its own report",
                      "root_recomputation")

    # 3. the named complaint: where in the chain does the action fall? -----------
    d = view.disputed
    if d is not None:
        def single(obj):
            rs = view.roots(obj)
            return next(iter(rs)) if len(rs) == 1 else None

        g, s, x = single("G"), single("S"), single("X")
        in_g = _member(view, oracle, g, "G", d) if g else None
        in_s = _member(view, oracle, s, "S", d) if s else None
        in_x = _member(view, oracle, x, "X", d) if x else None

        if in_x is True and in_s is False:
            f.add("E", f"executed '{d}', which is outside the committed sub-grant",
                  "overreach")
        if in_s is True and in_g is False:
            f.add("I", f"sub-delegated '{d}', which is outside the committed grant",
                  "widening")
        if in_g is True:
            # the two-party baseless-complaint test, unchanged
            f.add("P", f"baseless complaint: '{d}' IS in the committed grant",
                  "baseless_complaint")
    return f


def _witness_bytes(view: View3) -> int:
    return sum(SIG_BYTES + ROOT_BYTES * len(c.bindings) for c in view.copies)


def _full_bytes(view: View3) -> int:
    total = 0
    for c in view.copies:
        total += SIG_BYTES
        for b in c.bindings:
            total += sum(len(v.encode()) for v in (b.contents or ()))
    return total


# ---------------------------------------------------------------------------
# B0 -- bearer tokens and self-written logs
# ---------------------------------------------------------------------------

@register("B0_bearer3", "bearer3", Disclosure.FULL)
def b0_bearer3(view, oracle):
    claims = dict(view.claims)
    disagree = any(
        len({claims[p].get(o) for p in ("P", "I", "E") if claims[p].get(o) is not None}) > 1
        for o in ("G", "S", "X"))
    conflict = disagree or view.disputed is not None or bool(view.silent)
    disclosed = sum(len(v.encode()) for _p, c in view.claims
                    for o in ("G", "S", "X") for v in (c.get(o) or ()))
    return Verdict3(detected=conflict, attributes_fault=True,
                    status=Status3.SUSPECTED if conflict else Status3.CLEAR,
                    disclosed_bytes=disclosed,
                    reasons=("divergence visible; no party is bound by a prior statement",)
                    if conflict else ())


# ---------------------------------------------------------------------------
# B1 -- per-hop bilateral commitment, attributive, full disclosure
# ---------------------------------------------------------------------------

@register("B1_hop3", "hop3", Disclosure.FULL)
def b1_hop3(view, oracle):
    f = read_evidence(view, oracle)
    # The naive scheme: a party that produces nothing is presumed guilty. It
    # cannot tell loss, unreachability or a party outside the dispute from
    # concealment -- the two-party B1's defect, now with one more party to hit.
    for p in sorted(view.silent):
        f.add(p, "produced no record", "non_production")
    blamed = _P(f.parties)
    return Verdict3(detected=bool(blamed), blamed=blamed, attributes_fault=True,
                    status=Status3.EXPOSED if blamed else Status3.CLEAR,
                    disclosed_bytes=_full_bytes(view), reasons=f.reasons,
                    flags=frozenset(f.flags))


# ---------------------------------------------------------------------------
# B13 -- witness recomputation; one adjudicator, two specifications
# ---------------------------------------------------------------------------

def _b13(view, oracle):
    f = read_evidence(view, oracle)
    c = _P(f.parties)
    return Verdict3(detected=bool(c), contradicted=c, attributes_fault=False,
                    status=Status3.CONTRADICTED if c else Status3.CLEAR,
                    disclosed_bytes=_witness_bytes(view) + oracle.ledger.bytes_disclosed,
                    queries=oracle.ledger.queries, reasons=f.reasons,
                    flags=frozenset(f.flags))


@register("B13_hop3", "hop3", Disclosure.COMMITMENT_ONLY)
def b13_hop3(view, oracle):
    return _b13(view, oracle)


@register("B13_chain3", "chain3", Disclosure.COMMITMENT_ONLY)
def b13_chain3(view, oracle):
    return _b13(view, oracle)


# ---------------------------------------------------------------------------
# B17 -- B13_chain3 plus a duty to answer
#
# The two-party duty: a party that signed a commitment the counterparty holds
# must answer for it. Extended here without modification to three parties,
# which is exactly what makes it worth measuring: the executor is not a party
# to P's dispute with I, and may simply be unreachable.
# ---------------------------------------------------------------------------

@register("B17_chain3", "chain3", Disclosure.COMMITMENT_ONLY)
def b17_chain3(view, oracle):
    f = read_evidence(view, oracle)

    # (a) silence: a party that produced nothing but whose signature over a
    #     commitment is in evidence
    for p in sorted(view.silent):
        if view.signed_by(p):
            f.add(p, "failed to answer for a commitment it signed", "duty_breach")

    # (b) a missing copy: a message is shown to exist (someone produced a
    #     copy), its direct receiver produced a record, but not that message
    spec = load(view.spec)
    produced = {c.id for c in view.copies}
    for m in spec.messages:
        if not m.signed:
            continue
        exists = any(c.message == m.name for c in view.copies)
        mine = f"{m.name}@{m.receiver}"
        if exists and mine not in produced and m.receiver not in view.silent:
            f.add(m.receiver, f"did not produce '{m.name}', which is shown to exist",
                  "duty_breach")

    c = _P(f.parties)
    return Verdict3(detected=bool(c), contradicted=c, attributes_fault=False,
                    status=Status3.CONTRADICTED if c else Status3.CLEAR,
                    disclosed_bytes=_witness_bytes(view) + oracle.ledger.bytes_disclosed,
                    queries=oracle.ledger.queries, reasons=f.reasons,
                    flags=frozenset(f.flags))
