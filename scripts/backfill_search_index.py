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
from graphql_api.data.backfill import (
    STORES,
    BackfillStats,
    iter_dynamo_documents,
    iter_legacy_documents,
    run_backfill,
)

log = logging.getLogger("backfill")


def _parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stage", required=True, help="deployment stage, e.g. prod (tables are Toshi*Object-<STAGE>)")
    p.add_argument("--region", default="ap-southeast-2")
    p.add_argument("--source", choices=["all", "dynamo", "legacy"], default="all")
    p.add_argument("--store", choices=STORES, action="append", help="limit to a store; repeatable (default: all)")
    p.add_argument("--bucket", help="legacy S3 bucket (default: nzshm22-toshi-api-<stage>)")
    p.add_argument("--since", help="only documents created on/after this ISO date (undated documents are kept)")
    p.add_argument("--clazz", action="append", help="only this clazz_name; repeatable")
    p.add_argument(
        "--min-id",
        type=int,
        help="only ids at or above this number. Ids come from one shared counter, so this selects "
        "recently created objects — the only way to narrow File objects, which have no `created` date.",
    )
    p.add_argument("--endpoint", help="Elasticsearch domain URL (required with --execute)")
    p.add_argument("--index", default="toshi_index_mapped")
    p.add_argument("--batch-size", type=int, default=500)
    p.add_argument("--max-batch-bytes", type=int, default=5_000_000, help="split _bulk requests above this size")
    p.add_argument("--limit", type=int, help="stop after this many documents (use for a quick probe run)")
    p.add_argument(
        "--max-failures", type=int, default=1000, help="stop once this many documents are rejected (0 = never)"
    )
    p.add_argument("--failures-file", default="backfill-failures.jsonl")
    p.add_argument("--execute", action="store_true", help="write to Elasticsearch (default: dry run)")
    p.add_argument(
        "--index-counts",
        action="store_true",
        help="print the index's document count per clazz_name and exit (read-only; needs --endpoint)",
    )
    args = p.parse_args(argv)
    if args.execute and not args.endpoint:
        p.error("--execute requires --endpoint")
    if args.index_counts and not args.endpoint:
        p.error("--index-counts requires --endpoint")
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

    if args.index_counts:
        for clazz, n in sorted(search.count_by_clazz(args.endpoint, args.index).items()):
            print(f"{clazz:<40} {n:>10}")
        return 0

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

    def progress(stats, source, store):
        elapsed = max(time.monotonic() - started, 1)
        read = sum(stats.seen.values()) + stats.skipped_before_since
        log.info(
            "%s %s: read=%d (%.0f/s) kept=%d indexed=%d failed=%d",
            source,
            store,
            read,
            read / elapsed,
            sum(stats.seen.values()),
            stats.indexed,
            len(stats.failed),
        )

    stats = BackfillStats()
    try:
        run_backfill(
            sources,
            endpoint=args.endpoint,
            index=args.index,
            since=args.since,
            clazz=set(args.clazz) if args.clazz else None,
            min_id=args.min_id,
            batch_size=args.batch_size,
            max_batch_bytes=args.max_batch_bytes,
            limit=args.limit,
            max_failures=args.max_failures or None,
            execute=args.execute,
            on_progress=progress,
            stats=stats,
        )
    finally:
        # stats is ours, so failures survive an abort — they are the only record
        # of why documents were rejected.
        if stats.failed:
            with open(args.failures_file, "w") as f:
                for key, reason in stats.failed:
                    f.write(json.dumps({"_id": key, "error": reason}) + "\n")
            log.error("%d failures written to %s", len(stats.failed), args.failures_file)

    print("\nsource  store  clazz_name                          count")
    for (source, store, clazz), n in sorted(stats.seen.items()):
        print(f"{source:<7} {store:<6} {clazz:<35} {n:>8}")
    print(
        f"total: {sum(stats.seen.values())}   skipped (before --since): {stats.skipped_before_since}"
        f"   skipped (--clazz/--min-id): {stats.skipped_filtered}"
        f"   skipped (never indexed): {stats.skipped_not_indexed}"
        f"   skipped (no clazz_name): {stats.skipped_no_clazz}"
    )

    if args.execute:
        print(f"indexed: {stats.indexed}   failed: {len(stats.failed)}")
        if stats.failed:
            print(f"failures written to {args.failures_file}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
