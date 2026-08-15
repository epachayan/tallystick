"""Structural validation: is this a well-formed scenario?

Separated from semantic coherence on purpose (finding, section 6). JSON Schema
answers "is the shape right"; coherence.py answers "is this world possible".
Conflating them is how the v0.1 schema drifted two versions behind the corpus
without anything failing.

Falls back to a hand-rolled walker when `jsonschema` is unavailable, so the
correctness gate never silently skips.
"""

from __future__ import annotations

import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "scenario.v0.2.schema.json"


def load_schema() -> dict:
    with open(SCHEMA_PATH) as fh:
        return json.load(fh)


def validate_corpus(scenarios) -> list[str]:
    schema = load_schema()
    try:
        import jsonschema
    except ImportError:
        return _fallback(scenarios, schema)

    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for sc in scenarios:
        for err in validator.iter_errors(sc):
            errors.append(f"{sc.get('scenario_id', '?')}: "
                          f"{'/'.join(str(p) for p in err.absolute_path)}: {err.message}")
    return errors


def _fallback(scenarios, schema) -> list[str]:
    """Minimal structural walk: required keys, no extra keys, enum membership.
    Not a substitute for jsonschema, but enough that the gate is never a no-op."""
    errors: list[str] = []

    def walk(obj, spec, path, sid):
        req = spec.get("required", [])
        for k in req:
            if k not in obj:
                errors.append(f"{sid}: {path}: missing required key {k!r}")
        if spec.get("additionalProperties") is False:
            allowed = set(spec.get("properties", {}))
            for k in obj:
                if k not in allowed:
                    errors.append(f"{sid}: {path}: unexpected key {k!r}")
        for k, sub in spec.get("properties", {}).items():
            if k not in obj:
                continue
            val = obj[k]
            if "const" in sub and val != sub["const"]:
                errors.append(f"{sid}: {path}/{k}: expected {sub['const']!r}, got {val!r}")
            if "enum" in sub and val not in sub["enum"]:
                errors.append(f"{sid}: {path}/{k}: {val!r} not in enum")
            if sub.get("type") == "object" and isinstance(val, dict):
                walk(val, sub, f"{path}/{k}", sid)
            if "$ref" in sub and isinstance(val, dict):
                ref = schema["$defs"][sub["$ref"].split("/")[-1]]
                walk(val, ref, f"{path}/{k}", sid)

    for sc in scenarios:
        walk(sc, schema, "", sc.get("scenario_id", "?"))
    return errors


def main():
    from ..reporting.harness import load_corpus

    scs = load_corpus()
    errs = validate_corpus(scs)
    if errs:
        for e in errs[:40]:
            print(e)
        raise SystemExit(f"SCHEMA: {len(errs)} error(s) across {len(scs)} scenarios")
    print(f"schema: {len(scs)} scenarios valid against scenario.v0.2.schema.json")


if __name__ == "__main__":
    main()
