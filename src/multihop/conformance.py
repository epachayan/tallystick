"""Protocol conformance: the harness against the specifications it claims to run.

Five checks, each a derive-and-diff:

  1. every specification is internally valid (spec.Spec.validate)
  2. ordering: no scenario sends a message before what it requires, under any
     specification
  3. confinement: the copies each adjudicator received are exactly those its
     specification yields for that scenario. Derived here by a second,
     independent walk of the message table and diffed against the view the
     harness built. A protocol cannot see a forwarded copy its specification
     does not forward, or a copy its holder did not produce.
  4. visibility: mutating each hidden field (ground truth, class labels)
     leaves every verdict unchanged
  5. prevention: which classes an honest receiver would refuse under each
     specification's checks, derived and diffed against EXPECTED_PREVENTED
"""

from __future__ import annotations

import copy as _copy

from .evidence import HIDDEN_FIELDS, build_view
from .generator import load_corpus
from .harness import evaluate
from .model import Truth3
from .protocols import PROTOCOLS3
from .spec import SPEC_NAMES, load, ordering_violations, precondition_failures

#: classes an honest receiver refuses under each specification, before any
#: action outside the delegation is executed
EXPECTED_PREVENTED = {
    "bearer3": set(),
    "hop3": set(),
    "chain3": {"H2", "H3", "H5", "H9"},
}


def _expected_copy_ids(spec, sc) -> set[str]:
    """Independent re-derivation from the message table."""
    sent = sc["sent"]
    unavailable = set(sc.get("unavailable", ()))
    withheld = sc.get("withheld", {})
    by_name = {m.name: m for m in spec.messages}
    held: set[tuple[str, str]] = set()
    for m in spec.messages:
        if m.signed and sent.get(m.name):
            held.add((m.name, m.receiver))
    for m in spec.messages:
        if not sent.get(m.name):
            continue
        for f in m.forwards:
            if by_name[f].signed and sent.get(f):
                held.add((f, m.receiver))
    return {f"{name}@{holder}" for name, holder in held
            if holder not in unavailable and name not in withheld.get(holder, ())}


def _set_path(d: dict, path: str, value) -> bool:
    keys = path.split(".")
    cur = d
    for k in keys[:-1]:
        if not isinstance(cur, dict) or k not in cur or cur[k] is None:
            return False
        cur = cur[k]
    if not isinstance(cur, dict) or keys[-1] not in cur:
        return False
    cur[keys[-1]] = value
    return True


def _mutations(path: str, original):
    if path == "ground_truth.states":
        return [{"P": "dishonest", "I": "dishonest", "E": "dishonest"},
                {"P": "honest", "I": "honest", "E": "honest"}]
    if path == "ground_truth.adjudicable":
        return [not original]
    if path == "ground_truth.actual":
        return [{"G": [], "S": [], "X": [], "R": []}]
    return ["<mutated>"]


def run(scenarios=None) -> list[str]:
    scenarios = scenarios or load_corpus()
    errs: list[str] = []

    for name in SPEC_NAMES:
        try:
            load(name)
        except Exception as e:      # noqa: BLE001 -- report every malformed spec
            errs.append(f"spec {name}: {e}")

    for sc in scenarios:
        for name in SPEC_NAMES:
            for v in ordering_violations(load(name), sc["sent"]):
                errs.append(f"{sc['scenario_id']} under {name}: {v}")

    for sc in scenarios:
        for pname, proto in PROTOCOLS3.items():
            view, _ = build_view(proto.spec, sc, proto.disclosure)
            got = {c.id for c in view.copies}
            want = _expected_copy_ids(proto.spec, sc)
            if got != want:
                errs.append(f"{sc['scenario_id']} {pname}: view carries {sorted(got ^ want)} "
                            f"outside what {proto.spec_name} yields")

    for sc in scenarios[:: max(1, len(scenarios) // 45)]:
        for pname, proto in PROTOCOLS3.items():
            base = evaluate(proto, sc).key()
            for path in HIDDEN_FIELDS:
                keys = path.split(".")
                orig = sc
                for k in keys:
                    orig = orig.get(k) if isinstance(orig, dict) else None
                for value in _mutations(path, orig):
                    m = _copy.deepcopy(sc)
                    if not _set_path(m, path, value):
                        continue
                    if evaluate(proto, m).key() != base:
                        errs.append(f"{sc['scenario_id']} {pname}: verdict moved when "
                                    f"{path} was mutated")

    derived: dict[str, set[str]] = {n: set() for n in SPEC_NAMES}
    for sc in scenarios:
        truth = Truth3.from_scenario(sc)
        honest = frozenset(p.value for p, _s in truth.states) - {p.value for p in truth.dishonest}
        for name in SPEC_NAMES:
            if precondition_failures(load(name), sc["objects"], sc["sent"], honest):
                derived[name].add(sc["h_class"])
    for name in SPEC_NAMES:
        if derived[name] != EXPECTED_PREVENTED[name]:
            errs.append(f"prevention under {name}: declared {sorted(EXPECTED_PREVENTED[name])}, "
                        f"derived {sorted(derived[name])}")
    return errs


def main():
    scs = load_corpus()
    errs = run(scs)
    print("-- three-party protocol conformance")
    if errs:
        for e in errs[:40]:
            print(f"  {e}")
        if len(errs) > 40:
            print(f"  ... and {len(errs) - 40} more")
        raise SystemExit(f"CONFORMANCE: {len(errs)} issue(s)")
    print(f"  specs valid ({', '.join(SPEC_NAMES)}); ordering holds in {len(scs)} scenarios;")
    print(f"  every view confined to its specification; hidden fields inert;")
    prevented = ", ".join(f"{n}: {sorted(v) or 'none'}" for n, v in EXPECTED_PREVENTED.items())
    print(f"  prevention matches declaration ({prevented})")


if __name__ == "__main__":
    main()
