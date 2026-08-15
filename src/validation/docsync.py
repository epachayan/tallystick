"""Generated documentation, and a check that it has not drifted.

`docs/taxonomy.md` is the class list. It was hand-maintained, and a
hand-maintained class list is precisely the artifact that has carried six of
this project's defects. So it is generated from `M_CLASSES` and verified.

The rule this closes: a document that restates something the code already knows
must be generated from the code, not written alongside it. Prose that reasons
about the code is a different thing and stays hand-written -- but a table of
class names is not reasoning, it is a copy.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = ROOT / "docs" / "taxonomy.md"


def render_taxonomy() -> str:
    from ..generator import M_CLASSES

    rows = "\n".join(
        f"| {m} | {fam} | {liar} | {desc} |"
        for m, (fam, liar, desc) in sorted(M_CLASSES.items(),
                                           key=lambda kv: int(kv[0][1:]))
    )
    return f"""# Adversarial class taxonomy

**GENERATED from `src/generator.py::M_CLASSES` — do not hand-edit.**
Regenerate with `make taxonomy`. `make check` fails if this file drifts from the
code, because a hand-maintained taxonomy is exactly the artifact that has
carried six of this project's defects (see `RESEARCH.md` §9a).

{len(M_CLASSES)} classes, 25 instances each.

| class | family | dishonest | description |
|---|---|---|---|
{rows}

## Reading this table

`dishonest` names the party whose account is culpably false — `none` marks the
honest twins and controls, which exist so that a mechanism catching the
adversarial class can be checked for catching its innocent counterpart too.

Twin pairings are declared in `src/generator.py::TWIN_OF` and **verified** by
`src/validation/twins.py`; the declaration has been wrong before (F-H3), so the
audit is authoritative, not the list.

Which pairs admit an escape and which do not is derived in
`src/validation/conservation.py` — see `docs/findings/12-conservation-boundary.md`.
"""


def write_taxonomy() -> None:
    TAXONOMY.write_text(render_taxonomy(), encoding="utf-8")


def main():
    want = render_taxonomy()
    have = TAXONOMY.read_text(encoding="utf-8") if TAXONOMY.exists() else ""
    if want != have:
        raise SystemExit(
            "DOCSYNC: docs/taxonomy.md does not match src/generator.py::M_CLASSES. "
            "Run `make taxonomy`.")
    print(f"docsync: docs/taxonomy.md matches the code "
          f"({want.count('| M')} class rows)")


if __name__ == "__main__":
    main()
