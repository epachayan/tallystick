"""Evidence projection for the three-party chain.

scenario + specification -> what an adjudicator can see.

The rule is the two-party rule, generalised over copies:

  * a signed message exists only if it was sent, and only as the
    specification says (signed, binding these objects, held by its receiver
    and by anyone it was forwarded to)
  * a copy reaches the adjudicator only if its holder produces it -- an
    unavailable party produces nothing, a withholding party drops that copy
  * what a copy carries is a commitment root per bound object (and the
    contents, under full disclosure). Colluders can re-sign what they alone
    signed and hold; they cannot alter a copy an honest party holds
  * each party's own assertions are always visible: they ARE the dispute
  * which parties produced nothing is visible; WHY is not

Ground truth, party states, the true sets and the fabrication metadata never
reach a protocol. src/multihop/conformance.py mutates each of them and checks
that no verdict moves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..crypto.merkle import (
    MembershipProof,
    MerkleError,
    MerkleSet,
    NonMembershipProof,
    build_root,
    encoded_size,
    verify_membership,
    verify_non_membership,
)
from .spec import Copy, Spec, holdings


class Disclosure(str, Enum):
    FULL = "full"
    COMMITMENT_ONLY = "commitment_only"


@dataclass(frozen=True)
class Binding:
    obj: str
    root: str
    cardinality: int
    contents: tuple[str, ...] | None      # FULL only


@dataclass(frozen=True)
class SeenCopy:
    """A copy as the adjudicator receives it."""
    message: str
    signer: str
    holder: str
    forwarded: bool
    bindings: tuple[Binding, ...]

    @property
    def id(self) -> str:
        return f"{self.message}@{self.holder}"

    def binding(self, obj: str) -> Binding | None:
        for b in self.bindings:
            if b.obj == obj:
                return b
        return None


@dataclass(frozen=True)
class Claims:
    G: tuple[str, ...] | None = None
    S: tuple[str, ...] | None = None
    X: tuple[str, ...] | None = None
    report_received: bool | None = None

    def get(self, obj: str):
        return getattr(self, obj, None)


@dataclass(frozen=True)
class View3:
    spec: str
    disclosure: Disclosure
    copies: tuple[SeenCopy, ...]
    claims: tuple[tuple[str, Claims], ...]
    silent: frozenset[str]                # produced nothing at all
    disputed: str | None                  # the action P names

    def claim(self, party: str) -> Claims:
        return dict(self.claims)[party]

    def roots(self, obj: str) -> dict[str, set[str]]:
        """root -> signers who put their signature over it, across produced copies."""
        out: dict[str, set[str]] = {}
        for c in self.copies:
            b = c.binding(obj)
            if b is not None:
                out.setdefault(b.root, set()).add(c.signer)
        return out

    def signed_by(self, party: str) -> tuple[SeenCopy, ...]:
        return tuple(c for c in self.copies if c.signer == party)

    def fingerprint(self) -> str:
        """Observable equality. Roots are opaque to the adjudicator except as
        equal-or-not, so they are relabelled by first appearance -- two worlds
        whose copies carry different-but-consistent roots look the same."""
        import hashlib
        import json

        labels: dict[str, str] = {}

        def lab(r):
            return labels.setdefault(r, f"r{len(labels)}")

        d = {
            "spec": self.spec,
            "copies": sorted(
                (c.id, c.signer, c.forwarded,
                 tuple((b.obj, lab(b.root), b.cardinality, b.contents) for b in c.bindings))
                for c in sorted(self.copies, key=lambda c: c.id)),
            "claims": [(p, c.G, c.S, c.X, c.report_received) for p, c in self.claims],
            "silent": sorted(self.silent),
            "disputed": self.disputed,
        }
        return hashlib.sha256(json.dumps(d, default=list).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Prover side
# ---------------------------------------------------------------------------

@dataclass
class Ledger3:
    queries: int = 0
    bytes_disclosed: int = 0
    facts: list[str] = field(default_factory=list)


class Oracle3:
    """Answers membership questions about a NAMED value against each produced
    root of an object, with real proofs. Cannot enumerate a set."""

    def __init__(self, sets: dict[str, MerkleSet]):
        self._sets = sets            # root -> prover-side set
        self.ledger = Ledger3()

    def member(self, root: str, value: str) -> bool | None:
        tree = self._sets.get(root)
        self.ledger.queries += 1
        if tree is None:
            return None
        if value in tree.items:
            proof = tree.prove_membership(value)
            ok = verify_membership(root, value, proof)
            result = True if ok else None
        else:
            proof = tree.prove_non_membership(value)
            ok = verify_non_membership(root, value, proof)
            result = False if ok else None
        self.ledger.bytes_disclosed += encoded_size(proof)
        self.ledger.facts.append(f"{root[:8]}:{value}")
        return result


def _root(values) -> str:
    try:
        return build_root(list(values))
    except MerkleError:
        return "<unformable>"


def recompute(values) -> str | None:
    return None if values is None else _root(values)


# ---------------------------------------------------------------------------
# The projection
# ---------------------------------------------------------------------------

def _contents(sc: dict, copy: Copy, obj: str) -> list[str]:
    """What this copy carries for `obj`: the original, or the colluders'
    re-signed version where they could have swapped it."""
    fab = sc.get("fabrication")
    if fab and obj in fab["objects"]:
        by = set(fab["by"])
        if fab["before_report"]:
            # The original never left the colluders, so every party -- honest
            # ones included -- only ever saw and signed the cover version. (The
            # first version of this rule fabricated only colluder-signed copies,
            # and left P's report_ack over a report P never received. The twin
            # audit caught it: H6/H7 failed to derive as twins under hop3.)
            return list(fab["objects"][obj])
        if copy.signer in by and copy.holder in by:
            # After the fact, colluders can re-sign only what they alone signed
            # and hold. A copy an honest party holds keeps the original.
            return list(fab["objects"][obj])
    return list(sc["objects"][obj])


def produced_copies(spec: Spec, sc: dict) -> tuple[Copy, ...]:
    unavailable = set(sc.get("unavailable", ()))
    withheld = sc.get("withheld", {})
    out = []
    for c in holdings(spec, sc["sent"]):
        if c.holder in unavailable:
            continue
        if c.message in withheld.get(c.holder, ()):
            continue
        out.append(c)
    return tuple(out)


def build_view(spec: Spec, sc: dict, disclosure: Disclosure) -> tuple[View3, Oracle3]:
    sets: dict[str, MerkleSet] = {}
    seen: list[SeenCopy] = []
    for c in produced_copies(spec, sc):
        bindings = []
        for obj in c.binds:
            vals = _contents(sc, c, obj)
            ms = MerkleSet(vals)
            sets.setdefault(ms.root, ms)
            bindings.append(Binding(
                obj, ms.root, ms.n,
                tuple(ms.items) if disclosure is Disclosure.FULL else None))
        seen.append(SeenCopy(c.message, c.signer, c.holder, c.forwarded, tuple(bindings)))

    def _t(x):
        return tuple(x) if x is not None else None

    claims = []
    for p in ("P", "I", "E"):
        raw = sc["claims"].get(p, {})
        claims.append((p, Claims(G=_t(raw.get("G")), S=_t(raw.get("S")), X=_t(raw.get("X")),
                                 report_received=raw.get("report_received"))))

    view = View3(
        spec=spec.name,
        disclosure=disclosure,
        copies=tuple(sorted(seen, key=lambda c: c.id)),
        claims=tuple(claims),
        silent=frozenset(sc.get("unavailable", ())),
        disputed=sc.get("disputed"),
    )
    return view, Oracle3(sets)


#: scenario fields that must never reach a protocol. (`fabrication` is world
#: mechanics: it decides what a copy CONTAINS, so changing it legitimately
#: changes the evidence. It is not on this list for that reason.)
HIDDEN_FIELDS = (
    "ground_truth.states",
    "ground_truth.actual",
    "ground_truth.claim",
    "ground_truth.adjudicable",
    "h_class",
    "family",
)
