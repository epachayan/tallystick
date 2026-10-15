"""Three-party scenario classes (H1-H9).

Separate namespace from M0-M33: the two-party corpus is frozen and nothing
here may move one of its figures.

A scenario records the world ONCE, independent of any protocol:

    objects       the committed sets as originally signed (G, S, X, R)
    fabrication   colluders' re-signed versions, and when they made them
    sent          which messages of the flow actually reached their receiver
    unavailable   parties that produce nothing at adjudication
    withheld      single messages a producing party does not produce
    claims        what each party asserts, None meaning silent
    disputed      the action P names in its complaint, if any
    ground_truth  each party's state, and the true sets

Which of those messages are SIGNED, what each one binds, and who ends up
holding a copy is not in the scenario. It comes from the protocol's
specification (specs/*.toml), so the same world is adjudicated under every
variant and only the protocol differs.

Twin pairs are generated from the guilty class's random stream, so the two
worlds share every value and differ only where the class definition says.
Whether they are actually indistinguishable to an adjudicator, and under which
specification, is not declared here -- src/multihop/boundary.py derives it.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from ..generator import OPERATIONS

SCHEMA = "chain3-0.1"
DEFAULT_SEED = 20261015
PER_CLASS = 25
ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "corpus" / "multihop.v0.1.jsonl"

FLOW = ("grant", "grant_ack", "subgrant", "subgrant_ack",
        "exec_receipt", "report", "report_ack")

#: class -> (family, diverging parties, description)
H_CLASSES = {
    "H1": ("control", "", "honest chain; every party asserts the record"),
    "H2": ("widening_abuse", "I",
           "I sub-delegates beyond its grant, then claims it granted the narrow "
           "scope and that E overreached"),
    "H3": ("widening_mistake", "I",
           "I mis-transcribed the sub-grant and sincerely believes it granted the "
           "narrow scope (twin of H2)"),
    "H4": ("overreach_silent", "E",
           "E executes beyond its sub-grant and goes silent; I has genuinely lost "
           "E's acknowledgement of the sub-grant"),
    "H5": ("widening_withheld", "I",
           "I widens the sub-grant, withholds E's acknowledgement and claims it was "
           "lost; E acted in good faith and is unreachable (twin of H4 under re-signing)"),
    "H6": ("collusion_downstream", "IE",
           "I and E collude from the start and re-sign a consistent history that "
           "hides an action P observed"),
    "H7": ("complaint_mistake", "P",
           "P sincerely misattributes an outside effect to the chain; nothing it "
           "names was executed (twin of H6)"),
    "H8": ("collusion_upstream", "PI",
           "after the fact, P and I re-sign a narrower grant to pin an authorized "
           "action on E"),
    "H9": ("widening_beyond_grant", "I",
           "I sub-delegates an action P never granted and blames E; P is honest "
           "(twin of H8 under re-signing)"),
}

#: honest/mistaken class -> class whose random stream it shares
TWIN_OF = {"H3": "H2", "H4": "H5", "H7": "H6", "H9": "H8"}

#: classes whose divergence is a mistake rather than dishonesty
MISTAKE = {"H3": "I", "H7": "P"}


def _sorted(xs):
    return sorted(set(xs))


def make_scenario(h: str, seed: int, idx: int) -> dict:
    family, diverging, description = H_CLASSES[h]
    rng = random.Random(f"{TWIN_OF.get(h, h)}:{seed}:{idx}")

    G = _sorted(rng.sample(OPERATIONS, 3))
    S0 = _sorted(rng.sample(G, 2))
    outside = rng.choice([o for o in OPERATIONS if o not in G])   # never granted by P
    inside = next(o for o in G if o not in S0)                   # granted by P, not sub-delegated

    objects = {"G": G, "S": S0, "X": list(S0), "R": list(S0)}
    fabrication = None
    sent = {m: True for m in FLOW}
    unavailable: list[str] = []
    withheld: dict[str, list[str]] = {"P": [], "I": [], "E": []}
    claims = {
        "P": {"G": G, "report_received": True},
        "I": {"G": G, "S": S0, "X": list(S0)},
        "E": {"S": S0, "X": list(S0)},
    }
    disputed = None
    actual = {k: list(v) for k, v in objects.items()}

    if h == "H1":
        pass

    elif h in ("H2", "H3"):
        S = _sorted(S0 + [outside])
        objects.update(S=S, X=S, R=S)
        claims["I"].update(S=S0, X=S)          # I asserts the narrow sub-grant
        claims["E"].update(S=S, X=S)
        disputed = outside

    elif h in ("H4", "H5"):
        if h == "H4":
            X = _sorted(S0 + [outside])            # E overreaches
            objects.update(S=S0, X=X, R=X)
        else:
            S = _sorted(S0 + [outside])            # I widens
            objects.update(S=S, X=S, R=S)
        unavailable = ["E"]
        # H4: genuinely lost after the report was sent; H5: withheld and called lost.
        withheld["I"] = ["subgrant_ack"]
        claims["I"].update(S=S0, X=objects["X"])
        claims["E"] = {"S": None, "X": None}
        disputed = outside

    elif h in ("H6", "H7"):
        if h == "H6":
            S = _sorted(S0 + [outside])
            objects.update(S=S, X=S, R=S)
            # I and E agree on a cover story before anything reaches P.
            fabrication = {"by": ["I", "E"], "before_report": True,
                           "objects": {"S": S0, "X": S0, "R": S0}}
        claims["I"].update(S=S0, X=S0)
        claims["E"].update(S=S0, X=S0)
        disputed = outside                         # P names an action it observed (H6) or misattributed (H7)

    elif h in ("H8", "H9"):
        # `inside` is an action P genuinely granted (H8), sub-delegated by I and
        # executed by E. P and I now claim P never granted it.
        S = _sorted(S0 + [inside])
        G_narrow = [g for g in G if g != inside]
        if h == "H8":
            objects.update(G=G, S=S, X=S, R=S)
            fabrication = {"by": ["P", "I"], "before_report": False,
                           "objects": {"G": G_narrow}}
            # A colluding P also keeps back anything it holds that E signed over
            # the original grant. Under hop3 it holds nothing of the kind, so
            # this only bites where a specification forwards E's signature to P.
            withheld["P"] = ["subgrant_ack"]
        else:
            objects.update(G=G_narrow, S=S, X=S, R=S)
        withheld["I"] = ["subgrant_ack"]
        claims["P"].update(G=G_narrow)
        claims["I"].update(G=G_narrow, S=S0, X=S)
        claims["E"].update(S=S, X=S)
        disputed = inside
        actual = {k: list(v) for k, v in objects.items()}

    if h not in ("H8", "H9"):
        actual = {k: list(v) for k, v in objects.items()}

    states = {"P": "honest", "I": "honest", "E": "honest"}
    for p in diverging:
        states[p] = "mistaken" if MISTAKE.get(h) == p else "dishonest"

    return {
        "scenario_id": f"{h}-{seed}-{idx:04d}",
        "schema": SCHEMA,
        "seed": seed,
        "h_class": h,
        "family": family,
        "objects": objects,
        "fabrication": fabrication,
        "sent": sent,
        "unavailable": unavailable,
        "withheld": withheld,
        "claims": claims,
        "disputed": disputed,
        "ground_truth": {
            "states": states,
            "adjudicable": True,
            "claim": description,
            "actual": actual,
        },
    }


def generate(seed: int = DEFAULT_SEED, per_class: int = PER_CLASS):
    for h in H_CLASSES:
        for i in range(per_class):
            yield make_scenario(h, seed, i)


def load_corpus(path: Path = CORPUS) -> list[dict]:
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--per-class", type=int, default=PER_CLASS)
    ap.add_argument("--out", default=str(CORPUS))
    a = ap.parse_args()
    rows = list(generate(a.seed, a.per_class))
    with open(a.out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"wrote {len(rows)} three-party scenarios across {len(H_CLASSES)} H-classes -> {a.out}")


if __name__ == "__main__":
    main()
