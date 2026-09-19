"""Assemble the curated domain knowledge into plain lists of documents.

Loads from the mapping modules so there is ONE source of truth for the data
(Role 1's local resolution + the OpenSearch seed + tests all read the same
files).
"""

from __future__ import annotations

from ..mappings.e_numbers import E_NUMBERS
from ..mappings.allergen_synonyms import ALLERGENS
from ..mappings.cross_reactivity import CROSS_REACTIVITY_TABLE
from ..mappings.descriptions import DESCRIPTIONS

# Each function returns a list of dicts ready to bulk-index.

def additive_documents() -> list[dict]:
    docs = []
    for row in E_NUMBERS:
        # Copy before adding _doc_id: E_NUMBERS is the in-process knowledge
        # base every local lookup reads, and must not grow a seed-only key.
        entry = dict(row)
        entry["_doc_id"] = row["additive_id"]
        docs.append(entry)
    return docs


def allergen_documents() -> list[dict]:
    docs = []
    for allergen_id, entry in ALLERGENS.items():
        # OpenSearch nested synonym terms need explicit shape.
        entry = dict(entry)
        entry["_doc_id"] = allergen_id
        docs.append(entry)
    return docs


def cross_reactivity_documents() -> list[dict]:
    docs = []
    for row in CROSS_REACTIVITY_TABLE:
        entry = dict(row)
        entry["_doc_id"] = row["reaction_id"]
        docs.append(entry)
    return docs


def description_documents() -> list[dict]:
    docs = []
    for ingredient_id, entry in DESCRIPTIONS.items():
        entry = dict(entry)
        entry["_doc_id"] = ingredient_id
        docs.append(entry)
    return docs