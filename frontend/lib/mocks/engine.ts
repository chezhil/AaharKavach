import type {
  AlternativeProduct,
  Confidence,
  EvaluationResult,
  FlaggedIngredient,
  Product,
  Profile,
  ProfileEvaluation,
  Severity,
  Verdict,
} from "@/lib/types";
import {
  ALLERGEN_SYNONYMS,
  CROSS_REACTIVITY,
  FALSE_FRIENDS,
  RESTRICTION_ALIASES,
} from "./knowledge";
import { MOCK_PRODUCTS } from "./fixtures";

/**
 * A deliberately simple stand-in for Role 1's Strands agent: deterministic
 * synonym + cross-reactivity matching, so the UI has something honest to
 * render before the agent is wired up. Same output shape, no LLM.
 */

const norm = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9 ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

function allergensFor(restrictionLabel: string): string[] {
  const key = norm(restrictionLabel);
  if (RESTRICTION_ALIASES[key]) return RESTRICTION_ALIASES[key];
  // Fall back to a direct hit on an allergen name, else treat the raw label
  // as its own allergen so unknown restrictions still match literally.
  const direct = Object.keys(ALLERGEN_SYNONYMS).find((a) =>
    norm(a).includes(key),
  );
  return direct ? [direct] : [restrictionLabel];
}

/** Whole-word containment, so "oats" never matches inside "groats". */
function containsPhrase(hay: string, needle: string): boolean {
  if (!needle) return false;
  return new RegExp(
    `(^|\\s)${needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}($|\\s)`,
  ).test(hay);
}

function matchIngredient(ingredientName: string, allergen: string): boolean {
  const hay = norm(ingredientName);

  // "Cocoa butter" is not dairy — check the exclusions before the synonyms.
  if (
    (FALSE_FRIENDS[allergen] ?? []).some((phrase) =>
      containsPhrase(hay, norm(phrase)),
    )
  ) {
    return false;
  }

  // Only the ingredient may contain the synonym, never the other way round:
  // matching a synonym against the label would read plain "Butter" as the
  // peanut synonym "peanut butter". Terse forms ("milk", "wheat") are listed
  // as synonyms in their own right instead.
  const needles = ALLERGEN_SYNONYMS[allergen] ?? [norm(allergen)];
  return needles.some((n) => {
    const needle = norm(n);
    return hay === needle || containsPhrase(hay, needle);
  });
}

function downgrade(sev: Severity): Severity {
  return sev === "SEVERE" ? "MODERATE" : sev === "MODERATE" ? "MILD" : "MILD";
}

function verdictFor(flags: FlaggedIngredient[]): Verdict {
  const direct = flags.filter((f) => !f.cross_reactive);
  if (
    direct.some(
      (f) =>
        f.profile_severity === "SEVERE" || f.profile_severity === "MODERATE",
    )
  ) {
    return "UNSAFE";
  }
  if (flags.length > 0) return "CAUTION";
  return "SAFE";
}

function summarise(
  profile: Profile,
  flags: FlaggedIngredient[],
  verdict: Verdict,
): string {
  if (verdict === "SAFE") {
    return `Nothing here matches ${profile.name}'s restrictions.`;
  }
  const worst = flags.find((f) => f.profile_severity === "SEVERE") ?? flags[0];
  const others = flags.length - 1;
  const tail =
    others > 0 ? ` (plus ${others} more match${others > 1 ? "es" : ""})` : "";
  if (verdict === "UNSAFE") {
    return `Contains ${worst.ingredient} — ${worst.matched_allergen} for ${profile.name}${tail}.`;
  }
  return `Worth a second look: ${worst.ingredient} may affect ${profile.name}${tail}.`;
}

function evaluateProfile(
  product: Product,
  profile: Profile,
): ProfileEvaluation {
  const flags: FlaggedIngredient[] = [];
  const seen = new Set<string>();

  for (const restriction of profile.restrictions) {
    for (const allergen of allergensFor(restriction.label)) {
      // Direct matches.
      for (const ingredient of product.ingredients) {
        const label = ingredient.e_number
          ? `${ingredient.name} (${ingredient.e_number})`
          : ingredient.name;
        const hit =
          matchIngredient(ingredient.name, allergen) ||
          (ingredient.e_number
            ? matchIngredient(ingredient.e_number, allergen)
            : false);
        if (!hit) continue;
        const key = `${label}|${allergen}`;
        if (seen.has(key)) continue;
        seen.add(key);
        flags.push({
          ingredient: label,
          matched_allergen: allergen,
          profile_severity: restriction.severity,
          explanation:
            ingredient.explainer ??
            `${ingredient.name} is a source of ${allergen.toLowerCase()}, which ${profile.name} avoids.`,
          cross_reactive: false,
        });
      }

      // Cross-reactivity — a related risk, never listed as the allergen itself.
      const cross =
        CROSS_REACTIVITY[allergen] ?? CROSS_REACTIVITY[restriction.label];
      if (!cross) continue;
      for (const ingredient of product.ingredients) {
        const hay = norm(ingredient.name);
        const trigger = cross.triggers.find((t) => hay.includes(norm(t)));
        if (!trigger) continue;
        const key = `${ingredient.name}|${restriction.label}|cross`;
        if (seen.has(key)) continue;
        seen.add(key);
        flags.push({
          ingredient: ingredient.name,
          matched_allergen: `${restriction.label} (cross-reactive)`,
          profile_severity: downgrade(restriction.severity),
          explanation: cross.note,
          cross_reactive: true,
        });
      }
    }
  }

  const verdict = verdictFor(flags);
  return {
    profile_id: profile.id,
    profile_name: profile.name,
    verdict,
    summary: summarise(profile, flags, verdict),
    flagged_ingredients: flags,
  };
}

function confidenceFor(product: Product): Confidence {
  if (product.ingredients.length <= 3 && product.data_confidence !== "HIGH")
    return "LOW";
  if (product.source === "LABEL_PHOTO") {
    return product.data_confidence === "HIGH" ? "MEDIUM" : "LOW";
  }
  return product.data_confidence;
}

function alternativesFor(
  product: Product,
  profiles: Profile[],
): AlternativeProduct[] {
  const category = product.categories?.[0];
  if (!category) return [];
  return MOCK_PRODUCTS.filter((candidate) => {
    if (candidate.barcode === product.barcode) return false;
    if (!candidate.categories?.includes(category)) return false;
    return profiles.every(
      (p) => evaluateProfile(candidate, p).verdict === "SAFE",
    );
  })
    .slice(0, 3)
    .map((candidate) => ({
      barcode: candidate.barcode,
      name: candidate.name,
      brand: candidate.brand ?? null,
      reason: `No matches against ${profiles.map((p) => p.name).join(" or ")}'s restrictions.`,
    }));
}

export function evaluate(
  product: Product,
  profiles: Profile[],
): EvaluationResult {
  const profile_evaluations = profiles.map((p) => evaluateProfile(product, p));
  const confidence = confidenceFor(product);
  const unsafe = profile_evaluations.some((e) => e.verdict !== "SAFE");
  const alternatives = unsafe ? alternativesFor(product, profiles) : [];

  const notes: Record<Confidence, string | null> = {
    HIGH: null,
    MEDIUM:
      "Some fields on this product record are incomplete — the ingredient list may not be the full one.",
    LOW: "We're less sure about this one. The record is sparse or was read from a photo — double-check the physical label.",
  };

  return {
    confidence,
    profile_evaluations,
    safe_alternatives_suggestion:
      alternatives.length > 0
        ? `Safer picks in ${product.categories?.[0]?.toLowerCase() ?? "this category"}: ${alternatives
            .map((a) => a.name)
            .join(", ")}.`
        : unsafe
          ? "No clearly safe alternative in our catalogue yet — check for a certified free-from version."
          : null,
    safe_alternatives: alternatives,
    data_quality_note: notes[confidence],
  };
}

export function compareVerdicts(
  aEvals: ProfileEvaluation[],
  bEvals: ProfileEvaluation[],
): { safer_pick: "A" | "B" | "TIE"; reason: string } {
  const score = (evals: ProfileEvaluation[]) =>
    evals.reduce((total, e) => {
      const base =
        e.verdict === "UNSAFE" ? 100 : e.verdict === "CAUTION" ? 10 : 0;
      const weight = e.flagged_ingredients.reduce(
        (sum, f) =>
          sum +
          (f.profile_severity === "SEVERE"
            ? 5
            : f.profile_severity === "MODERATE"
              ? 3
              : 1),
        0,
      );
      return total + base + weight;
    }, 0);

  const a = score(aEvals);
  const b = score(bEvals);
  if (a === b) {
    return {
      safer_pick: "TIE",
      reason:
        a === 0
          ? "Both are clear for everyone you selected."
          : "Both carry the same level of risk for the profiles you selected.",
    };
  }
  const winner = a < b ? "A" : "B";
  const winnerEvals = a < b ? aEvals : bEvals;
  const loserEvals = a < b ? bEvals : aEvals;
  const clean = winnerEvals.every((e) => e.verdict === "SAFE");
  const loserFlags = loserEvals.flatMap((e) => e.flagged_ingredients);
  return {
    safer_pick: winner,
    reason: clean
      ? `It clears every selected profile, while the other flags ${loserFlags[0]?.matched_allergen ?? "a restriction"}.`
      : `Fewer and less severe matches — the other flags ${loserFlags[0]?.ingredient ?? "an ingredient"}.`,
  };
}
