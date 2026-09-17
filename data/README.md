# 🌾 AaharKavach — Role 2: Knowledge Base, Data & OpenSearch

**Owner:** Data / OpenSearch / Open Food Facts Lead

This package is the brain behind what AaharKavach *knows* about food. It owns
the allergen ontology, the additive E-number dictionary, the cross-reactivity
tables, the plain-language ingredient explainers, and the live product lookup
via Open Food Facts — plus the **confidence signal** that the whole app relies
on to say "we're less sure about this one."

Everything is decoupled: the curated knowledge base lives in pure Python data
modules (`data/mappings/`) so Role 1 / Role 3 / tests work with **zero
infrastructure**. OpenSearch and Open Food Facts are optional, pluggable
layers that sit on top.

---

## 1. Folder structure

```
AaharKavach/data/
├── __init__.py            # package metadata
├── services.py            # 🔌 CONTRACT — the facade other roles import
├── requirements.txt
├── README.md
│
├── mappings/              # Curated domain knowledge (single source of truth)
│   ├── e_numbers.py          # E-number/additive dictionary + alias index
│   ├── allergen_synonyms.py  # Allergen → synonym ontology + HARD_NEGATIVES
│   ├── cross_reactivity.py   # trigger × primary-allergy tables
│   └── descriptions.py       # tap-to-explain plain-language texts
│
├── client/
│   ├── openfoodfacts.py      # OFF REST client (typed ProductRecord, fallbacks)
│   └── confidence.py         # HIGH/MEDIUM/LOW scoring + data-quality notes
│
├── search/
│   ├── opensearch.py         # index-name → mapping definitions
│   ├── queries.py            # search utilities (OpenSearch, with local fallback)
│   └── fuzzy_match.py        # deterministic synonym/fuzzy matcher (no infra)
│
├── seed/
│   ├── seed_data.py          # assembles mapping modules → index documents
│   └── seed_opensearch.py    # CLI: creates indices + bulk-indexes documents
│
└── alternative/
    └── suggestions.py        # safe-alternative product suggestions
```

---

## 2. The integration contract (what other roles import)

Everything other roles need is in **`data.services`**:

| Function | Purpose | Used by |
|---|---|---|
| `scan_barcode(barcode)` | OFF lookup → normalised product → confidence → per-ingredient KB matches | Role 1, Role 3 |
| `resolve_ingredient(token)` | Local enrichment of one ingredient (matches + explainer) | Role 1, Role 3 (tap-to-explain) |
| `suggest_safe_products(ctx, allergen_ids)` | 1–3 safer alternatives in same category | Role 1, Role 3 |
| `compare_products(a, b)` | Two fully-resolved `ScanContext`s | Role 1, Role 3 |

`ScanContext.to_dict()` shape (stable for the API layer):

```json
{
  "product": { "barcode": "...", "product_name": "...", "ingredients": [...],
               "allergens": [...], "is_found": true, "confidence": "HIGH" },
  "confidence": { "confidence": "HIGH", "score": 0.93, "reasons": [...] },
  "data_quality": "High-confidence product data — ingredient list looks complete and verified.",
  "ingredient_matches": { "sodium caseinate": [ { "matched_allergen": "Milk / Dairy",
                                                  "match_type": "exact", "confidence": 1.0,
                                                  "explanation": "...", } ] }
}
```

`Match.to_dict()` shape (fed straight into Role 1's `flagged_ingredients`):

```json
{
  "ingredient": "Sodium Caseinate",
  "matched_allergen": "Milk / Dairy",
  "allergen_id": "milk",
  "match_type": "exact",
  "confidence": 1.0,
  "explanation": "Milk proteins (casein or whey) trigger the immune system...",
  "source_note": "FARE (Food Allergy Research & Education); ..."
}
```

---

## 3. Install & run

### Python deps

```bash
pip install -r AaharKavach/data/requirements.txt
```

If you don't install `opensearch-py`, everything still works — the query layer
falls back to the deterministic fuzzy matcher. Same for `requests` being
missing… except OFF product lookup obviously needs the network.

### Live product lookup (no OpenSearch)

```python
from data.services import scan_barcode

ctx = scan_barcode("3017624010701")   # a Nutella jar barcode
print(ctx.product.product_name)       # "Nutella"
print(ctx.confidence.level)           # "MEDIUM" / "HIGH" / "LOW"
print(ctx.ingredient_matches["palm oil"])   # [Match.to_dict(), ...]
```

### OpenSearch (optional, for the "real" path)

Either run a local cluster:

```bash
docker run -p 9200:9200 -e "discovery.type=single-node" opensearchproject/opensearch:2
```

then seed it:

```bash
python -m data.seed.seed_opensearch          # creates + indexes all 4 indices
python -m data.seed.seed_opensearch --delete # recreate from scratch
python -m data.seed.seed_opensearch --dry-run
```

The seed is idempotent (bulk upserts by `_doc_id`). For AWS OpenSearch
Domains set the env vars the client reads:

```
OPENSEARCH_HOST / OPENSEARCH_PORT / OPENSEARCH_USE_SSL / OPENSEARCH_VERIFY_CERTS
OPENSEARCH_USERNAME / OPENSEARCH_PASSWORD
```

Once seeded, `queries.search_allergens("casein")` etc. query the cluster and
still return `Match` objects.

---

## 4. What this module deliberately does NOT do

- ❌ **Per-profile verdicts** → that's Role 1. We supply *matches* + *confidence*
  + *explainers*; Role 1 merges them into verdicts using the profile severities.
- ❌ **Auth / Cedar policies** → Role 3.
- ❌ **UI** → Role 4.
- ✅ We DO produce: the `confidence` value Role 1 must echo verbatim into its
  structured output, and the `data_quality_note` it can use as-is.

---

## 5. Known domain design decisions

1. **Hard negatives** (`allergen_synonyms.HARD_NEGATIVES`): buckwheat must
   never match gluten; coconut must never match tree nuts; "pineapple" must
   not substring-match "pine nut". These are enforced in the fuzzy matcher.
2. **Cross-reactivity is opt-in**: a warning only fires when the *primary*
   allergy is on the profile. Latex → banana, birch → apple, peanut → lupin,
   etc. `severity_bump` can upgrade the UI tone (Role 4 reads it).
3. **Confidence is data-driven, not guessed**: ingredient completeness,
   OFF verification status, allergen-tag presence, brand and photo. The exact
   rules live in `client/confidence.py`.
4. **Synonyms carry their own confidence** (e.g. `whey protein` 1.0 vs
   `mayonnaise 0.85`), so Role 1 can downgrade borderline matches.
5. **French/regional term support**: OFF returns `fr:` tags; `strip_lang()`
   normalises them so cross-role contracts stay in English ids.

---

## 6. Testing

```bash
python -m pytest AaharKavach/data/tests/
```

Test matrix is in `data/tests/test_data_services.py` and covers:
- synonym resolution (milk/casein/ghee, soy/tamari, fake "buckwheat" traps)
- additive E-number lookups (E120 → carmine)
- cross-reactivity gating on primary allergy
- confidence scoring on thin vs complete records
- OFF client normalisation against a canned payload (no network)

Integration with Role 1: pass `ScanContext` into the Strands agent as the
context object. Integration with Role 3: the Lambda handlers call
`data.services.scan_barcode(...)` and wrap results into API responses.