"""docs/protocols/specs.md is GENERATED from specs/*.toml.

A prose restatement of a specification is a copy, and copies drift (the
two-party taxonomy did, which is why docs/taxonomy.md is generated). So the
message tables are rendered from the TOML and `make check` fails if the file
on disk differs from what the specifications produce.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .spec import SPEC_NAMES, load

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "protocols" / "specs.md"


def render() -> str:
    L = ["# Interaction-protocol specifications (generated)", "",
         "Generated from `specs/*.toml` by `make spec-doc`. Do not edit by hand: "
         "`make check` fails if this file differs from the specifications. "
         "The prose account is in [README.md](README.md).", ""]
    for name in SPEC_NAMES:
        s = load(name)
        L.append(f"## {s.name}")
        L.append("")
        L.append(f"{s.description}. Roles {', '.join(s.roles)}; objects "
                 f"{', '.join(s.objects)}.")
        L.append("")
        L.append("| # | message | from | to | signed | binds | forwards | requires | receiver checks |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for i, m in enumerate(s.messages, 1):
            def cell(xs):
                return ", ".join(xs) if xs else "-"
            L.append(f"| {i} | `{m.name}` | {m.sender} | {m.receiver} | "
                     f"{'yes' if m.signed else 'no'} | {cell(m.binds)} | {cell(m.forwards)} | "
                     f"{cell(m.requires)} | {cell(m.checks)} |")
        L.append("")
    return "\n".join(L)


def write():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")


def main():
    if "--write" in sys.argv:
        write()
        print(f"regenerated {OUT.relative_to(ROOT)}")
        return
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != render():
        raise SystemExit("SPEC-DOC: docs/protocols/specs.md does not match specs/*.toml; "
                         "run `make spec-doc`")
    print(f"spec-doc: docs/protocols/specs.md matches {len(SPEC_NAMES)} specifications")


if __name__ == "__main__":
    main()
