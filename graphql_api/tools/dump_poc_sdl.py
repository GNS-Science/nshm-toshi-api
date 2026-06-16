"""Dump the Strawberry POC SDL to stdout.

Usage (from spike/strawberry_poc/):
    uv run python tools/dump_poc_sdl.py > poc.sdl
"""

import sys
from pathlib import Path

# Make spike/strawberry_poc/ importable when invoked as `python tools/dump_poc_sdl.py`
# from the spike root. pytest config does this via pythonpath but a bare python
# call doesn't pick that up.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graphql_api.schema import schema  # noqa: E402


def main() -> int:
    sys.stdout.write(schema.as_str())
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
