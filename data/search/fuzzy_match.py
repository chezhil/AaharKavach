"""Local fuzzy / synonym matching against the curated knowledge base.

Two tiers of matching are provided:
  1. Exact alias lookup (fast, error-free) — `resolve_synonym` in mappings.
  2. Fuzzy fallback — token overlap + difflib SequenceMatcher on synonyms,
     with strict guards against hard negatives (buckwheat ↔ wheat, etc.).

The OpenSearch path (`data/search/queries.py`) is the production route when an
OpenSearch cluster is available; this module is the deterministic fallback that
keeps Role 1 & tests working with zero external services. Contract is the same:
a list of `Match` objects with `(*, match_type, confidence, matched_allergen)`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from ..mappings.allergen_synonyms import ALLERGENS, HARD_NEGATIVES, resolve_synonym
from ..mappings.e_numbers import ALIAS_INDEX, lookup_additive, E_NUMBERS
from ..mappings.cross_reactivity import CROSS_REACTIVITY_TABLE
from ..mappings.descriptions import DESCRIPTION_ALIAS_INDEX, lookup_description

MIN_FUZZY_RATIO = 0.82


@dataclass
class Match:
    ingredient: str
    matched_allergen: str       # canonical group name, e.g. "Milk / Dairy"
    allergen_id: str
    match_type: str             # exact | synonym | additive | fuzzy | cross_reactivity
    confidence: float           # 0..1
    explanation: str = ""
    source_note: str = ""
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ingredient": self.ingredient,
            "matched_allergen": self.matched_allergen,
            "allergen_id": self.allergen_id,
            "match_type": self.match_type,
            "confidence": round(self.confidence, 3),
            "explanation": self.explanation,
            "source_note": self.source_note,
        }


def _normalise(raw: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, fold accents."""
    out = raw.lower().strip()
    # Fold diacritics to ASCII for more forgiving matching.
    out = out.replace("é", "e").replace("è", "e").replace("ê", "e")
    out = out.replace("í", "i").replace("í", "i")
    out = out.replace("ó", "o").replace("ö", "o").replace("ò", "o")
    out = out.replace("ü", "u").replace("ú", "u")
    out = out.replace("ç", "c").replace("ñ", "n").replace("ß", "ss")
    return " ".join(out.split())


def _contains_whole(token: str, candidate: str) -> bool:
    """True if `candidate` appears in `token` as a whole word."""
    import re
    return re.search(rf"\b{re.escape(candidate)}\b", token) is not None


def _hard_negative(ingredient: str, allergen_id: str) -> bool:
    """Block known false-positive confusions."""
    for bad in HARD_NEGATIVES.get(ingredient, []):
        if bad == allergen_id:
            return True
    return False


def match_ingredient(ingredient: str) -> list[Match]:
    """High-level entry point: resolve one ingredient token → matches.

    Order of preference:
      1. exact synonym (allergen ontology)
      2. exact additive E-number/alias → additive match
      3. exact description lookup
      4. fuzzy against synonym terms + cross-reactivity triggers (guarded)
    """
    norm = _normalise(ingredient)
    matches: list[Match] = []

    if not norm:
        return matches

    # 1) Allergen synonyms — the ontology.
    entry = resolve_synonym(norm)
    if entry and not _hard_negative(norm, entry["allergen_id"]):
        conf = entry.get("matched_confidence", 1.0)
        matches.append(Match(
            ingredient=ingredient,
            matched_allergen=entry["canonical_name"],
            allergen_id=entry["allergen_id"],
            match_type="exact",
            confidence=conf,
            explanation=entry["manifestation"],
            source_note=entry["confidence_source"],
            data=entry,
        ))

    # 2) Additives via E-number / alias.
    additive = lookup_additive(norm) or lookup_additive(ingredient)
    if additive:
        matches.append(Match(
            ingredient=ingredient,
            matched_allergen=additive["name"],
            allergen_id=f"e:{additive['additive_id']}",
            match_type="additive",
            confidence=0.9,
            explanation=additive["plain_explanation"],
            source_note=additive["confidence_source"],
            data=additive,
        ))

    # If we already have an exact hit, skip fuzzy (avoid spurious extras) —
    # but still add cross-reactivity checks below, they are independent.
    found_exact = bool(matches)

    # 3) Cross-reactivity trigger match.
    for row in CROSS_REACTIVITY_TABLE:
        trigger = _normalise(row["trigger"])
        if norm == trigger:
            matches.append(Match(
                ingredient=ingredient,
                matched_allergen=row["primary_allergy"],
                allergen_id=f"x:{row['reaction_id']}",
                match_type="cross_reactivity",
                confidence=row["confidence"],
                explanation=row["reason"],
                source_note=row["category"],
                data=row,
            ))

    if found_exact:
        # Still attempt a transparent fuzzy pass for additive already covered.
        # Deduplicate by (allergen_id, match_type).
        return _dedupe(matches)

    # 4) Fuzzy pass — synonyms only, guarded against hard negatives.
    for allergen_id, entry in ALLERGENS.items():
        if _hard_negative(norm, allergen_id):
            continue
        for term in entry["synonym_terms"]:
            ratio = _token_ratio(norm, _normalise(term["term"]))
            if ratio >= MIN_FUZZY_RATIO:
                matches.append(Match(
                    ingredient=ingredient,
                    matched_allergen=entry["canonical_name"],
                    allergen_id=entry["allergen_id"],
                    match_type="fuzzy",
                    confidence=max(term["confidence"], ratio),
                    explanation=entry["manifestation"],
                    source_note=f"fuzzy match ({ratio:.0%})",
                    data=entry,
                ))
                break  # one match per allergen is enough

    # 5) Description lookup for the tap-to-explain feature (always allowed).
    desc = lookup_description(norm) or lookup_description(ingredient)
    if desc and not any(m.match_type == "description" for m in matches):
        matches.append(Match(
            ingredient=ingredient,
            matched_allergen=desc["name"],
            allergen_id=f"d:{desc['ingredient_id']}",
            match_type="description",
            confidence=0.95 if "confidence_source" in desc else 0.5,
            explanation=desc["plain_explanation"],
            source_note=desc.get("confidence_source", ""),
            data=desc,
        ))

    return _dedupe(matches)


def _token_ratio(a: str, b: str) -> float:
    """Combined character + token overlap ratio."""
    if not a or not b:
        return 0.0
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    if not a_tokens or not b_tokens:
        return 0.0
    overlap = len(a_tokens & b_tokens) / max(len(a_tokens), len(b_tokens))
    seq = SequenceMatcher(None, a, b).ratio()
    return max(overlap, seq)


def _dedupe(matches: list[Match]) -> list[Match]:
    """Keep highest-confidence first per (allergen_id, match_type)."""
    seen: dict[tuple[str, str], Match] = {}
    for m in matches:
        key = (m.allergen_id, m.match_type)
        if key not in seen or m.confidence > seen[key].confidence:
            seen[key] = m
    return sorted(seen.values(), key=lambda m: m.confidence, reverse=True)


def match_ingredients(ingredients: list[str]) -> dict[str, list[Match]]:
    """Batch wrapper: token → list[Match]."""
    return {token: match_ingredient(token) for token in ingredients}