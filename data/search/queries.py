"""Query utilities for OpenSearch — used when a cluster is available.

These wrap `opensearch-py` and return the SAME shape as `fuzzy_match`
(Match objects), so Role 1's pipeline is agnostic to whether the fuzzy
local fallback or the live cluster answers. Configuration can come from
environment variables (the SAM Lambda way):

    OPENSEARCH_HOST  (default: localhost)
    OPENSEARCH_PORT  (default: 9200)
    OPENSEARCH_USE_SSL / OPENSEARCH_VERIFY_CERTS  (for AWS OpenSearch Serverless /
                                                    Domain endpoints)
    OPENSEARCH_USERNAME / OPENSEARCH_PASSWORD

If no client can be constructed (e.g. missing `opensearch-py`), the functions
transparently fall back to `fuzzy_match`.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

from .fuzzy_match import Match, match_ingredient  # noqa: E402  (fallback)


class OpenSearchQueryError(RuntimeError):
    """Raised when a cluster is configured but unreachable for a query."""


def _client_available() -> bool:
    try:
        import opensearchpy  # noqa: F401
        return True
    except Exception:
        return False


_client = None


def get_client():
    """Lazily build an OpenSearch client from env config; None if unavailable."""
    global _client
    if _client is not None:
        return _client
    if not _client_available():
        logger.info("opensearch-py not installed — falling back to local fuzzy match")
        return None

    # No host configured means no cluster, not "try localhost". Defaulting to
    # localhost made every ontology miss in Lambda open a doomed TCP connection
    # and log a full traceback before falling back — 32 of them in a day — and
    # on a dev machine it silently queried whatever unrelated service happened
    # to be listening on 9200, returning matches from someone else's index.
    # Pointing at a real cluster is an explicit OPENSEARCH_HOST, which is what
    # data/seed/seed_opensearch.py already documents.
    host = os.getenv("OPENSEARCH_HOST")
    if not host:
        logger.debug("OPENSEARCH_HOST unset — using the local ontology only")
        return None

    port = int(os.getenv("OPENSEARCH_PORT", "9200"))
    use_ssl = os.getenv("OPENSEARCH_USE_SSL", "false").lower() in {"1", "true", "yes"}
    verify = os.getenv("OPENSEARCH_VERIFY_CERTS", "true").lower() in {"1", "true", "yes"}
    user = os.getenv("OPENSEARCH_USERNAME") or None
    password = os.getenv("OPENSEARCH_PASSWORD") or None

    from opensearchpy import OpenSearch

    kwargs = {
        "hosts": [{"host": host, "port": port}],
        "timeout": 5,
        "use_ssl": use_ssl,
        "verify_certs": verify,
    }
    if user:
        kwargs["http_auth"] = (user, password)

    _client = OpenSearch(**kwargs)
    return _client


def _build_query(index: str, keyword: str, size: int = 5) -> dict:
    """Multi-field fuzzy query against the ingredient-friendly analyzer."""
    return {
        "size": size,
        "query": {
            "multi_match": {
                "query": keyword,
                "fields": ["*", "aliases^1.5", "name^2", "term"],
                "fuzziness": "AUTO",
                "operator": "or",
            }
        },
    }


def search_additives(keyword: str, size: int = 5) -> list[Match]:
    """Search E-numbers & additives index."""
    return _run_query("additives", keyword, size)


def search_allergens(keyword: str, size: int = 5) -> list[Match]:
    """Search allergen synonym ontology index."""
    return _run_query("allergens", keyword, size)


def search_descriptions(keyword: str, size: int = 5) -> list[Match]:
    """Search tap-to-explain descriptions index."""
    return _run_query("descriptions", keyword, size)


def search_cross_reactivity(keyword: str, size: int = 3) -> list[Match]:
    """Search cross-reactivity trigger table."""
    return _run_query("cross_reactivity", keyword, size)


def _run_query(index: str, keyword: str, size: int) -> list[Match]:
    client = get_client()
    if client is None:
        return match_ingredient(keyword)  # deterministic fallback

    try:
        resp = client.search(index=index, body=_build_query(index, keyword, size))
        hits = resp.get("hits", {}).get("hits") or []
        out = []
        for hit in hits:
            src = hit.get("_source", {})
            out.append(Match(
                ingredient=keyword,
                matched_allergen=src.get("name") or src.get("canonical_name") or src.get("trigger") or hit.get("_id", keyword),
                allergen_id=src.get("additive_id") or src.get("allergen_id") or src.get("ingredient_id") or src.get("reaction_id") or hit.get("_id", keyword),
                match_type=index,
                confidence=float(hit.get("_score", 0) or 0),
                explanation=src.get("plain_explanation") or src.get("manifestation") or src.get("reason", ""),
                source_note=f"opensearch:{index}",
                data=src,
            ))
        return out
    except Exception as exc:  # pragma: no cover — network/cluster failure
        logger.warning("OpenSearch query failed (%s); falling back to fuzzy match", exc)
        return match_ingredient(keyword)


def enrich_ingredient(ingredient: str) -> dict:
    """One-stop enrich: allergen match + additive + description + cross-reaction.

    This is the utility Role 1 / the backend calls per ingredient token to get
    all fetchable context in a single call (single round-trip per token).

    The local ontology answers FIRST and its answer is authoritative. It carries
    the hard-negatives and the 0.88 fuzzy floor, and those exist for a reason:
    at 0.82 "calcium carbonate" scored 0.824 against "calcium caseinate", which
    flagged chalk as milk and marked an oat drink UNSAFE for a dairy allergy.
    An OpenSearch `fuzziness: AUTO` query is exactly the looser matching that
    produced that bug, so it is never allowed to overrule a local hit.

    OpenSearch is consulted only when local resolution finds NOTHING — a typo,
    a trade name, a spelling nobody curated. That is the case its fuzziness is
    genuinely good at, and the one case where a loose hit cannot override a
    precise one because there is no precise one. Returns `source` so the caller
    can say which backend answered rather than guessing.
    """
    matches = match_ingredient(ingredient)  # local KB resolution
    source = "local"

    if not matches:
        # _run_query falls back to match_ingredient() when no cluster answers,
        # so keep only hits that genuinely came back from OpenSearch — that way
        # `source` never claims a cluster that was not actually reached.
        rescued = [m for m in search_descriptions(ingredient)
                   if m.source_note.startswith("opensearch:")]
        if rescued:
            matches, source = rescued, "opensearch"

    return {
        "ingredient": ingredient,
        "matches": [m.to_dict() for m in matches],
        "source": source,
    }