"""Declarative interaction-protocol specifications (specs/*.toml).

A specification lists roles, committed objects and messages. For each message
it says who sends it, who receives it, whether it is signed, which objects'
commitment roots it carries ("binds"), which earlier messages it carries along
("forwards"), which messages must already have arrived ("requires"), and which
checks an honest receiver runs before accepting it ("checks").

The harness does not hard-code any of this. Which signed artifacts exist in a
scenario, and who holds them, is DERIVED from the specification and the
scenario's record of which messages were sent. Changing what a protocol
carries means editing the specification, not the adjudicator.

Three properties are checked in `make check` (see `conformance`):

  1. ordering   -- no scenario marks a message sent whose required
                   predecessors were not sent, under any specification
  2. confinement -- every artifact an adjudicator read was one its own
                   specification declares and the holder actually produced
  3. preconditions -- which classes an honest receiver would have refused
                   under each specification, derived from `checks` and
                   diffed against the declared expectation
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "specs"


@dataclass(frozen=True)
class Message:
    name: str
    sender: str
    receiver: str
    signed: bool
    binds: tuple[str, ...]
    forwards: tuple[str, ...]
    requires: tuple[str, ...]
    checks: tuple[str, ...]


@dataclass(frozen=True)
class Spec:
    name: str
    roles: tuple[str, ...]
    objects: tuple[str, ...]
    messages: tuple[Message, ...]
    description: str = ""

    def message(self, name: str) -> Message:
        for m in self.messages:
            if m.name == name:
                return m
        raise KeyError(f"{self.name}: no message {name!r}")

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(m.name for m in self.messages)

    def validate(self) -> None:
        """Internal consistency. A specification that refers to a message or
        object it does not declare, or forwards a message the forwarder never
        holds, is rejected before anything runs."""
        seen: set[str] = set()
        holds: dict[str, set[str]] = {r: set() for r in self.roles}
        for m in self.messages:
            if m.sender not in self.roles or m.receiver not in self.roles:
                raise ValueError(f"{self.name}.{m.name}: unknown role")
            for o in m.binds:
                if o not in self.objects:
                    raise ValueError(f"{self.name}.{m.name}: binds unknown object {o}")
            if m.binds and not m.signed:
                raise ValueError(f"{self.name}.{m.name}: an unsigned message cannot bind")
            for r in m.requires:
                if r not in seen:
                    raise ValueError(f"{self.name}.{m.name}: requires {r}, "
                                     f"which is not declared earlier")
            for f in m.forwards:
                if f not in holds[m.sender]:
                    raise ValueError(f"{self.name}.{m.name}: forwards {f}, "
                                     f"which {m.sender} never holds")
            for c in m.checks:
                kind, *objs = c.split(":")
                if kind not in ("subset", "equal") or len(objs) != 2:
                    raise ValueError(f"{self.name}.{m.name}: malformed check {c!r}")
                if any(o not in self.objects for o in objs):
                    raise ValueError(f"{self.name}.{m.name}: check on unknown object")
            seen.add(m.name)
            holds[m.receiver].add(m.name)
            holds[m.receiver].update(m.forwards)


@lru_cache(maxsize=None)
def load(name: str) -> Spec:
    raw = tomllib.loads((SPEC_DIR / f"{name}.toml").read_text(encoding="utf-8"))
    msgs = tuple(
        Message(
            name=m["name"], sender=m["from"], receiver=m["to"],
            signed=bool(m["signed"]), binds=tuple(m.get("binds", ())),
            forwards=tuple(m.get("forwards", ())),
            requires=tuple(m.get("requires", ())),
            checks=tuple(m.get("checks", ())),
        )
        for m in raw["message"]
    )
    spec = Spec(name=raw["protocol"]["name"], roles=tuple(raw["protocol"]["roles"]),
                objects=tuple(raw["objects"]), messages=msgs,
                description=raw["protocol"].get("description", ""))
    if spec.name != name:
        raise ValueError(f"specs/{name}.toml declares name {spec.name!r}")
    spec.validate()
    return spec


SPEC_NAMES = ("bearer3", "hop3", "chain3")


# ---------------------------------------------------------------------------
# Holdings: which signed artifacts exist, and who holds a copy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Copy:
    """One party's copy of one signed message."""
    message: str
    signer: str
    holder: str
    binds: tuple[str, ...]
    forwarded: bool          # True when held via another message, not received directly

    @property
    def id(self) -> str:
        return f"{self.message}@{self.holder}"


def holdings(spec: Spec, sent: dict[str, bool]) -> tuple[Copy, ...]:
    """Every copy of every signed message that exists, given which messages
    were sent. A forwarded copy exists only if both the forwarding message and
    the forwarded one were sent: you cannot pass on what you never received."""
    out: list[Copy] = []
    for m in spec.messages:
        if not sent.get(m.name, False):
            continue
        if m.signed:
            out.append(Copy(m.name, m.sender, m.receiver, m.binds, forwarded=False))
        for f in m.forwards:
            fm = spec.message(f)
            if fm.signed and sent.get(f, False):
                out.append(Copy(fm.name, fm.sender, m.receiver, fm.binds, forwarded=True))
    # a party may receive the same message by two routes; one copy is enough
    uniq: dict[str, Copy] = {}
    for c in out:
        uniq.setdefault(c.id, c)
    return tuple(uniq.values())


def ordering_violations(spec: Spec, sent: dict[str, bool]) -> list[str]:
    errs = []
    for m in spec.messages:
        if sent.get(m.name, False):
            for r in m.requires:
                if not sent.get(r, False):
                    errs.append(f"{m.name} sent without {r}")
    return errs


def precondition_failures(spec: Spec, objects: dict[str, list[str]],
                          sent: dict[str, bool],
                          honest: frozenset[str] = frozenset({"P", "I", "E"})) -> list[str]:
    """Checks an HONEST receiver would have failed, on the objects as signed.

    A failure means that, under this specification, an honest receiver refuses
    the message and the run stops there. The harness still adjudicates the
    world as it happened -- the corpus is fixed across specifications -- so a
    failure is reported as prevention, a separate property from adjudication.
    A dishonest receiver is assumed to accept anything that serves it.
    """
    fails = []
    for m in spec.messages:
        if not sent.get(m.name, False) or m.receiver not in honest:
            continue
        for c in m.checks:
            kind, a, b = c.split(":")
            A, B = set(objects.get(a, ())), set(objects.get(b, ()))
            ok = A <= B if kind == "subset" else A == B
            if not ok:
                fails.append(f"{m.name}:{c}")
    return fails
