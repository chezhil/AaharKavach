"""Tools the Strands agent calls — now backed by Role 2 instead of mocks.

These were stubs returning empty dicts, which meant the agent reasoned over
nothing. They call Role 2's knowledge base in-process: under Lambda both roles
are packaged together, so there is no HTTP hop to make.
"""

from __future__ import annotations

from typing import Any

from data.search.fuzzy_match import match_ingredient


def lookup_ingredient_details(ingredient_name: str) -> dict[str, Any]:
    """Resolve one ingredient against the allergen ontology and additive index."""
    matches = match_ingredient(ingredient_name)
    return {
        "query": ingredient_name,
        "base_allergens": sorted(
            {m.allergen_id for m in matches if m.match_type in ("exact", "synonym", "fuzzy")}
        ),
        "additives": [
            {"id": m.allergen_id.removeprefix("e:"), "name": m.matched_allergen}
            for m in matches
            if m.match_type == "additive"
        ],
        "matches": [m.to_dict() for m in matches],
        "description": next((m.explanation for m in matches if m.explanation), ""),
    }
