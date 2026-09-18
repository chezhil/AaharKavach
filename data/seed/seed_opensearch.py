#!/usr/bin/env python3
"""Seed OpenSearch with the AaharKavach curated knowledge base.

Run from the repo root:
    python -m data.seed.seed_opensearch               # local defaults
    OPENSEARCH_HOST=... python -m data.seed.seed_opensearch --delete

Flags:
    --host        override OpenSearch host  (env: OPENSEARCH_HOST)
    --port        override OpenSearch port  (env: OPENSEARCH_PORT)
    --delete      delete existing indices first
    --dry-run     just print the plan without touching the cluster

The script is idempotent: index creation is guarded, and documents are
bulk-indexed with explicit `_id` from `_doc_id` so re-running upserts.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_opensearch")

# Ensure `data` package importable when invoked as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.search.opensearch import INDEX_MAPPINGS  # noqa: E402
from data.seed.seed_data import (  # noqa: E402
    additive_documents,
    allergen_documents,
    cross_reactivity_documents,
    description_documents,
)

SOURCE_FUNCTIONS = {
    "additives": additive_documents,
    "allergens": allergen_documents,
    "cross_reactivity": cross_reactivity_documents,
    "descriptions": description_documents,
}


def ensure_index(client, index: str, dry_run: bool) -> None:
    if dry_run:
        logger.info("[dry] would ensure index %s", index)
        return
    if client.indices.exists(index=index):
        logger.info("index %s already exists — skipping creation", index)
        return
    client.indices.create(index=index, body=INDEX_MAPPINGS[index])
    logger.info("created index %s", index)


def delete_index(client, index: str, dry_run: bool) -> None:
    if dry_run:
        logger.info("[dry] would delete index %s", index)
        return
    if client.indices.exists(index=index):
        client.indices.delete(index=index)
        logger.info("deleted index %s", index)


def seed_index(client, index: str, docs: list[dict], dry_run: bool) -> int:
    if not docs:
        logger.warning("no documents for %s", index)
        return 0
    if dry_run:
        logger.info("[dry] would bulk-index %d docs into %s", len(docs), index)
        return 0

    from opensearchpy.helpers import bulk

    actions = [
        {
            "_index": index,
            "_id": doc["_doc_id"],
            "_source": {k: v for k, v in doc.items() if k != "_doc_id"},
        }
        for doc in docs
    ]
    success, _ = bulk(client, actions, refresh=True, raise_on_error=False)
    logger.info("indexed %d docs into %s (attempted %d)", success, index, len(docs))
    return success


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed AaharKavach OpenSearch indices")
    parser.add_argument("--host", default=os.getenv("OPENSEARCH_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("OPENSEARCH_PORT", "9200")))
    parser.add_argument("--delete", action="store_true", help="delete indices before seeding")
    parser.add_argument("--dry-run", action="store_true", help="plan only, touch nothing")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN — no changes will be made")

    try:
        from opensearchpy import OpenSearch
    except ImportError:
        logger.error(
            "opensearch-py is not installed. Install dependencies first:\n"
            "    pip install -r AaharKavach/data/requirements.txt\n"
            "Or use the local Docker setup (see data/README.md)."
        )
        sys.exit(1)

    client = OpenSearch(hosts=[{"host": args.host, "port": args.port}], timeout=10)
    if not client.ping():
        logger.error("Cannot reach OpenSearch at %s:%s — is the cluster running?", args.host, args.port)
        sys.exit(1)

    logger.info("connected to OpenSearch at %s:%s", args.host, args.port)

    for index in INDEX_MAPPINGS:
        if args.delete:
            delete_index(client, index, args.dry_run)
        ensure_index(client, index, args.dry_run)
        seed_index(client, index, SOURCE_FUNCTIONS[index](), args.dry_run)

    logger.info("seed complete")


if __name__ == "__main__":
    main()