"""
Tallystick mutation generator.

Emits adversarial delegation scenarios as seeded JSONL. Knows NOTHING about
cryptography: no signatures, no hashes, no receipts. A scenario says what each
party did and what each party claims. Whether a given scheme can detect the
divergence is the scheme's problem, evaluated separately by the scorer.

This decoupling is deliberate. If the generator learns about signing it couples
to the first baseline and becomes useless the moment a second one is added.

Usage:
    python3 generator.py --seed 20260808 --per-class 25 --out corpus/corpus.v0.1.jsonl
"""

import argparse
import json
import random

SCHEMA_VERSION = "0.2"

# ---------------------------------------------------------------------------
# Vocabulary. Deliberately generic: the point is the delegation structure, not
# the domain. Swap this out without touching anything else.
# ---------------------------------------------------------------------------

_VERBS = ["read", "write", "delete", "send", "issue", "modify",
          "export", "invoke", "update", "approve", "archive", "publish"]
_OBJECTS = ["records", "email", "refund", "permissions", "dataset",
            "payment", "config", "report", "ticket", "invoice",
            "credential", "workflow"]
OPERATIONS = [f"{v}:{o}" for v in _VERBS for o in _OBJECTS]   # 144 operations

SCOPE_SIZE = 3   # overridden by --scope-size


# ---------------------------------------------------------------------------
# M-class taxonomy. Versioned independently of the schema so that adding a
# class is not a breaking change.
#
# NOTE: this is a reconstruction of the M0-M11 set. It preserves the
# behavioural/record-tampering split and adds explicit principal-liar coverage,
# which is what the regression thesis needs to test. Reconcile against the
# authoritative list before publication.
# ---------------------------------------------------------------------------

M_CLASSES = {
    "M0":  ("control",            "none", "honest run, no mutation"),
    "M1":  ("behavioural",        "E",    "executor exceeds granted scope"),
    "M2":  ("behavioural",        "E",    "executor omits an authorized action, claims completion"),
    "M3":  ("record_tampering",   "E",    "executor alters its stored copy of the authorization"),
    "M4":  ("record_tampering",   "E",    "executor alters its stored copy of the execution record"),
    "M5":  ("behavioural",        "P",    "principal repudiates the authorization entirely"),
    "M6":  ("behavioural",        "P",    "principal asserts a narrower scope than was granted"),
    "M7":  ("behavioural",        "P",    "principal denies receiving the delivered result"),
    "M8":  ("behavioural",        "E",    "executor fabricates an authorization never issued"),
    "M9":  ("record_tampering",   "P",    "principal alters its stored copy of the authorization"),
    "M10": ("benign_divergence",  "none", "records diverge through loss, neither party dishonest"),
    "M11": ("behavioural",        "both", "both parties misrepresent a committed authorization"),
    "M12": ("no_commitment",      "both", "implicit grant, never committed; parties disagree, unadjudicable"),
    "M13": ("query_abuse",        "P",    "principal raises a baseless dispute to probe the committed set"),
    "M14": ("adjudicator_abuse",  "J",    "adjudicator colludes with the principal against a correct executor"),
    # --- V1: mistake, not malice. Evidence identical to the malicious twin. ---
    "M15": ("mistake",            "none", "principal sincerely misremembers the scope it granted (twin of M6)"),
    "M16": ("mistake",            "none", "executor acts in good faith on a stale cached grant (twin of M1)"),
    "M17": ("mistake",            "none", "principal misremembers delivery; result was in fact delivered (twin of M7)"),
    "M18": ("mixed",              "E",    "principal misremembers AND executor genuinely exceeded scope"),
    "M19": ("record_tampering",   "E",    "executor tampers, then claims the record is simply unavailable"),
    # --- A4/T5: statefulness. A single claim of loss is an assertion; a
    #     PATTERN of claimed losses is a behaviour. Twins again.
    "M20": ("pattern_abuse",      "E",    "executor repeatedly claims loss to hide repeated tampering"),
    "M21": ("pattern_benign",     "none", "executor suffers genuine repeated loss at the same observed rate"),
    # --- K5: excuse-ranking. Claiming key compromise dominates claiming loss:
    #     equally unprovable, and it destroys evidence already issued.
    "M22": ("excuse_abuse",       "E",    "executor falsely claims its signing key was compromised, voiding its evidence"),
    "M23": ("excuse_benign",      "none", "a thief with the executor's compromised key performed the out-of-scope action"),
    # --- T10 relocation test: attest the residual, and see where it moves ---
    "M24": ("attestor_abuse",     "E",    "executor guilty; the external attestor's own record is unavailable"),
    "M25": ("attestor_benign",    "none", "executor honest; the attestor's record is genuinely unavailable"),
    # --- RC-H9: SYMMETRIC WITHHOLDING. Every class above models withholding as
    #     an executor behaviour; the principal produced its record in all 650
    #     scenarios. These four mirror M19/M10 and M20/M21 with the roles
    #     reversed, so a mechanism whose duty attaches on non-production is
    #     tested against both parties rather than only the one it was built for.
    "M26": ("record_tampering",   "P",    "principal alters its stored authorization, then claims it is unavailable"),
    "M27": ("benign_divergence",  "none", "principal genuinely loses its stored copy; nobody is dishonest"),
    "M28": ("pattern_abuse",      "P",    "principal repeatedly claims loss to hide repeated tampering"),
    "M29": ("pattern_benign",     "none", "principal suffers genuine repeated loss at the same observed rate"),
    # --- RC-H7: ABORT. Every class above assumes the message chain completes.
    #     B13's witness chain has a fairness asymmetry after step 2: the
    #     executor holds evidence of origin while the principal holds nothing
    #     about the execution. These four make that visible.
    "M30": ("abort_abuse",        "E",    "executor acts, then aborts before sending the execution receipt"),
    "M31": ("abort_benign",       "none", "the execution receipt is lost in transit; executor acted correctly"),
    "M32": ("abort_abuse",        "P",    "principal aborts before acknowledging a delivered result"),
    "M33": ("abort_benign",       "none", "the delivery acknowledgement is lost in transit"),
}

# Classes where the principal is dishonest AND the executor is correct. These
# are the ones on which "can a correct executor defend itself?" is a fair
# question at all.
#
# RC-H12 found this set had been standing in for two different things. The
# original PRINCIPAL_LIAR held M5/M6/M7/M9 and was used as the F01 denominator,
# but the corpus contains six more classes with a dishonest principal, and in
# four of them the executor IS correct. Measuring F01 on the smaller set
# flattered B1: it scores 0/25 on each of the four, exactly as B0 does.
#
# So the set is split. The distinction is the KIND of lie, and it turns out to
# be the thing that decides whether a bilateral commitment helps.

#: The principal lies BY ASSERTION about a committed fact. A signature
#: contradicts it. This is the set F01 is stated over.
PRINCIPAL_LIAR = {"M5", "M6", "M7", "M9"}

#: The principal is dishonest and the executor is correct, but the lie is not an
#: assertion about a committed fact -- it is a baseless complaint (M13), a
#: withheld record (M26, M28), or an abort before acknowledging delivery (M32).
#: No signature contradicts these, and bilateral commitment does not reach them.
PRINCIPAL_LIAR_NON_ASSERTIONAL = {"M13", "M26", "M28", "M32"}

#: Both parties dishonest: "can a CORRECT executor defend itself" does not apply.
PRINCIPAL_LIAR_BOTH = {"M11", "M12"}

#: Every class with a dishonest principal, for audit purposes.
PRINCIPAL_DISHONEST = (PRINCIPAL_LIAR | PRINCIPAL_LIAR_NON_ASSERTIONAL
                       | PRINCIPAL_LIAR_BOTH)

# Evidential twins: a mistake class and its malicious counterpart must be
# generated from the SAME underlying scope and actions, so that the only
# difference between them is intent. Seeding both from the malicious class's
# stream is what makes the adjudicator views byte-identical.
TWIN_OF = {"M15": "M6", "M16": "M1", "M17": "M7", "M23": "M22", "M25": "M24",
           "M10": "M19", "M21": "M20",
           # symmetric-withholding twins (RC-H9)
           "M27": "M26", "M29": "M28",
           # abort twins (RC-H7): a deliberate abort and a lost message are
           # indistinguishable to the counterparty by construction.
           "M31": "M30", "M33": "M32"}


def _scope(rng, n=None):
    return sorted(rng.sample(OPERATIONS, n or SCOPE_SIZE))


def _view(scope, actions, auth_issued=True, result_received=True, intact=True, available=True, disputed=None):
    return {
        "asserted_scope": scope,
        "asserted_actions": actions,
        "asserted_auth_issued": auth_issued,
        "asserted_result_received": result_received,
        "record_intact": intact,
        "record_available": available,
        "disputed_action": disputed,
    }


def make_scenario(m_class, seed, idx):
    """Build one scenario. Deterministic in (m_class, seed, idx)."""
    rng = random.Random(f"{TWIN_OF.get(m_class, m_class)}:{seed}:{idx}")
    family, dishonest, description = M_CLASSES[m_class]

    scope = _scope(rng)
    actions = list(scope[: rng.randint(1, len(scope))])
    auth_issued = True
    result_delivered = True
    # RC-H7: which witness messages actually reached the counterparty.
    exec_receipt_sent = True
    delivery_ack_sent = True
    adjudicable = True

    # defaults: both parties assert the truth
    p_scope, p_actions = list(scope), list(actions)
    e_scope, e_actions = list(scope), list(actions)
    p_auth, e_auth = True, True
    p_recv, e_recv = True, True
    p_intact, e_intact = True, True
    p_available, e_available = True, True
    auth_committed = True
    p_disputed = None
    key_claim = {"revoked": False, "genuine": False}
    attestor = {"present": True, "available": True}
    adjudicator = {"colluding": False}
    p_state, e_state = "honest", "honest"
    history = {"e_disputes": 0, "e_suspensions": 0}

    if m_class == "M0":
        pass

    elif m_class == "M1":
        # executor performs something outside scope, then hides it
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = [a for a in actions if a != extra]   # E omits it from its account
        p_actions = None                                  # P cannot observe directly

    elif m_class == "M2":
        omitted = rng.choice(actions)
        actions = [a for a in actions if a != omitted]
        e_actions = actions + [omitted]                   # E claims it did the omitted one
        p_actions = None

    elif m_class == "M3":
        widened = rng.choice([o for o in OPERATIONS if o not in scope])
        e_scope = sorted(scope + [widened])               # E's stored auth was widened
        e_intact = False
        p_actions = None

    elif m_class == "M4":
        victim = rng.choice(actions) if actions else None
        e_actions = [a for a in actions if a != victim]
        e_intact = False
        p_actions = None

    elif m_class == "M5":
        p_auth = False
        p_scope, p_actions = None, None                   # "I never authorized anything"

    elif m_class == "M6":
        p_scope = scope[: max(1, len(scope) - 1)]         # P asserts a narrower grant
        p_actions = None

    elif m_class == "M7":
        p_recv = False                                     # P denies delivery
        p_actions = None

    elif m_class == "M8":
        auth_issued = False
        actions = []
        e_scope, e_actions = list(scope), list(scope)      # E invents the whole thing
        p_auth = False
        p_scope, p_actions = None, None

    elif m_class == "M9":
        p_scope = scope[: max(1, len(scope) - 1)]
        p_intact = False                                   # P's stored copy was edited
        p_actions = None

    elif m_class == "M10":
        e_actions = None                                   # record lost, not altered
        e_available = False
        p_actions = None

    elif m_class == "M11":
        p_scope = scope[: max(1, len(scope) - 1)]
        e_scope = sorted(scope + [rng.choice([o for o in OPERATIONS if o not in scope])])
        p_actions, e_actions = None, list(actions)
        # both lie, but a committed authorization settles it -> adjudicable

    elif m_class == "M24":
        # An external attestor was supposed to close the residual. The executor
        # is guilty, and now the ATTESTOR cannot produce its witness.
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = None
        e_available = False
        p_actions = None
        attestor = {"present": True, "available": False}

    elif m_class == "M25":
        # True twin: identical view, but the executor is honest and the
        # attestor's outage is genuine.
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = None
        e_available = False
        p_actions = None
        attestor = {"present": True, "available": False}
        e_state = "honest"

    elif m_class == "M22":
        # Guilty of overreach, then voids its own signatures retroactively.
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = None
        p_actions = None
        key_claim = {"revoked": True, "genuine": False}

    elif m_class == "M23":
        # TRUE twin of M22. The record contains the same out-of-scope action,
        # signed with the executor's key -- but the executor did not perform it;
        # a thief holding the compromised key did. The adjudicator sees exactly
        # what it sees in M22. Did you do it, or did the thief?
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = None
        p_actions = None
        key_claim = {"revoked": True, "genuine": True}
        e_state = "honest"

    elif m_class == "M20":
        # Guilty, hiding behind the loss excuse, and has done so before.
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = None
        e_available = False
        e_intact = False
        p_actions = None
        n = rng.randint(6, 12)
        history = {"e_disputes": n, "e_suspensions": rng.randint(max(1, n // 2), n)}

    elif m_class == "M21":
        # Honest, genuinely unlucky, and the OBSERVED rate is drawn from the
        # same range. If the adjudicator only sees the rate, it cannot separate
        # this from M20.
        e_actions = None
        e_available = False
        p_actions = None
        n = rng.randint(6, 12)
        history = {"e_disputes": n, "e_suspensions": rng.randint(max(1, n // 2), n)}

    elif m_class == "M19":
        # A19 was untested: record_intact and record_available were treated as
        # independent. A tamperer can hide behind the loss excuse, which every
        # suspected/exposed scheme treats as non-culpable.
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = None
        e_available = False          # "I can't produce it"
        e_intact = False             # ...because I altered it
        p_actions = None

    elif m_class == "M30":
        # The executor performs an out-of-scope action, then does not send the
        # execution receipt. The principal therefore never obtains a commitment
        # over the execution record -- the exact gap B13's chain leaves open.
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = None
        exec_receipt_sent = False
        result_delivered = False

    elif m_class == "M31":
        # TRUE twin of M30: the executor acted correctly and the receipt was
        # lost in transit. Identical evidence; only intent differs.
        e_actions = None
        exec_receipt_sent = False
        result_delivered = False

    elif m_class == "M32":
        # The principal receives the result and aborts before acknowledging,
        # leaving the executor with no proof of delivery.
        p_recv = False
        p_actions = None
        delivery_ack_sent = False

    elif m_class == "M33":
        # TRUE twin of M32: the acknowledgement was genuinely lost.
        p_recv = False
        p_actions = None
        delivery_ack_sent = False

    elif m_class == "M26":
        # Mirror of M19 with the roles reversed. The principal narrows the scope
        # it asserts, alters its stored copy to match, then declines to produce
        # it. Withholding is exactly as available to a principal as to an
        # executor; the corpus simply never asked.
        p_scope, p_actions = None, None
        p_intact = False              # ...because I altered it
        p_available = False           # "I can't produce it"

    elif m_class == "M27":
        # TRUE twin of M26: the principal's copy is genuinely lost. Nobody is
        # dishonest. Evidence identical to M26 by construction.
        p_scope, p_actions = None, None
        p_available = False

    elif m_class == "M28":
        # Mirror of M20. A single claimed loss is an assertion; a PATTERN of
        # them is a behaviour. The pattern is on the principal's side here, and
        # no mechanism in the set currently looks for it there.
        p_scope, p_actions = None, None
        p_intact = False
        p_available = False
        n = rng.randint(6, 12)
        history = {"p_disputes": n, "p_suspensions": rng.randint(max(1, n // 2), n),
                   "e_disputes": 0, "e_suspensions": 0}

    elif m_class == "M29":
        # TRUE twin of M28: genuine repeated loss at the same observed rate.
        p_scope, p_actions = None, None
        p_available = False
        n = rng.randint(6, 12)
        history = {"p_disputes": n, "p_suspensions": rng.randint(max(1, n // 2), n),
                   "e_disputes": 0, "e_suspensions": 0}

    elif m_class == "M15":
        # Byte-identical to M6. The ONLY difference is intent, which leaves no
        # trace in any signed record.
        p_scope = scope[: max(1, len(scope) - 1)]
        p_actions = None
        p_state = "mistaken"

    elif m_class == "M16":
        # Twin of M1: the executor performs an action outside the current scope,
        # but on a grant it holds in good faith and believes current.
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = actions
        p_actions = None
        e_state = "mistaken"

    elif m_class == "M17":
        p_recv = False
        p_actions = None
        p_state = "mistaken"

    elif m_class == "M18":
        p_scope = scope[: max(1, len(scope) - 1)]
        extra = rng.choice([o for o in OPERATIONS if o not in scope])
        actions = actions + [extra]
        e_actions = [a for a in actions if a != extra]
        p_state, e_state = "mistaken", "dishonest"

    elif m_class == "M14":
        # Both parties behave correctly. The ADJUDICATOR is the adversary: it
        # returns a verdict against the executor despite the evidence.
        adjudicator = {"colluding": True, "favours": "P", "favours_blame": "E"}
        p_actions = None

    elif m_class == "M13":
        # P's account is entirely truthful. It simply names an in-scope action as
        # "unauthorized" so the adjudicator will run a membership query on it.
        # The complaint is baseless; the query is the point.
        p_disputed = rng.choice(scope)
        p_actions = None

    elif m_class == "M12":
        # No commitment was ever made: the grant was implicit/verbal. The parties
        # disagree and NOTHING can settle it. Abstaining here is correct.
        auth_committed = False
        p_scope = scope[: max(1, len(scope) - 1)]
        e_scope = sorted(scope + [rng.choice([o for o in OPERATIONS if o not in scope])])
        p_actions, e_actions = None, list(actions)
        adjudicable = False

    return {
        "scenario_id": f"{m_class}-{seed}-{idx:04d}",
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "m_class": m_class,
        "mutation_family": family,
        "authorization": {
            "auth_id": f"auth-{seed}-{idx:04d}",
            "issued": auth_issued,
            "committed": auth_committed,
            "scope": scope if auth_issued else [],
            "constraints": {},
        },
        "chain": {
            "exec_receipt_sent": exec_receipt_sent,
            "delivery_ack_sent": delivery_ack_sent,
        },
        "execution": {
            "actions": actions,
            "result_delivered": result_delivered,
        },
        "p_view": _view(p_scope, p_actions, p_auth, p_recv, p_intact, p_available, p_disputed),
        "e_view": _view(e_scope, e_actions, e_auth, e_recv, e_intact, e_available),
        "adjudicator": adjudicator,
        "history": history,
        "key_claim": key_claim,
        "attestor": attestor,
        "ground_truth": {
            "dishonest_party": dishonest,
            "claim": description,
            "actual": f"scope={scope} actions={actions} issued={auth_issued}",
            "adjudicable": adjudicable,
            # Party states default from the class's liar, unless a mistake class
            # overrode them above. Mistake and malice are distinct states that
            # produce identical evidence -- that is the whole point of M15-M18.
            "p_state": (p_state if p_state != "honest"
                        else ("dishonest" if dishonest in ("P", "both") else "honest")),
            "e_state": (e_state if e_state != "honest"
                        else ("dishonest" if dishonest in ("E", "both") else "honest")),
        },
    }


def generate(seed, per_class):
    for m_class in M_CLASSES:
        for i in range(per_class):
            yield make_scenario(m_class, seed, i)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260808)
    ap.add_argument("--per-class", type=int, default=25)
    ap.add_argument("--out", default="../corpus/corpus.v0.2.jsonl")
    ap.add_argument("--scope-size", type=int, default=3)
    args = ap.parse_args()

    global SCOPE_SIZE
    SCOPE_SIZE = args.scope_size

    n = 0
    with open(args.out, "w") as fh:
        for s in generate(args.seed, args.per_class):
            fh.write(json.dumps(s) + "\n")
            n += 1
    print(f"wrote {n} scenarios across {len(M_CLASSES)} classes -> {args.out}")


if __name__ == "__main__":
    main()
