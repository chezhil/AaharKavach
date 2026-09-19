"""Tests for Role 2 — knowledge base, confidence, OFF normalisation.

Run:  python -m pytest AaharKavach/data/tests/
"""

from __future__ import annotations

import pytest

from data.client.openfoodfacts import ProductRecord
from data.client.confidence import score_record, data_quality_note, HIGH, MEDIUM, LOW
from data.mappings.e_numbers import lookup_additive
from data.mappings.allergen_synonyms import resolve_synonym
from data.mappings.cross_reactivity import lookup_cross_reactivity
from data.search.fuzzy_match import match_ingredient


# --------------------------------------------------------------------------- #
# Allergen synonym resolution                                                 #
# --------------------------------------------------------------------------- #
class TestSynonymResolution:
    def test_caseinate_resolves_to_milk(self):
        entry = resolve_synonym("Sodium Caseinate")
        assert entry is not None
        assert entry["allergen_id"] == "milk"
        assert entry["matched_confidence"] == 1.0

    def test_ghee_resolves_to_milk(self):
        assert resolve_synonym("Ghee")["allergen_id"] == "milk"

    def test_mayonnaise_resolves_to_egg_with_reduced_confidence(self):
        entry = resolve_synonym("mayonnaise")
        assert entry is not None
        assert entry["allergen_id"] == "egg"
        assert entry["matched_confidence"] < 1.0

    def test_hard_negative_buckwheat_never_matches_gluten(self):
        matches = match_ingredient("buckwheat")
        matched_ids = {m.allergen_id for m in matches}
        assert "wheat_gluten" not in matched_ids

    def test_coconut_never_matches_tree_nuts(self):
        matches = match_ingredient("coconut")
        assert "tree_nuts" not in {m.allergen_id for m in matches}

    def test_pineapple_does_not_match_pine_nut(self):
        matches = match_ingredient("pineapple")
        assert "tree_nuts" not in {m.allergen_id for m in matches}


# --------------------------------------------------------------------------- #
# Additive E-number lookups                                                   #
# --------------------------------------------------------------------------- #
class TestAdditiveLookup:
    def test_e120_resolves_to_carmine(self):
        entry = lookup_additive("E120")
        assert entry is not None
        assert entry["name"] == "Carmine / Cochineal"
        assert "insect" in entry["is_derived_from"]

    def test_lookup_is_case_insensitive(self):
        assert lookup_additive("e322")["additive_id"] == "E322"
        assert lookup_additive("E322")["additive_id"] == "E322"

    def test_unknown_number_returns_none(self):
        assert lookup_additive("E999") is None


# --------------------------------------------------------------------------- #
# Cross-reactivity gating                                                     #
# --------------------------------------------------------------------------- #
class TestCrossReactivity:
    def test_latex_banana_mapping(self):
        rows = lookup_cross_reactivity("banana", "latex")
        assert rows and rows[0]["reaction_id"] == "latex_fruit_banana"

    def test_no_warning_without_primary_allergy(self):
        # If profile lists peanuts, banana should NOT warn.
        assert lookup_cross_reactivity("banana", "peanuts") == []

    def test_peanut_lupin_cross(self):
        rows = lookup_cross_reactivity("lupin", "peanuts")
        assert rows and rows[0]["severity_bump"] == "caution_and_monitor"


# --------------------------------------------------------------------------- #
# Confidence scoring                                                          #
# --------------------------------------------------------------------------- #
def _record(**overrides) -> ProductRecord:
    defaults = {
        "barcode": "1234567890123",
        "product_name": "Test Product",
        "brands": "TestBrand",
        "categories": ["snacks"],
        "ingredients": ["sugar", "palm oil", "cocoa", "milk powder"],
        "ingredients_raw": "sugar, palm oil, cocoa, milk powder",
        "allergens": ["milk"],
        "image_url": "https://fake/image.jpg",
        "off_status_verbose": "complete",
        "is_found": True,
        "confidence": "UNKNOWN",
    }
    defaults.update(overrides)
    return ProductRecord(**defaults)


class TestConfidenceScoring:
    def test_complete_record_scores_high(self):
        result = score_record(_record())
        assert result.level == HIGH

    def test_missing_ingredients_scores_low(self):
        result = score_record(_record(ingredients=[], ingredients_raw=None))
        assert result.level == LOW
        assert any("No ingredient list" in r for r in result.reasons)

    def test_partial_ingredients_scores_medium(self):
        result = score_record(_record(ingredients=["sugar"], ingredients_raw=None))
        assert result.level == MEDIUM

    def test_unverified_record_is_penalised(self):
        complete = score_record(_record(off_status_verbose="complete"))
        unverified = score_record(_record(off_status_verbose="to-be-completed"))
        assert unverified.score < complete.score

    def test_missing_allergen_tags_penalised(self):
        result = score_record(_record(allergens=[]))
        assert result.level in (MEDIUM, LOW)

    def test_not_found_always_low(self):
        result = score_record(ProductRecord.not_found("0000000000000"))
        assert result.level == LOW
        assert "not found" in data_quality_note(result).lower()


# --------------------------------------------------------------------------- #
# Open Food Facts normalisation                                               #
# --------------------------------------------------------------------------- #
class TestOffNormalisation:
    def test_normalise_full_payload(self):
        from data.client.openfoodfacts import OpenFoodFactsClient

        payload = {
            "code": "3017624010701",
            "product": {
                "product_name": "Nutella",
                "brands_tags": ["ferrero"],
                "categories_tags": ["en:spreads", "en:hazelnut-spreads"],
                "ingredients": [
                    {"text": "Sugar"}, {"text": "Palm Oil"}, {"text": "Hazelnuts"}
                ],
                "ingredients_text": "Sugar, Palm Oil, Hazelnuts",
                "allergens_tags": ["en:milk", "en:hazelnuts"],
                "additives_tags": ["en:e322i"],
                "image_front_url": "https://fake/img.jpg",
                "nova_groups_tags": ["en:4"],
                "status": 1,
                "status_verbose": "found",
            },
        }
        rec = OpenFoodFactsClient._normalise("3017624010701", payload["product"], 1, "found")
        assert rec.product_name == "Nutella"
        assert rec.ingredients == ["sugar", "palm oil", "hazelnuts"]
        assert rec.allergens == ["milk", "hazelnuts"]
        assert rec.nova_group == 4
        assert rec.additives_tags == ["e322i"]
        assert rec.is_found

    def test_normalise_missing_product_handling(self):
        from data.client.openfoodfacts import OpenFoodFactsClient

        # minimal payload — should not raise.
        rec = OpenFoodFactsClient._normalise("001", {"product_name": "X"}, 1, "found")
        assert rec.product_name == "X"
        assert rec.ingredients == []
        assert rec.brands == ""


# --------------------------------------------------------------------------- #
# services facade (network-free paths)                                        #
# --------------------------------------------------------------------------- #
class TestServicesFacade:
    def test_resolve_ingredient_shape(self):
        from data.services import resolve_ingredient

        result = resolve_ingredient("sodium caseinate")
        assert result["ingredient"] == "sodium caseinate"
        assert isinstance(result["matches"], list)
        assert result["matches"][0]["matched_allergen"] == "Milk / Dairy"

    def test_scan_barcode_with_fake_client(self):
        from data.services import scan_barcode

        class FakeClient:
            def get_product(self, barcode):
                return _record(barcode=barcode)

        ctx = scan_barcode("1234567890123", client=FakeClient())
        assert ctx.product.is_found is True
        assert ctx.confidence.level in (HIGH, MEDIUM, LOW)
        assert "sugar" in ctx.ingredient_matches
        assert ctx.data_quality

    def test_scan_missing_product_via_fake(self):
        from data.services import scan_barcode

        class NotFoundClient:
            def get_product(self, barcode):
                return ProductRecord.not_found(barcode)

        ctx = scan_barcode("0000000000000", client=NotFoundClient())
        assert ctx.product.is_found is False
        assert ctx.confidence.level == LOW

# --------------------------------------------------------------------------- #
# OpenSearch enrichment — local stays authoritative, the cluster only rescues  #
# --------------------------------------------------------------------------- #
class TestOpenSearchEnrichment:
    """These must pass with OR without a cluster running.

    The suite is the only thing standing between "OpenSearch answers the misses"
    and "OpenSearch quietly started answering the hits too" — which is how the
    0.88 fuzzy floor would get bypassed and chalk would read as milk again.
    """

    def test_source_is_reported(self):
        from data.services import resolve_ingredient

        assert resolve_ingredient("sodium caseinate")["source"] in ("local", "opensearch")

    def test_local_hit_is_never_overruled_by_the_cluster(self):
        from data.services import resolve_ingredient

        result = resolve_ingredient("sodium caseinate")
        assert result["source"] == "local"
        assert result["matches"][0]["matched_allergen"] == "Milk / Dairy"

    def test_hard_negative_survives_the_opensearch_path(self):
        """Cocoa butter is not dairy, and a fuzzy cluster hit must not make it so."""
        from data.services import resolve_ingredient

        result = resolve_ingredient("refined cocoa butter")
        assert not any(m["matched_allergen"] == "Milk / Dairy" for m in result["matches"])

    def test_unreachable_cluster_degrades_to_local(self, monkeypatch):
        from data.search import queries

        monkeypatch.setattr(queries, "_client", None)
        monkeypatch.setattr(queries, "get_client", lambda: None)

        result = queries.enrich_ingredient("sodium caseinate")
        assert result["source"] == "local"
        assert result["matches"], "local resolution must still answer with no cluster"

    def test_unknown_token_resolves_to_nothing_either_way(self):
        from data.services import resolve_ingredient

        result = resolve_ingredient("zzzznotanactualingredient")
        assert result["matches"] == []
        assert result["source"] == "local"
