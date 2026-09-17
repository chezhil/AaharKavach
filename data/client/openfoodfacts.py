"""Open Food Facts REST client for barcode lookup.

Endpoints used:
  - GET /api/v2/product/{barcode}.json   — single product by barcode
  - GET /api/v2/search                    — search products (used for
                                            alternative suggestions)

The client normalises raw OFF payloads into a compact, typed ProductRecord
suitable for Role 1 and for the confidence scorer. Fallback handling:
  - 204 / 404 / "product": null  -> ProductRecord.not_found
  - Missing ingredient list      -> flagged, keeps alpha pair for label-photo
                                    fallback downstream
  - Throttled / network errors   -> raises OffApiError so the Lambda layer
                                    can return a friendly 503
"""

from __future__ import annotations

import json
import logging
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import Any

import requests

logger = logging.getLogger(__name__)

OFF_BASE_URL = "https://world.openfoodfacts.org"


class OffApiError(Exception):
    """Raised on network failure or persistent server error."""


class OffProductNotFound(LookupError):
    """Raised when a barcode is valid but no product exists."""


@dataclass
class ProductRecord:
    """Normalised product envelope that Role 1 / the API layer will consume.

    All fields are optional so we can model thin records cleanly. `confidence`
    is populated by :func:`data.client.confidence.score_record`.
    """

    barcode: str = ""
    product_name: str | None = None
    brands: str | None = None
    categories: list[str] = field(default_factory=list)
    ingredients: list[str] = field(default_factory=list)
    ingredients_raw: str | None = None
    allergens: list[str] = field(default_factory=list)
    vitamins: list[str] = field(default_factory=list)
    additives_tags: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    image_url: str | None = None
    nutrition_grade: str | None = None
    nutriscore: str | None = None
    nova_group: int | None = None
    ecoscore: str | None = None
    countries: list[str] = field(default_factory=list)
    off_status: int | None = None
    off_status_verbose: str | None = None
    source: str = "open_food_facts"
    confidence: str = "UNKNOWN"  # HIGH | MEDIUM | LOW — set by scorer
    is_found: bool = True

    @classmethod
    def not_found(cls, barcode: str) -> "ProductRecord":
        return cls(barcode=barcode, product_name=None, is_found=False, confidence="LOW")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_list(raw: Any) -> list[str]:
    """Flatten OFF lists (list of dicts or list of strings) into a string list."""
    if not raw:
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            val = item.get("id") or item.get("text") or item.get("name")
            if val:
                out.append(str(val))
        elif isinstance(item, str):
            out.append(item)
    return out


def _parse_ingredients(raw: Any) -> tuple[list[str], str | None]:
    """Parse `ingredients` (list of dicts) → flat token list + raw text."""
    if not raw:
        return [], None
    parsed: list[str] = []
    raw_text = None
    for item in raw:
        text = (item or {}).get("text")
        if text:
            parsed.append(str(text))
            continue
        raw_text = raw_text or (item or {}).get("raw", "")
    return [p.lower() for p in parsed], raw_text or None


def _looks_like_barcode(value: str) -> bool:
    return value.isdigit() and 8 <= len(value) <= 14


class OpenFoodFactsClient:
    """Thin, dependency-injected client (good for unit tests with a fake)."""

    def __init__(self, base_url: str = OFF_BASE_URL, session: requests.Session | None = None, timeout: float = 10.0, user_agent: str = "AaharKavach/0.1 (food-safety research project)"):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def get_product(self, barcode: str) -> ProductRecord:
        """Fetch a single product by barcode. Returns .not_found() gracefully."""
        barcode = str(barcode).strip()
        if not barcode:
            raise OffApiError("barcode cannot be empty")
        if not _looks_like_barcode(barcode):
            logger.warning("barcode %r does not look like a barcode; attempting anyway", barcode)

        url = f"{self.base_url}/api/v2/product/{urllib.parse.quote(barcode)}.json"
        try:
            resp = self.session.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise OffApiError(f"network error contacting Open Food Facts: {exc}") from exc

        if resp.status_code == 204:
            return ProductRecord.not_found(barcode)
        if resp.status_code == 404:
            return ProductRecord.not_found(barcode)
        if resp.status_code == 429:
            raise OffApiError("Open Food Facts rate limit hit — try again shortly")
        if resp.status_code >= 500:
            raise OffApiError("Open Food Facts server error")

        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            raise OffApiError(f"malformed response from Open Food Facts: {exc}") from exc

        product = payload.get("product")
        if not product:
            return ProductRecord.not_found(barcode)

        return self._normalise(barcode, product, payload.get("status", 1), payload.get("status_verbose", "found"))

    def search_products(self, query: str, category: str | None = None, page_size: int = 5) -> list[ProductRecord]:
        """Keyword search used for safe-alternative suggestions."""
        params: dict[str, Any] = {"search_terms": query, "page_size": page_size, "fields": json.dumps(
            ["code", "product_name", "brands", "categories", "ingredients_text", "allergens_tags", "image_url", "nutrition_grades_tags", "nova_groups_tags"]
        )}
        if category:
            params["tagtype_0"] = "categories"
            params["tag_contains_0"] = "contains"
            params["tag_0"] = category

        url = f"{self.base_url}/api/v2/search"
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise OffApiError(f"network error during search: {exc}") from exc

        if resp.status_code != 200:
            raise OffApiError(f"search failed with HTTP {resp.status_code}")

        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            raise OffApiError(f"malformed search response: {exc}") from exc

        records: list[ProductRecord] = []
        for hit in (payload.get("products") or []):
            code = hit.get("code") or ""
            if not code:
                continue
            records.append(self._normalise(code, hit, 1, "found"))
        return records

    # ------------------------------------------------------------------ #
    # Normalisation                                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _normalise(barcode: str, product: dict[str, Any], status: int, status_verbose: str) -> ProductRecord:
        ingredients, raw_text = _parse_ingredients(product.get("ingredients"))
        raw_text = raw_text or product.get("ingredients_text")

        # OFF uses tags like "en:milk", "en:soybeans"; strip prefix and join.
        def strip_lang(tags: Any) -> list[str]:
            cleaned = []
            for t in _clean_list(tags):
                cleaned.append(t.split(":", 1)[-1].replace("_", " ") if ":" in t else t.replace("_", " "))
            return cleaned

        def first_tag(tags: Any) -> str | None:
            values = strip_lang(tags)
            return values[0] if values else None

        nova_group = None
        for tag in (product.get("nova_groups_tags") or []):
            parts = str(tag).split(":")
            if parts[-1].isdigit():
                nova_group = int(parts[-1])
                break
        if nova_group is None and isinstance(product.get("nova_group"), int):
            nova_group = product["nova_group"]

        nutrient_score = product.get("nutriscore_grade") \
            if isinstance(product.get("nutriscore_grade"), str) else None
        overall_score = product.get("ecoscore_grade") \
            if isinstance(product.get("ecoscore_grade"), str) else None

        return ProductRecord(
            barcode=barcode,
            product_name=product.get("product_name") or product.get("product_name_en"),
            brands=", ".join(_clean_list(product.get("brands_tags") or product.get("brands"))),
            categories=strip_lang(product.get("categories_tags") or product.get("categories")),
            ingredients=ingredients,
            ingredients_raw=raw_text,
            allergens=strip_lang(product.get("allergens_tags") or product.get("allergens")),
            vitamins=_clean_list(product.get("vitamins")),
            additives_tags=strip_lang(product.get("additives_tags") or product.get("additives")),
            labels=strip_lang(product.get("labels_tags") or product.get("labels")),
            image_url=product.get("image_front_url") or product.get("image_url"),
            nutrition_grade=nutrient_score,
            nutriscore=nutrient_score,
            nova_group=nova_group,
            ecoscore=overall_score,
            countries=strip_lang(product.get("countries_tags") or product.get("countries")),
            off_status=status,
            off_status_verbose=status_verbose,
            source="open_food_facts",
        )


# Module-level default instance for convenience (still injectable for tests).
default_client = OpenFoodFactsClient()


def get_product(barcode: str) -> ProductRecord:
    """Convenience wrapper using the default client."""
    return default_client.get_product(barcode)


def search_products(query: str, category: str | None = None, page_size: int = 5) -> list[ProductRecord]:
    """Convenience wrapper using the default client."""
    return default_client.search_products(query, category, page_size)