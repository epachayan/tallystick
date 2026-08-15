"""Validate local Markdown links and documentation reachability.

The repository has three intended entry points: README.md, START-HERE.md, and
INDEX.md. Every retained Markdown document must be reachable from at least one
of them, and every local link (including a heading fragment) must resolve.
External URLs are deliberately out of scope: this is a deterministic build
gate, not a network availability check.
"""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
ENTRY_POINTS = {ROOT / "README.md", ROOT / "START-HERE.md", ROOT / "INDEX.md"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "data"}


def markdown_files() -> set[Path]:
    return {
        path.resolve()
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts and ".pytest_cache" not in path.parts
    }


def heading_slugs(path: Path) -> set[str]:
    """Return GitHub-style heading slugs, including duplicate suffixes."""
    slugs: set[str] = set()
    seen: defaultdict[str, int] = defaultdict(int)
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        heading = match.group(1)
        heading = re.sub(r"!?(?:\[([^]]*)\])\([^)]+\)", r"\1", heading)
        heading = re.sub(r"[`*_~]", "", heading).strip().lower()
        base = "".join(
            char for char in heading
            if char.isalnum() or char in {" ", "-", "_"}
        ).replace(" ", "-")
        number = seen[base]
        seen[base] += 1
        slugs.add(base if number == 0 else f"{base}-{number}")
    return slugs


def local_destination(source: Path, destination: str) -> tuple[Path, str] | None:
    destination = destination.strip()
    if destination.startswith("<") and destination.endswith(">"):
        destination = destination[1:-1]
    # Optional Markdown link titles are not used for local repository links.
    parsed = urlsplit(destination)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or parsed.netloc:
        return None
    raw_path = unquote(parsed.path)
    if raw_path.startswith("/"):
        target = ROOT / raw_path.lstrip("/")
    elif raw_path:
        target = source.parent / raw_path
    else:
        target = source
    return target.resolve(), unquote(parsed.fragment)


def main() -> None:
    documents = markdown_files()
    errors: list[str] = []
    graph: defaultdict[Path, set[Path]] = defaultdict(set)
    local_links = 0

    missing_entries = ENTRY_POINTS - documents
    for path in sorted(missing_entries):
        errors.append(f"missing entry point: {path.relative_to(ROOT)}")

    anchors: dict[Path, set[str]] = {}
    for source in sorted(documents):
        text = source.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            resolved = local_destination(source, match.group(1))
            if resolved is None:
                continue
            local_links += 1
            target, fragment = resolved
            display_source = source.relative_to(ROOT)
            if not target.exists():
                errors.append(
                    f"{display_source}: missing target {match.group(1)!r}"
                )
                continue
            if target in documents:
                graph[source].add(target)
            if fragment and target.suffix.lower() == ".md":
                target_anchors = anchors.setdefault(target, heading_slugs(target))
                if fragment.lower() not in target_anchors:
                    errors.append(
                        f"{display_source}: missing heading #{fragment} in "
                        f"{target.relative_to(ROOT)}"
                    )

    reached: set[Path] = set()
    queue = deque(ENTRY_POINTS & documents)
    while queue:
        source = queue.popleft()
        if source in reached:
            continue
        reached.add(source)
        queue.extend(graph[source] - reached)

    for path in sorted(documents - reached):
        errors.append(f"unreachable Markdown document: {path.relative_to(ROOT)}")

    if errors:
        detail = "\n".join(f"  - {error}" for error in errors)
        raise SystemExit(f"LINKS: {len(errors)} error(s)\n{detail}")

    print(
        f"links: {len(documents)} Markdown files, {local_links} local links; "
        "all targets and headings resolve, all documents reachable"
    )


if __name__ == "__main__":
    main()
