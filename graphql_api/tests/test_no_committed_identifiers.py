"""
Guard against committing AWS identifiers to this public repository (#386).

`scripts/capture_search_state.sh` writes AWS CLI output verbatim into docs/, and
the first capture published the account ID, the domain endpoint hostnames and the
source IP in the domain's access policy. The script redacts those now; this fails
the build if a raw one reaches the tree anyway.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]

# 12 consecutive digits: an AWS account ID. Dates/counts in prose are shorter.
ACCOUNT_ID = re.compile(r"(?<!\d)\d{12}(?!\d)")
# A reachable domain/collection endpoint: name + the random suffix AWS assigns.
ES_ENDPOINT = re.compile(r"[a-z0-9-]+-[a-z0-9]{26}\.[a-z0-9-]+\.es\.amazonaws\.com")
AOSS_ENDPOINT = re.compile(r"\b[a-z0-9]{20,}\.[a-z0-9-]+\.aoss\.amazonaws\.com")
# Public IPv4. Private/loopback ranges are fine: they identify nothing.
IPV4 = re.compile(r"(?<![\d.])(?!10\.|127\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")

PATTERNS = {
    "AWS account ID": ACCOUNT_ID,
    "Elasticsearch domain endpoint": ES_ENDPOINT,
    "OpenSearch Serverless endpoint": AOSS_ENDPOINT,
    "public IP address": IPV4,
}

TRACKED_DOCS = sorted(REPO.glob("docs/**/*.md")) + [REPO / "README.md", REPO / "CLAUDE.md"]


@pytest.mark.parametrize("path", TRACKED_DOCS, ids=lambda p: str(p.relative_to(REPO)))
def test_no_aws_identifiers_in_committed_docs(path):
    hits = []
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        for label, pattern in PATTERNS.items():
            for match in pattern.findall(line):
                hits.append(f"{path.relative_to(REPO)}:{lineno} {label}: {match}")
    assert not hits, "unredacted AWS identifiers (see #386):\n" + "\n".join(hits[:20])
