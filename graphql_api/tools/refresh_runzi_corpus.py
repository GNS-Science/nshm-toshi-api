"""Re-snapshot the runzi GraphQL query corpus into a vendored fixture.

The vendored fixture lives at `tests/runzi_corpus_data.py` and is loaded
by `tests/test_runzi_query_corpus.py` to validate every runzi-embedded
query against POC's SDL.

Run this from the repo root or from anywhere — it locates the runzi
clone via `--runzi-path` (default: `../../MISC/nzshm-runzi`) and writes
the fixture in-place.

## Why a vendored snapshot rather than reading the live clone

A vendored snapshot keeps POC's CI green when the runzi clone isn't
on the runner. It also pins the corpus to a specific runzi commit so
we know exactly what we tested.

The trade-off is that the snapshot can drift from current runzi. The
intended cadence: re-run this script before each runzi release, and
file a runzi PR if the corpus surfaces a new POC parity gap (or vice
versa).

## Longer-term plan (Option 4 — see runzi#308)

The right home for "runzi queries validate against the toshi-api SDL"
is on the runzi side, like weka and kororaa do. Both clients keep
their own copy of `schema.graphql` and run codegen/validation against
it as part of their build. When runzi follows suit, this vendored
fixture + corpus test can be deleted entirely.

Usage:
    python tools/refresh_runzi_corpus.py
    python tools/refresh_runzi_corpus.py --runzi-path /path/to/nzshm-runzi
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import textwrap
from pathlib import Path


# Triple-quoted block whose first non-whitespace token is `query`,
# `mutation`, or `fragment`. Permissive on whitespace and the operation
# name so we catch runzi's typical `qry = '''mutation foo (…) {…}'''`.
_GQL_LITERAL = re.compile(
    r"'''(\s*(?:query|mutation|fragment)\b[^']*?)'''",
    re.DOTALL,
)


def _has_unresolved_placeholders(op: str) -> bool:
    """Runzi uses ###NAME## tokens that get string-substituted before send.

    The static extractor can't resolve them; drop those queries from the
    corpus so we test only the parts where the literal IS the real query.
    """
    return "###" in op or "##" in op


def extract(runzi_root: Path) -> list[tuple[str, str]]:
    """Walk runzi/automation/toshi_api/ and return (label, query) tuples."""
    pkg_root = runzi_root / "runzi" / "automation" / "toshi_api"
    if not pkg_root.is_dir():
        raise SystemExit(f"runzi toshi_api package not found at {pkg_root}")

    out: list[tuple[str, str]] = []
    for py in sorted(pkg_root.rglob("*.py")):
        text = py.read_text(encoding="utf-8")
        for m in _GQL_LITERAL.finditer(text):
            op = m.group(1).strip()
            if _has_unresolved_placeholders(op):
                continue
            first_line = op.splitlines()[0] if op else ""
            label = f"{py.relative_to(runzi_root)}::{first_line[:60]}"
            out.append((label, op))
    return out


def runzi_sha(runzi_root: Path) -> str | None:
    """Best-effort short SHA of the runzi clone, for the snapshot header."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=runzi_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def write_fixture(operations: list[tuple[str, str]], dest: Path, sha: str | None):
    """Emit a Python module the test can import."""
    header = f'''"""Vendored snapshot of runzi GraphQL queries.

DO NOT EDIT BY HAND. Regenerate with:

    python graphql_api/tools/refresh_runzi_corpus.py

Snapshot source: GNS-Science/nzshm-runzi at {sha or "(sha unknown)"}
Extracted from: runzi/automation/toshi_api/
Operations: {len(operations)} (placeholder-templated queries dropped)

This vendored copy exists to keep POC's CI gate honest while runzi
catches up on owning client-side schema validation itself. See
runzi#308 for the long-term plan.
"""

OPERATIONS = [
'''

    parts = [header]
    for label, query in operations:
        # Use ` ''' `-safe triple-quoted strings; runzi queries never contain
        # `"""` so emit with double-quote triplets.
        parts.append(f"    (\n")
        parts.append(f"        {label!r},\n")
        parts.append(f'        """\\\n')
        # Indent the query body by 8 spaces so the docstring is readable but
        # the query text itself is left-aligned for parse correctness.
        parts.append(textwrap.indent(query, ""))
        if not query.endswith("\n"):
            parts.append("\n")
        parts.append('""",\n')
        parts.append("    ),\n")
    parts.append("]\n")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {len(operations)} operations → {dest}")


def main(argv: list[str] | None = None) -> int:
    default_runzi = (Path(__file__).resolve().parents[3] / ".." / ".." / "MISC" / "nzshm-runzi").resolve()
    default_fixture = Path(__file__).resolve().parent.parent / "tests" / "runzi_corpus_data.py"

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runzi-path", type=Path, default=default_runzi, help="Path to runzi clone")
    parser.add_argument(
        "--out",
        type=Path,
        default=default_fixture,
        help="Output fixture path (default: tests/runzi_corpus_data.py)",
    )
    args = parser.parse_args(argv)

    if not args.runzi_path.is_dir():
        print(f"runzi path not found: {args.runzi_path}", file=sys.stderr)
        return 1

    operations = extract(args.runzi_path)
    sha = runzi_sha(args.runzi_path)
    write_fixture(operations, args.out, sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
