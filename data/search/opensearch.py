"""OpenSearch index definitions (index-name → mapping body).

These maps are used BOTH by the seed script (to create indices) and by the
query utilities (to know which field to query). The documents themselves come
from the curated modules in `data/mappings/` — see `data/seed/seed_opensearch.py`.

Index layout:
  - additives          : E-numbers/additives dictionary
  - allergens          : synonym ontology for allergens
  - cross_reactivity   : trigger→primary-allergy tables
  - descriptions       : 'what is this ingredient' tap-explainers

All indices share a text field with a custom analyzer for fuzzy, case-
insensitive matching (standard + lowercase + asciifolding).
"""

# Shared analyzer: keeps accents-normalised tokens so "café" matches "cafe",
# and everything lower-cased so queries are trivially case-insensitive.
COMMON_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "ingredient_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "_match_all": {"type": "text", "analyzer": "ingredient_analyzer"}
        }
    },
}


def _text_field(analyzer: str = "ingredient_analyzer") -> dict:
    return {"type": "text", "analyzer": analyzer, "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}}


ADDITIVES_INDEX = "additives"
ALLERGENS_INDEX = "allergens"
CROSS_REACTIVITY_INDEX = "cross_reactivity"
DESCRIPTIONS_INDEX = "descriptions"

ADDITIVES_MAPPING = {
    "settings": COMMON_MAPPING["settings"],
    "mappings": {"properties": {
        "additive_id": {"type": "keyword"},
        "name": _text_field(),
        "aliases": _text_field(),
        "is_derived_from": {"type": "keyword"},
        "derived_from": {"type": "object"},
        "allergen_tags": {"type": "keyword"},
        "risk_level": {"type": "keyword"},
        "top_uses": _text_field(),
        "vegan_vegetarian": _text_field(),
        "plain_explanation": _text_field(),
        "confidence_source": _text_field(),
    }},
}

ALLERGENS_MAPPING = {
    "settings": COMMON_MAPPING["settings"],
    "mappings": {"properties": {
        "allergen_id": {"type": "keyword"},
        "canonical_name": _text_field(),
        "category": {"type": "keyword"},
        "aliases": _text_field(),
        "synonym_terms": {"type": "nested", "properties": {
            "term": _text_field(),
            "confidence": {"type": "float"},
        }},
        "derived_from": {"type": "keyword"},
        "manifestation": _text_field(),
        "cross_reacts_with": {"type": "keyword"},
        "common_products": _text_field(),
        "label_phrases": _text_field(),
        "confidence_source": _text_field(),
    }},
}

CROSS_REACTIVITY_MAPPING = {
    "settings": COMMON_MAPPING["settings"],
    "mappings": {"properties": {
        "reaction_id": {"type": "keyword"},
        "trigger": _text_field(),
        "primary_allergy": {"type": "keyword"},
        "confidence": {"type": "float"},
        "category": {"type": "keyword"},
        "reason": _text_field(),
        "headline": _text_field(),
        "severity_bump": {"type": "keyword"},
    }},
}

DESCRIPTIONS_MAPPING = {
    "settings": COMMON_MAPPING["settings"],
    "mappings": {"properties": {
        "ingredient_id": {"type": "keyword"},
        "name": _text_field(),
        "aliases": _text_field(),
        "plain_explanation": _text_field(),
        "alternate_names": _text_field(),
        "tone": {"type": "keyword"},
        "category": {"type": "keyword"},
        "typical_role": _text_field(),
        "confidence_source": _text_field(),
    }},
}

INDEX_MAPPINGS = {
    ADDITIVES_INDEX: ADDITIVES_MAPPING,
    ALLERGENS_INDEX: ALLERGENS_MAPPING,
    CROSS_REACTIVITY_INDEX: CROSS_REACTIVITY_MAPPING,
    DESCRIPTIONS_INDEX: DESCRIPTIONS_MAPPING,
}