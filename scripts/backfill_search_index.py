"""
Backfill the search index from DynamoDB and legacy S3 (#378, #230).

Dry run by default: scans the sources and prints what would be indexed, without
contacting Elasticsearch. Add --execute to write. Re-running is safe; each
object overwrites its own document.

    # 1. see the scope (read-only; needs DynamoDB + S3 read)
    uv run python scripts/backfill_search_index.py --stage prod

    # 2. write (needs es:ESHttpPost on the domain; requests are SigV4-signed)
    uv run python scripts/backfill_search_index.py --stage prod --execute \\
        --endpoint https://search-nzshm22-toshi-api-es-prod-....ap-southeast-2.es.amazonaws.com

    # only objects created since the indexing outage began (plus undated ones)
    uv run python scripts/backfill_search_index.py --stage prod --source dynamo --since 2026-06-12 --execute ...

Take a manual snapshot of the domain before the first --execute on prod.
"""

import argparse
import json
import logging
import os
import sys
import time

import boto3
import requests

from graphql_api.data import search
from graphql_api.data.backfill import STORES, iter_dynamo_documents, iter_legacy_documents, run_backfill

log = logging.getLogger("backfill")


def _parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stage", required=True, help="deployment stage, e.g. prod (tables are Toshi*Object-<STAGE>)")
    p.add_argument("--region", default="ap-southeast-2")
    p.add_argument("--source", choices=["all", "dynamo", "legacy"], default="all")
    p.add_argument("--store", choices=STORES, action="append", help="limit to a store; repeatable (default: all)")
    p.add_argument("--bucket", help="legacy S3 bucket (default: nzshm22-toshi-api-<stage>)")
    p.add_argument("--since", help="only documents created on/after this ISO date (undated documents are kept)")
    p.add_argument("--endpoint", help="Elasticsearch domain URL (required with --execute)")
    p.add_argument("--index", default="toshi_index_mapped")
    p.add_argument("--batch-size", type=int, default=500)
    p.add_argument("--failures-file", default="backfill-failures.jsonl")
    p.add_argument("--execute", action="store_true", help="write to Elasticsearch (default: dry run)")
    args = p.parse_args(argv)
    if args.execute and not args.endpoint:
        p.error("--execute requires --endpoint")
    return args


def _check_index_exists(endpoint: str, index: str) -> None:
    # Writing to a misspelt index would silently create a new, unmapped one
    # that weka never reads — the code default is "toshi-index-mapped", not
    # the live "toshi_index_mapped".
    resp = requests.head(f"{endpoint}/{index}", auth=search._auth_for(endpoint), timeout=30)
    if resp.status_code != 200:
        sys.exit(f"index {index!r} not found at {endpoint} (HTTP {resp.status_code}); refusing to create it")


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parse_args(argv)
    os.environ["ES_REGION"] = args.region  # read by search._aws_auth for signing
    stores = args.store or list(STORES)
    stage = args.stage.upper()  # matches dynamo.STAGE (DEPLOYMENT_STAGE.upper())
    bucket = args.bucket or f"nzshm22-toshi-api-{args.stage.lower()}"

    dynamodb = boto3.resource("dynamodb", region_name=args.region)
    s3 = boto3.client("s3", region_name=args.region)

    # Legacy first, so where an id is in both stores the DynamoDB copy is written last.
    sources = []
    if args.source in ("all", "legacy"):
        sources += [("legacy", st, iter_legacy_documents(s3, bucket, st)) for st in stores]
    if args.source in ("all", "dynamo"):
        sources += [("dynamo", st, iter_dynamo_documents(dynamodb, st, stage)) for st in stores]

    if args.execute:
        _check_index_exists(args.endpoint, args.index)
        log.info("writing to %s/%s", args.endpoint, args.index)
    else:
        log.info("DRY RUN — nothing will be written (add --execute)")

    started = time.monotonic()

    def progress(stats, last_key):
        rate = stats.indexed / max(time.monotonic() - started, 1)
        log.info("indexed=%d failed=%d (%.0f/s) last=%s", stats.indexed, len(stats.failed), rate, last_key)

    stats = run_backfill(
        sources,
        endpoint=args.endpoint,
        index=args.index,
        since=args.since,
        batch_size=args.batch_size,
        execute=args.execute,
        on_batch=progress,
    )

    print("\nsource  store  clazz_name                          count")
    for (source, store, clazz), n in sorted(stats.seen.items()):
        print(f"{source:<7} {store:<6} {clazz:<35} {n:>8}")
    print(f"total: {sum(stats.seen.values())}   skipped (before --since): {stats.skipped_before_since}")

    if args.execute:
        print(f"indexed: {stats.indexed}   failed: {len(stats.failed)}")
        if stats.failed:
            with open(args.failures_file, "w") as f:
                for key, reason in stats.failed:
                    f.write(json.dumps({"_id": key, "error": reason}) + "\n")
            print(f"failures written to {args.failures_file}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
