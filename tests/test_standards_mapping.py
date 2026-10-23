"""Standards mapping study (docs/standards/): keep it honest and in step with the code.

The study is deliberately unscored. These tests pin three things:
the manifests stay well-formed and revision-pinned, none of them is wired in as a
scored protocol, and the plain-language case index agrees with the generator it
describes (a hand-maintained table is recomputed against the code, not trusted).
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from src.multihop.generator import H_CLASSES, MISTAKE
from src.multihop.protocols import PROTOCOLS3
from src.multihop.spec import SPEC_NAMES

ROOT = Path(__file__).resolve().parents[1]
STANDARDS = ROOT / "docs" / "standards"
MANIFESTS = sorted((STANDARDS / "mappings").glob("*.toml"))
OBJECTS = {"G", "S", "X", "R"}


def _load(path):
    with path.open("rb") as fh:
        return tomllib.load(fh)


def test_manifests_exist():
    assert MANIFESTS, "docs/standards/mappings/ has no manifests"


@pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: p.name)
def test_manifest_is_pinned_unscored_and_partitions_objects(path):
    data = _load(path)
    draft, mapping = data["draft"], data["mapping"]

    # Revision-pinned: the id names a numbered revision and the URL points at exactly it.
    assert re.fullmatch(r"draft-[a-z0-9-]+-\d{2}", draft["id"]), draft["id"]
    assert draft["url"] == f"https://datatracker.ietf.org/doc/html/{draft['id']}"
    assert draft["kind"] == "individual-internet-draft"

    # Unscored by construction: only the two pre-scoring statuses exist.
    assert mapping["status"] in ("blocked", "partial-blocked")
    assert mapping["required_extensions"], "an unscored mapping must say what blocks it"

    # Every committed object is either projected or explicitly unmodelled, never both.
    projected, unmodelled = set(mapping["projected_objects"]), set(mapping["unmodelled_objects"])
    assert projected | unmodelled == OBJECTS
    assert not projected & unmodelled

    assert data["artifact"], "a mapping must declare at least one artifact shape"
    for art in data["artifact"]:
        assert art["name"] and art["actor"] and art["binds"]


def test_no_manifest_is_wired_in_as_a_scored_protocol():
    """A manifest must not leak into the scored harness by name or by file."""
    registered = set(SPEC_NAMES) | set(PROTOCOLS3)
    spec_files = {p.stem for p in (ROOT / "specs").glob("*.toml")}
    for path in MANIFESTS:
        draft_id = _load(path)["draft"]["id"]
        for name in (path.stem, draft_id):
            assert name not in registered, f"{name} is registered as a scored protocol"
            assert name not in spec_files, f"{name} has an executable spec in specs/"


def _case_rows():
    text = (STANDARDS / "case-index.md").read_text(encoding="utf-8")
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and re.fullmatch(r"H\d", cells[0]):
            rows[cells[0]] = cells
    return rows


def _parties(cell):
    return set() if cell == "None" else set(re.split(r"\s+and\s+", cell))


def test_case_index_lists_every_class_once():
    assert set(_case_rows()) == set(H_CLASSES)


def test_case_index_divergence_matches_generator():
    """The 'Accounts that diverge' column is D(w) as the generator declares it."""
    for h, cells in _case_rows().items():
        assert _parties(cells[2]) == set(H_CLASSES[h][1]), h


def test_case_index_mistakes_match_generator():
    """'Yes (X)' exactly where the generator marks X's divergence as a mistake."""
    for h, cells in _case_rows().items():
        expected = f"Yes ({MISTAKE[h]})" if h in MISTAKE else "No"
        assert cells[3] == expected, h
