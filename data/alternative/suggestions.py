"""Safe-alternative suggestions.

When Role 1 flags a product as unsafe for a profile, we suggest 1–3 similar
products from the same category that avoid the offending allergen(s).

Strategy:
  1. Take the flagged product's category (e.g. "milk-chocolates").
  2. Query Open Food Facts for the category + a keyword close to the product.
  3. Score candidates:
       - no forbidden allergens
       - ingredient coverage (prefer records with a parseable list)
       - preference for same brand family when available
       - penalise low-confidence records
  4. Return the top N ordered candidates.

Contract for Role 3 / frontend:
    [
      {
        "barcode": "890...",
        "product_name": "...",
        "brands": "...",
        "categories": [...],
        "image_url": "...",
        "confidence": "HIGH"|"MEDIUM"|"LOW",
        "reason": "No milk derivatives found in this alternative"
      }
    ]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..client.openfoodfacts import OpenFoodFactsClient, ProductRecord, OffApiError
from ..client.confidence import score_record, HIGH, MEDIUM, LOW


@dataclass
class Suggestion:
    barcode: str
    product_name: str | None
    brands: str | None
    categories: list[str] = field(default_factory=list)
    image_url: str | None = None
    confidence: str = LOW
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "barcode": self.barcode,
            "product_name": self.product_name,
            "brands": self.brands,
            "categories": self.categories[:3],
            "image_url": self.image_url,
            "confidence": self.confidence,
            "reason": self.reason,
        }


# Allergen terms we must NOT find in a candidate. Expanding this terminally
# lives in the allergen ontology, but suggestions run on raw OFF tags; a
# compact denylist gets us good first-pass results without over-engineering.
FORBIDDEN_TERMS = {
    "milk": {"milk", "milk-powder", "butterfat", "cream", "condensed-milk", "milk-solids"},
    "eggs": {"egg", "egg-white", "egg-yolk", "albumen"},
    "peanuts": {"peanut", "groundnut", "peanut-butter"},
    "tree_nuts": {"almond", "walnut", "cashew", "pistachio", "hazelnut", "pecan", "brazil-nut",
                  "macadamia", "pine-nut", "nut"},
    "soybeans": {"soy", "soya", "soybean", "soybeans", "soy-lecithin", "tofu", "soy-protein"},
    "wheat_gluten": {"wheat", "gluten", "durum", "spelt", "seitan", "wheat-flour", "semolina"},
    "fish": {"fish", "surimi", "anchovy", "salmon", "tuna", "cod"},
    "shellfish": {"crab", "shrimp", "prawn", "lobster", "shellfish", "crustacean", "molluscs"},
    "sulphites": {"sulphite", "sulfite", "sulphur-dioxide", "sulfur-dioxide", "metabisulphite"},
    "sesame": {"sesame", "sesame-seed", "tahini"},
    "mustard": {"mustard", "mustard-seed", "mustard-powder"},
    "celery": {"celery", "celeriac"},
    "lupin": {"lupin", "lupine"},
}


def _contains_forbidden(allergen_ids: list[str], record: ProductRecord) -> bool:
    """Whether a product record signals any of the given allergens."""
    forbidden = set()
    for allergen_id in allergen_ids:
        forbidden |= FORBIDDEN_TERMS.get(allergen_id, set())
    if not forbidden:
        return False

    haystack = set(record.allergens) | set(record.additives_tags) | set(record.labels)
    haystack |= {t.split(":")[-1] for t in haystack}
    haystack |= {t.replace("_", "-") for t in haystack}

    # Also scan parsed ingredients for the forbidden terms.
    for ing in record.ingredients:
        haystack |= set(ing.replace(" ", "-").split("-"))

    return bool(haystack & forbidden)


def _candidate_keywords(product: ProductRecord) -> list[str]:
    """Keywords used for the OFF search — prefer product family then category."""
    words = []
    if product.brands:
        words.append(product.brands.split(",")[0].strip())
    if product.product_name:
        words.append(product.product_name.split(",")[0].strip())
    return [w for w in words if w] or ["organic"]


def suggest_alternatives(
    product: ProductRecord,
    allergen_ids: list[str],
    max_results: int = 3,
    client: OpenFoodFactsClient | None = None,
) -> list[Suggestion]:
    """Return up to `max_results` safer alternatives for the given product."""
    client = client or OpenFoodFactsClient()
    results: list[Suggestion] = []

    if not product.categories:
        return results  # nothing to match against; don't guess

    primary_category = product.categories[0]
    keywords = _candidate_keywords(product)

    for kw in keywords:
        try:
            candidates = client.search_products(kw, category=primary_category, page_size=10)
        except OffApiError:
            continue

        for cand in candidates:
            # Never suggest the same barcode.
            if cand.barcode == product.barcode:
                continue
            if _contains_forbidden(allergen_ids, cand):
                continue

            conf = score_record(cand)
            reason = f"No {_display(allergen_ids)} found — ingredient list present ({len(cand.ingredients)} items)."
            if not cand.ingredients:
                reason = f"No {_display(allergen_ids)} found in allergen tags — but verify the label; ingredient list is thin."
            results.append(Suggestion(
                barcode=cand.barcode,
                product_name=cand.product_name,
                brands=cand.brands,
                categories=cand.categories,
                image_url=cand.image_url,
                confidence=conf.level,
                reason=reason,
            ))
            if len(results) >= max_results:
                return results

    return results


def _display(allergen_ids: list[str]) -> str:
    pretty = {
        "milk": "milk/dairy", "eggs": "eggs", "peanuts": "peanut",
        "tree_nuts": "tree nuts", "soybeans": "soy", "wheat_gluten": "wheat/gluten",
        "fish": "fish", "shellfish": "shellfish", "sulphites": "sulphites",
        "sesame": "sesame", "mustard": "mustard", "celery": "celery", "lupin": "lupin",
    }
    return ", ".join(pretty.get(a, a) for a in allergen_ids)