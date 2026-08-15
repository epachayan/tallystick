"""Evidence projection: scenario -> what a protocol's adjudicator can see.

This is the structural fix for P0-1. A protocol never receives a scenario. It
receives an EvidenceView, which is frozen, and (under commitment-only policies)
a ProofOracle, which answers queries about NAMED values and returns real proofs
the protocol must verify. Neither carries ground truth, party states, intent,
`adjudicator.colluding`, or `key_claim.genuine`.

Two disclosure policies, because the findings are right that one view cannot
serve both families:

    FULL              contents of the committed artifacts reach the adjudicator
    COMMITMENT_ONLY   only roots and cardinalities; contents by query and proof

Availability still gates everything (A3): a record that cannot be produced
yields neither its contents nor its integrity status. What SURVIVES
non-production is the commitment made earlier -- its root and, because the root
binds it, its cardinality.

The adjudicator's own honesty is not visible. What IS visible is the verdict it
published. A protocol that wants to catch a corrupt adjudicator must recompute
from the transcript and compare, which is what B7 now does instead of reading
`adjudicator.colluding`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..crypto.merkle import (
    MerkleSet,
    NonMembershipProof,
    MembershipProof,
    encoded_size,
    verify_membership,
    verify_non_membership,
)
from .types import Party


class DisclosurePolicy(str, Enum):
    FULL = "full"
    COMMITMENT_ONLY = "commitment_only"


#: What a protocol is allowed to see beyond the base view. Every widening is a
#: trust assumption and must be declared here, not taken silently.
ENTITLEMENTS: dict[str, frozenset[str]] = {
    "B11_stateful": frozenset({"history"}),
    "B16c_custodial_attestor": frozenset({"custodial_copy"}),
}


@dataclass(frozen=True)
class PartyClaims:
    """What a party asserts. Its own claims are always visible -- that is what
    a dispute consists of."""
    asserted_scope: tuple[str, ...] | None
    asserted_actions: tuple[str, ...] | None
    asserted_auth_issued: bool
    asserted_result_received: bool
    record_available: bool
    record_intact: bool | None      # None when unproduced: unobservable
    disputed_action: str | None = None


@dataclass(frozen=True)
class EvidenceView:
    # --- authorization -----------------------------------------------------
    auth_committed: bool
    auth_exists: bool
    scope_root: str | None
    scope_cardinality: int | None
    committed_scope: tuple[str, ...] | None       # FULL policy only

    # --- execution ---------------------------------------------------------
    exec_root: str | None
    exec_cardinality: int | None
    exec_record_produced: bool
    committed_actions: tuple[str, ...] | None     # FULL policy, produced only
    delivery_ack_exists: bool

    # --- party claims ------------------------------------------------------
    p: PartyClaims
    e: PartyClaims

    # --- ambient -----------------------------------------------------------
    key_revocation_claimed: bool
    attestor_present: bool
    attestor_available: bool
    adjudicator_published_blame: Party | None

    # --- entitlement-gated -------------------------------------------------
    history: tuple[tuple[str, int], ...] | None = None
    custodial_actions: tuple[str, ...] | None = None

    # --- witness-carrying message chain (B13) ------------------------------
    #: E's signed acknowledgement of the authorization commitment, held by P.
    auth_receipt_held: bool = False
    #: E's signed execution receipt carrying the execution commitment, held by P.
    exec_receipt_held: bool = False

    policy: DisclosurePolicy = DisclosurePolicy.FULL
    #: Cardinality every committed set was padded to, or None. Carried so a
    #: protocol recomputing a root from a party's assertion pads it the same way.
    pad_to: int | None = None

    def fingerprint(self) -> str:
        """Exact equality of the projected view."""
        return hashlib.sha256(
            json.dumps(_jsonable(self), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def observable_fingerprint(self) -> str:
        """Equality up to OPAQUE values.

        Two indistinguishable worlds have different commitment roots -- a root is
        a hash of different contents. The adjudicator sees a root in both and
        cannot tell which world it is in, so comparing raw roots overstates
        distinguishability. This redacts them and keeps everything the
        adjudicator can actually read off, cardinality included.
        """
        d = _jsonable(self)
        for k in ("scope_root", "exec_root"):
            if d.get(k) is not None:
                d[k] = "<opaque>"
        return hashlib.sha256(
            json.dumps(d, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, EvidenceView):
        return {k: _jsonable(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, PartyClaims):
        return {k: _jsonable(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, (tuple, list)):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, Enum):
        return obj.value
    return obj


# ---------------------------------------------------------------------------
# The prover side
# ---------------------------------------------------------------------------

@dataclass
class QueryLedger:
    queries: int = 0
    bytes_disclosed: int = 0
    facts: list[str] = field(default_factory=list)


PAD_PREFIX = "~pad:"


def pad_set(items, pad_to):
    """Pad a committed set to a fixed cardinality with unique filler.

    Sorted-leaf non-membership requires an authenticated leaf count, so a plain
    commitment publishes |set| to every verifier. Padding to a fixed size makes
    the count carry no information -- at the cost of a deeper tree, hence larger
    proofs. That trade is the point: it is measurable.
    """
    if pad_to is None or items is None:
        return items
    real = list(items)
    if len(real) > pad_to:
        raise ValueError(f"set of {len(real)} exceeds pad_to={pad_to}")
    return real + [f"{PAD_PREFIX}{i:04d}" for i in range(pad_to - len(real))]


class ProofOracle:
    """Answers membership questions about NAMED values, with real proofs.

    A protocol cannot enumerate a committed set through this object: it can only
    ask about values it can already name (a party's assertion, or the action a
    complainant explicitly disputed). That is the honest version of what the
    v0.9 baselines did by reading `authorization["scope"]` directly.

    Every answer is charged. Charging happens here rather than in the protocol
    so that disclosure reflects evidence actually transmitted (finding 11.2).
    """

    def __init__(self, scope_items, exec_items, exec_producible: bool = True):
        self._scope = MerkleSet(scope_items) if scope_items is not None else None
        self._exec = MerkleSet(exec_items) if exec_items is not None else None
        self._exec_producible = exec_producible
        self.ledger = QueryLedger()

    # -- roots and cardinalities are public once a commitment is made --------
    @property
    def scope_root(self):
        return self._scope.root if self._scope is not None else None

    @property
    def exec_root(self):
        return self._exec.root if self._exec is not None else None

    @property
    def scope_cardinality(self):
        return self._scope.n if self._scope is not None else None

    @property
    def exec_cardinality(self):
        return self._exec.n if self._exec is not None else None

    # -- queries -------------------------------------------------------------
    def query_scope(self, value: str):
        return self._query(self._scope, value, "scope")

    def query_exec(self, value: str):
        if not self._exec_producible:
            # The executor cannot produce a proof over a record it will not
            # produce. Non-production is not a proof of anything.
            self.ledger.queries += 1
            return None
        return self._query(self._exec, value, "exec")

    def _query(self, tree, value, label):
        if tree is None:
            self.ledger.queries += 1
            return None
        self.ledger.queries += 1
        proof = (tree.prove_membership(value) if value in tree.items
                 else tree.prove_non_membership(value))
        self.ledger.bytes_disclosed += encoded_size(proof)
        self.ledger.facts.append(f"{label}:{value}")
        return proof


def check_scope_membership(view: EvidenceView, oracle: ProofOracle, value: str):
    """Ask, then VERIFY. Returns True / False / None (no answer available).

    A protocol must branch only on this function's output -- never on a true
    set. This is finding P0-4's `if verify_non_membership(...)` in place of
    `if action not in true_scope`.
    """
    proof = oracle.query_scope(value)
    if proof is None or view.scope_root is None:
        return None
    if isinstance(proof, MembershipProof):
        return True if verify_membership(view.scope_root, value, proof) else None
    if isinstance(proof, NonMembershipProof):
        return False if verify_non_membership(view.scope_root, value, proof) else None
    return None


def check_exec_membership(view: EvidenceView, oracle: ProofOracle, value: str):
    proof = oracle.query_exec(value)
    if proof is None or view.exec_root is None:
        return None
    if isinstance(proof, MembershipProof):
        return True if verify_membership(view.exec_root, value, proof) else None
    if isinstance(proof, NonMembershipProof):
        return False if verify_non_membership(view.exec_root, value, proof) else None
    return None


# ---------------------------------------------------------------------------
# The projection
# ---------------------------------------------------------------------------

def _claims(raw: dict, produced_key: str = "record_available") -> PartyClaims:
    available = bool(raw.get(produced_key, True))
    scope = raw.get("asserted_scope")
    actions = raw.get("asserted_actions")
    return PartyClaims(
        asserted_scope=tuple(scope) if scope is not None else None,
        asserted_actions=tuple(actions) if actions is not None else None,
        asserted_auth_issued=bool(raw.get("asserted_auth_issued", True)),
        asserted_result_received=bool(raw.get("asserted_result_received", True)),
        record_available=available,
        # A3: availability gates integrity. An unproduced record's integrity is
        # unobservable, so it is None, not False.
        record_intact=(bool(raw.get("record_intact", True)) if available else None),
        disputed_action=raw.get("disputed_action"),
    )


def build_view(
    sc: dict,
    policy: DisclosurePolicy = DisclosurePolicy.FULL,
    entitlements: frozenset[str] = frozenset(),
    pad_to: int | None = None,
) -> tuple[EvidenceView, ProofOracle]:
    auth = sc["authorization"]
    execu = sc["execution"]
    chain = sc.get("chain", {})
    committed = bool(auth.get("committed", True))
    issued = bool(auth.get("issued", True))

    e_claims = _claims(sc["e_view"])
    p_claims = _claims(sc["p_view"])
    produced = e_claims.record_available or ("custodial_copy" in entitlements)
    # A3 applies symmetrically. _claims() already returns record_intact=None for
    # an unproduced record, so a principal that withholds is exactly as opaque
    # about its own integrity as an executor that withholds (RC-H9).

    scope_items = list(auth.get("scope", [])) if (committed and issued) else None
    exec_items = list(execu.get("actions", [])) if committed else None
    oracle = ProofOracle(pad_set(scope_items, pad_to), pad_set(exec_items, pad_to),
                         exec_producible=produced)

    full = policy is DisclosurePolicy.FULL
    view = EvidenceView(
        auth_committed=committed,
        auth_exists=committed and issued,
        scope_root=oracle.scope_root,
        scope_cardinality=oracle.scope_cardinality,
        committed_scope=(tuple(scope_items) if (full and scope_items is not None) else None),
        exec_root=oracle.exec_root,
        exec_cardinality=oracle.exec_cardinality,
        exec_record_produced=produced,
        committed_actions=(tuple(exec_items) if (full and produced and exec_items is not None) else None),
        delivery_ack_exists=(bool(execu.get("result_delivered", True))
                             and bool(chain.get("delivery_ack_sent", True))),
        p=p_claims,
        e=e_claims,
        key_revocation_claimed=bool(sc.get("key_claim", {}).get("revoked", False)),
        attestor_present=bool(sc.get("attestor", {}).get("present", False)),
        attestor_available=bool(sc.get("attestor", {}).get("available", False)),
        # The published verdict is evidence; WHY it was published is not.
        adjudicator_published_blame=(
            Party(sc["adjudicator"]["favours_blame"])
            if sc.get("adjudicator", {}).get("favours_blame") else None
        ),
        # Both receipts exist once the message chain completed. Each is the
        # COUNTERPARTY's signature, so it survives the holder losing its own log.
        # RC-H7: a receipt is held only if the message carrying it was sent.
        # An aborted chain leaves the intended holder with no commitment, which
        # is precisely the gap the abort classes probe.
        auth_receipt_held=committed and issued,
        exec_receipt_held=(committed
                           and bool(chain.get("exec_receipt_sent", True))
                           and bool(execu.get("result_delivered", True))),
        history=(tuple(sorted(sc.get("history", {}).items()))
                 if "history" in entitlements else None),
        custodial_actions=(tuple(execu.get("actions", []))
                           if "custodial_copy" in entitlements else None),
        policy=policy,
        pad_to=pad_to,
    )
    return view, oracle


#: Fields of the scenario that must never reach a protocol. The visibility
#: mutation test walks this list.
HIDDEN_FIELDS = (
    "ground_truth.dishonest_party",
    "ground_truth.p_state",
    "ground_truth.e_state",
    "ground_truth.adjudicable",
    "ground_truth.claim",
    "ground_truth.actual",
    "adjudicator.colluding",
    "adjudicator.favours",
    "key_claim.genuine",
    "m_class",
    "mutation_family",
)
