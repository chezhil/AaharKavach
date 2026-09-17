"""Role 2 → Role 1/3 integration facade.

This is the contract other roles import. It hides the layering
(client ↔ confidence ↔ fuzzy/OpenSearch query ↔ suggestions) behind four
stable functions, so when Role 3's Lambda or Role 1's Strands agent calls in,
they don't have to know about OpenSearch, OFF or the confidence scorer.

All functions are network-optional: the ontology matching is 100% local;
only OFF product enrichment and alternative suggestions touch the network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .client.openfoodfacts import OpenFoodFactsClient, ProductRecord, OffApiError, OffProductNotFound
from .client.confidence import score_record, data_quality_note, ConfidenceResult
from .search.fuzzy_match import Match, match_ingredient, match_ingredients
from .search.queries import enrich_ingredient
from .alternative.suggestions import Suggestion, suggest_alternatives


@dataclass
class ScanContext:
    """Complete resolve for one barcode — consumed by Role 1's agent.

    contract:
      - product_record:  normalised OFF product
      - confidence:      HIGH | MEDIUM | LOW
      - confidence_reason: one-line data-quality note
      - ingredient_matches: { ingredient_token: [Match.to_dict(), ...] }
    """

    product: ProductRecord
    confidence: ConfidenceResult
    ingredient_matches: dict[str, list[dict]] = field(default_factory=dict)
    data_quality: str = ""

    @classmethod
    def build(cls, product: ProductRecord, conf: ConfidenceResult,
              matches: dict[str, list[Match]]) -> "ScanContext":
        return cls(
            product=product,
            confidence=conf,
            ingredient_matches={token: [m.to_dict() for m in ms] for token, ms in matches.items()},
            data_quality=data_quality_note(conf),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product.to_dict(),
            "confidence": self.confidence.to_dict(),
            "data_quality": self.data_quality,
            "ingredient_matches": self.ingredient_matches,
        }


def scan_barcode(
    barcode: str,
    client: OpenFoodFactsClient | None = None,
    enrich: bool = True,
) -> ScanContext:
    """End-to-end: fetch barcode → normalise → confidence → KB enrichment.

    Raises OffApiError for network / server failures (backend's job to map to
    a 503); never raises for a missing product — returns a ScanContext with
    product.is_found=False and LOW confidence.
    """
    client = client or OpenFoodFactsClient()
    product = client.get_product(str(barcode))

    conf = score_record(product)
    matches: dict[str, list[Match]] = {}
    if enrich and product.ingredients:
        matches = match_ingredients(product.ingredients)

    return ScanContext.build(product, conf, matches)


def resolve_ingredient(token: str) -> dict:
    """Local-only enrichment for one ingredient token (tap-to-explain / checks)."""
    return enrich_ingredient(token)


def suggest_safe_products(
    context: ScanContext,
    allergen_ids: list[str],
    max_results: int = 3,
    client: OpenFoodFactsClient | None = None,
) -> list[dict]:
    """Safe alternatives for a scan — maps Suggestion objects to dicts."""
    suggestions = suggest_alternatives(context.product, allergen_ids, max_results, client)
    return [s.to_dict() for s in suggestions]


def compare_products(barcode_a: str, barcode_b: str, client=None):
    """Compare two barcodes → two fully-resolved ScanContexts (compare suite).

    Role 1 uses the two contexts to generate its side-by-side summary; Role 3
    just forwards these to the frontend unchanged.
    """
    client = client or OpenFoodFactsClient()
    ctx_a = scan_barcode(barcode_a, client)
    ctx_b = scan_barcode(barcode_b, client)
    return {"product_a": ctx_a.to_dict(), "product_b": ctx_b.to_dict()}


__all__ = [
    "ScanContext",
    "scan_barcode",
    "resolve_ingredient",
    "suggest_safe_products",
    "compare_products",
    "Match",
    "ProductRecord",
    "OffApiError",
    "OffProductNotFound",
]