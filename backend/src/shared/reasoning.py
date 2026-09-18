"""Turn a product plus a household into per-person verdicts.

Two paths, same output shape:

* **deterministic** — resolves every ingredient through Role 2's ontology and
  applies the severity rules directly. No network, no model, fully repeatable.
  This is what the demo runs on.
* **strands** — Role 1's agent. Used when ``AAHAR_USE_AGENT=true`` and the
  Strands SDK plus Bedrock credentials are actually available; it falls back to
  the deterministic path on any failure rather than failing the request.

An allergen app that answers "service unavailable" is worse than one that
answers from a rulebook, so the fallback is deliberate, not incidental.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from data.mappings.allergen_synonyms import ALLERGENS, resolve_synonym
from data.search.fuzzy_match import Match, match_ingredient

from .contracts import (
    AlternativeProduct,
    EvaluationResult,
    FlaggedIngredient,
    Product,
    Profile,
    ProfileEvaluation,
    Restriction,
    SEVERITY_ORDER,
    Severity,
    Verdict,
)

logger = logging.getLogger(__name__)

# Diet restrictions aren't allergens — they select groups of allergen ids.
DIET_RESTRICTIONS: dict[str, set[str]] = {
    "vegetarian": {"egg", "fish", "shellfish", "carmine"},
    "eggetarian": {"fish", "shellfish", "carmine"},
    "vegan": {"milk", "egg", "fish", "shellfish", "carmine"},
    "jain": {"egg", "fish", "shellfish", "carmine"},
    "halal": set(),
    "kosher": {"shellfish"},
}
# Diets that also care about additives whose source is animal or insect.
ANIMAL_SOURCE_DIETS = {"vegetarian", "vegan", "jain", "eggetarian"}


def _norm(value: str) -> str:
    return " ".join(value.lower().strip().split())


def allergen_ids_for(label: str) -> set[str]:
    """Map a user's restriction label onto Role 2's allergen ids."""
    token = _norm(label)
    if token in DIET_RESTRICTIONS:
        return set(DIET_RESTRICTIONS[token])

    entry = resolve_synonym(token)
    if entry:
        return {entry["allergen_id"]}

    ids: set[str] = set()
    for allergen_id, record in ALLERGENS.items():
        if token == _norm(record["canonical_name"]) or token in {_norm(a) for a in record["aliases"]}:
            ids.add(allergen_id)
        # "Tree Nuts" vs "tree_nuts", "Gluten" vs "wheat_gluten"
        elif token.replace(" ", "_") == allergen_id or token in allergen_id.split("_"):
            ids.add(allergen_id)
    return ids


def _downgrade(severity: Severity) -> Severity:
    return "MODERATE" if severity == "SEVERE" else "MILD"


def _is_animal_derived(additive: dict[str, Any]) -> bool:
    sources = {str(s).lower() for s in additive.get("is_derived_from", [])}
    return bool(sources & {"animal", "insect", "fish", "dairy"})


def _flag_for(
    match: Match,
    restriction: Restriction,
    wanted: set[str],
    diet: str | None,
) -> FlaggedIngredient | None:
    """Decide whether one ontology match trips one restriction."""
    label = match.ingredient

    if match.match_type in ("exact", "synonym", "fuzzy"):
        if match.allergen_id in wanted:
            return FlaggedIngredient(
                ingredient=label,
                matched_allergen=match.matched_allergen,
                profile_severity=restriction.severity,
                explanation=match.explanation,
                cross_reactive=False,
            )
        return None

    if match.match_type == "additive":
        tags = {str(t) for t in match.data.get("allergen_tags", [])}
        if tags & wanted:
            return FlaggedIngredient(
                ingredient=f"{label} ({match.data.get('additive_id')})",
                matched_allergen=match.matched_allergen,
                profile_severity=restriction.severity,
                explanation=match.explanation,
                cross_reactive=False,
            )
        # Ambiguous additives matter to diets, not to allergies: flag softly.
        if diet in ANIMAL_SOURCE_DIETS and _is_animal_derived(match.data):
            note = match.data.get("vegan_vegetarian") or match.explanation
            return FlaggedIngredient(
                ingredient=f"{label} ({match.data.get('additive_id')})",
                matched_allergen=f"{restriction.label} — possibly animal-derived",
                profile_severity=_downgrade(restriction.severity),
                explanation=note,
                cross_reactive=False,
            )
        return None

    if match.match_type == "cross_reactivity":
        primary = _norm(str(match.data.get("primary_allergy", "")))
        if primary and (primary in wanted or allergen_ids_for(primary) & wanted):
            return FlaggedIngredient(
                ingredient=label,
                matched_allergen=f"{restriction.label} (cross-reactive)",
                profile_severity=_downgrade(restriction.severity),
                explanation=match.explanation,
                cross_reactive=True,
            )
    return None


# Same fact, different routes: an allergen hit is better evidence than the
# additive record for the same token, which beats a cross-reaction.
_MATCH_PRIORITY = {"exact": 0, "synonym": 1, "fuzzy": 2, "additive": 3, "cross_reactivity": 4}

_E_SUFFIX = __import__("re").compile(r"\s*\([A-Z]?\d{3,4}[a-z]?\)\s*$")


def _base_ingredient(label: str) -> str:
    """Strip a trailing E-number so one ingredient dedupes to one flag."""
    return _norm(_E_SUFFIX.sub("", label))


def _verdict(flags: list[FlaggedIngredient]) -> Verdict:
    direct = [f for f in flags if not f.cross_reactive]
    if any(SEVERITY_ORDER[f.profile_severity] >= 2 for f in direct):
        return "UNSAFE"
    return "CAUTION" if flags else "SAFE"


def _summary(profile: Profile, flags: list[FlaggedIngredient], verdict: Verdict) -> str:
    if verdict == "SAFE":
        return f"Nothing here matches {profile.name}'s restrictions."
    worst = next((f for f in flags if f.profile_severity == "SEVERE"), flags[0])
    others = len(flags) - 1
    tail = f" (plus {others} more match{'es' if others > 1 else ''})" if others else ""
    if verdict == "UNSAFE":
        return f"Contains {worst.ingredient} — {worst.matched_allergen} for {profile.name}{tail}."
    return f"Worth a second look: {worst.ingredient} may affect {profile.name}{tail}."


def evaluate_profile(
    matches_by_token: dict[str, list[Match]], profile: Profile
) -> ProfileEvaluation:
    # Best flag per (ingredient, restriction) — never the same ingredient twice
    # for one person just because two index routes found it.
    best: dict[tuple[str, str], tuple[int, FlaggedIngredient]] = {}

    for restriction in profile.restrictions:
        wanted = allergen_ids_for(restriction.label)
        diet = _norm(restriction.label) if _norm(restriction.label) in DIET_RESTRICTIONS else None
        if not wanted and not diet:
            continue
        for matches in matches_by_token.values():
            for match in matches:
                flag = _flag_for(match, restriction, wanted, diet)
                if not flag:
                    continue
                key = (_base_ingredient(flag.ingredient), restriction.id)
                rank = _MATCH_PRIORITY.get(match.match_type, 9)
                if key not in best or rank < best[key][0]:
                    best[key] = (rank, flag)

    flags = [f for _, f in best.values()]
    flags.sort(key=lambda f: (-SEVERITY_ORDER[f.profile_severity], f.cross_reactive))
    verdict = _verdict(flags)
    return ProfileEvaluation(
        profile_id=profile.id,
        profile_name=profile.name,
        verdict=verdict,
        summary=_summary(profile, flags, verdict),
        flagged_ingredients=flags,
    )


_NOTES = {
    "HIGH": None,
    "MEDIUM": "Some fields on this product record are incomplete — the ingredient list may not be the full one.",
    "LOW": "We're less sure about this one. The record is sparse or was read from a photo — double-check the physical label.",
}


def evaluate_deterministic(
    product: Product,
    profiles: list[Profile],
    alternatives: list[AlternativeProduct] | None = None,
) -> EvaluationResult:
    matches_by_token = {
        ing.name: match_ingredient(ing.name) for ing in product.ingredients
    }
    evaluations = [evaluate_profile(matches_by_token, p) for p in profiles]

    confidence = product.data_confidence
    if product.source == "LABEL_PHOTO" and confidence == "HIGH":
        confidence = "MEDIUM"
    if len(product.ingredients) <= 3 and confidence != "HIGH":
        confidence = "LOW"

    alternatives = alternatives or []
    unsafe = any(e.verdict != "SAFE" for e in evaluations)
    if alternatives:
        suggestion = "Safer picks: " + ", ".join(a.name for a in alternatives) + "."
    elif unsafe:
        suggestion = "No clearly safe alternative found — look for a certified free-from version."
    else:
        suggestion = None

    return EvaluationResult(
        confidence=confidence,
        profile_evaluations=evaluations,
        safe_alternatives_suggestion=suggestion,
        safe_alternatives=alternatives,
        data_quality_note=_NOTES[confidence],
        reasoning="deterministic",
    )


def _corroborating_flag(
    flag: FlaggedIngredient, profile: Profile
) -> FlaggedIngredient | None:
    """The knowledge base's own version of this flag, or None.

    Returns the *index's* reading rather than a yes/no, because the agent's
    severity and cross-reactive markers cannot be trusted: on banana chips it
    reported a latex cross-reaction as a direct MODERATE hit, which turned a
    CAUTION into an UNSAFE. Severity comes from the profile, cross-reactivity
    from the ontology; only the prose is the model's.
    """
    for restriction in profile.restrictions:
        wanted = allergen_ids_for(restriction.label)
        token = _norm(restriction.label)
        diet = token if token in DIET_RESTRICTIONS else None
        if not wanted and not diet:
            continue
        for match in match_ingredient(flag.ingredient):
            rebuilt = _flag_for(match, restriction, wanted, diet)
            if rebuilt is not None:
                # Keep the agent's wording, take the facts from the index.
                rebuilt.explanation = flag.explanation or rebuilt.explanation
                return rebuilt
    return None


def _corroborated(flag: FlaggedIngredient, profile: Profile) -> bool:
    """Can the knowledge base back this flag for this person?"""
    wanted: set[str] = set()
    diets = set()
    for restriction in profile.restrictions:
        wanted |= allergen_ids_for(restriction.label)
        token = _norm(restriction.label)
        if token in DIET_RESTRICTIONS:
            diets.add(token)

    for match in match_ingredient(flag.ingredient):
        if match.match_type in ("exact", "synonym", "fuzzy") and match.allergen_id in wanted:
            return True
        if match.match_type == "additive":
            if {str(t) for t in match.data.get("allergen_tags", [])} & wanted:
                return True
            if diets & ANIMAL_SOURCE_DIETS and _is_animal_derived(match.data):
                return True
        if match.match_type == "cross_reactivity":
            primary = _norm(str(match.data.get("primary_allergy", "")))
            if primary and (primary in wanted or allergen_ids_for(primary) & wanted):
                return True
    return False


def reconcile(result: EvaluationResult, profiles: list[Profile]) -> EvaluationResult:
    """Keep the model honest about what it can actually support.

    The agent reaches past the knowledge base into its own training data. On a
    Monster Energy scan it flagged taurine as animal-derived — outdated (the
    commercial product is synthetic), absent from the index, and different on
    every run, while the rulebook said SAFE. A verdict that changes because a
    model was reachable is the wrong property for an allergen app.

    So: flags the index can corroborate stand and drive the verdict. Flags it
    cannot are kept as context, marked unverified, capped at MILD, and excluded
    from the verdict.
    """
    by_id = {p.id: p for p in profiles}
    for evaluation in result.profile_evaluations:
        profile = by_id.get(evaluation.profile_id)
        if profile is None:
            continue

        supported: list[FlaggedIngredient] = []
        for flag in evaluation.flagged_ingredients:
            rebuilt = _corroborating_flag(flag, profile)
            if rebuilt is not None:
                supported.append(rebuilt)
            else:
                flag.unverified = True
                flag.profile_severity = "MILD"
                supported.append(flag)
                logger.info(
                    "Agent flagged %r for %s with no knowledge-base support",
                    flag.ingredient, evaluation.profile_name,
                )

        evaluation.flagged_ingredients = supported
        # The verdict follows only what the index can stand behind.
        evaluation.verdict = _verdict([f for f in supported if not f.unverified])
    return result


def evaluate(
    product: Product,
    profiles: list[Profile],
    alternatives: list[AlternativeProduct] | None = None,
) -> EvaluationResult:
    """Agent first when enabled, deterministic rulebook otherwise."""
    baseline = evaluate_deterministic(product, profiles, alternatives)

    if os.environ.get("AAHAR_USE_AGENT", "").lower() == "true":
        try:
            from .agent_bridge import evaluate_with_agent

            # Hand the agent what the ontology already found. It writes the
            # verdict and the plain-English prose; it does not go looking for
            # allergens the knowledge base has not confirmed.
            known = [
                {
                    "profile_name": e.profile_name,
                    "flagged": [
                        {
                            "ingredient": f.ingredient,
                            "allergen": f.matched_allergen,
                            "severity": f.profile_severity,
                            "cross_reactive": f.cross_reactive,
                        }
                        for f in e.flagged_ingredients
                    ],
                }
                for e in baseline.profile_evaluations
            ]
            from . import cache
            from .contracts import (
                FlaggedIngredient as _Flag,
                ProfileEvaluation as _Eval,
            )

            # Same product, same household, same answer — and Bedrock bills
            # per token. Keyed on the ingredients rather than the barcode so an
            # updated record re-asks.
            cache_key = cache.key_for(
                "agent",
                product.barcode,
                [i.name for i in product.ingredients],
                [(p.id, [(r.label, r.severity) for r in p.restrictions]) for p in profiles],
            )
            payload = cache.get("agent", cache_key)
            if payload is not None:
                result = EvaluationResult(
                    confidence=payload["confidence"],
                    profile_evaluations=[
                        _Eval(
                            profile_id=e["profile_id"],
                            profile_name=e["profile_name"],
                            verdict=e["verdict"],
                            summary=e["summary"],
                            flagged_ingredients=[_Flag(**f) for f in e["flagged_ingredients"]],
                        )
                        for e in payload["profile_evaluations"]
                    ],
                    safe_alternatives_suggestion=payload.get("safe_alternatives_suggestion"),
                    data_quality_note=payload.get("data_quality_note"),
                    reasoning=payload.get("reasoning", "strands"),
                )
                result.safe_alternatives = alternatives or []
                return reconcile(result, profiles)

            result = evaluate_with_agent(product, profiles, known)
            if result is not None:
                stored = result.to_dict()
                stored.pop("safe_alternatives", None)
                cache.put("agent", cache_key, stored)
                result.safe_alternatives = alternatives or []
                return reconcile(result, profiles)
        except Exception as exc:
            logger.warning("Strands agent unavailable (%s) — using the rulebook", exc)
    return baseline
