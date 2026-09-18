"""AaharKavach — Role 2 (Data, OpenSearch & Open Food Facts).

Provides the knowledge-base and product-lookup services that Role 1 (agent),
Role 3 (backend) and Role 4 (frontend) depend on:

    - `services.enrich_product(barcode)`  → full scan context (product +
      confidence + per-ingredient knowledge matches)
    - `services.resolve_ingredient(token)` → allergen/additive/description matches
    - `services.suggest_alternatives(...)` → safe-product candidates
    - in-memory knowledge base lives in `data/mappings/*` (no network needed
      for the ontology itself)

Everything is layered, so local development works with zero infrastructure:
the OpenSearch client degrades gracefully to the deterministic fuzzy matcher.
"""

from . import client, mappings, search, alternative, seed

__all__ = ["client", "mappings", "search", "alternative", "seed"]
__version__ = "0.1.0"