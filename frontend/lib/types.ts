/**
 * AaharKavach — shared wire types.
 *
 * Everything that crosses the network boundary is snake_case, matching the
 * agent output schema in the architecture doc. Role 1 (agent), Role 2 (data)
 * and Role 3 (API) should treat this file as the frontend's half of the
 * contract — if a field name changes here it breaks the UI.
 */

export type Severity = "MILD" | "MODERATE" | "SEVERE";
export type Verdict = "SAFE" | "CAUTION" | "UNSAFE";
export type Confidence = "HIGH" | "MEDIUM" | "LOW";

/** Cedar household roles (Role 3 enforces these; the UI only reflects them). */
export type HouseholdRole = "ADMIN" | "MEMBER" | "CHILD";

export interface Restriction {
  id: string;
  /** Human label as the user typed/picked it, e.g. "Peanuts", "Gluten". */
  label: string;
  severity: Severity;
}

export interface Profile {
  id: string;
  name: string;
  household_role: HouseholdRole;
  restrictions: Restriction[];
  /** Token name from the accent palette — purely cosmetic. */
  accent: string;
  /**
   * Set by Role 3 from the Cedar decision for the *calling* user.
   * The UI greys out editing when false; it never decides this itself.
   */
  can_edit: boolean;
}

export interface Ingredient {
  name: string;
  /** e.g. "E322" when the ingredient is a numbered additive. */
  e_number?: string | null;
  /** Plain-language "what is this", from Role 2's knowledge base. */
  explainer?: string | null;
}

export type ProductSource =
  | "OPEN_FOOD_FACTS"
  | "LABEL_PHOTO"
  | "MANUAL"
  /** Served from the backend's bundled catalogue when Open Food Facts is unreachable. */
  | "OFFLINE_CATALOGUE";

export interface Product {
  barcode: string;
  name: string;
  brand?: string | null;
  image_url?: string | null;
  categories?: string[];
  ingredients: Ingredient[];
  /** Role 2's completeness signal for this record. */
  data_confidence: Confidence;
  source: ProductSource;
}

export interface FlaggedIngredient {
  ingredient: string;
  matched_allergen: string;
  profile_severity: Severity;
  explanation: string;
  /** True when the match came from cross-reactivity rather than a direct hit. */
  cross_reactive?: boolean;
}

export interface ProfileEvaluation {
  profile_id: string;
  profile_name: string;
  verdict: Verdict;
  summary: string;
  flagged_ingredients: FlaggedIngredient[];
}

/** Role 1's structured output, verbatim. */
export interface EvaluationResult {
  confidence: Confidence;
  profile_evaluations: ProfileEvaluation[];
  safe_alternatives_suggestion?: string | null;
  data_quality_note?: string | null;
  /** Optional: Role 2 may attach concrete swaps alongside the prose line. */
  safe_alternatives?: AlternativeProduct[];
}

export interface AlternativeProduct {
  barcode: string;
  name: string;
  brand?: string | null;
  reason: string;
}

export interface ScanResult {
  id: string;
  /** ISO 8601. */
  scanned_at: string;
  product: Product;
  evaluation: EvaluationResult;
  /** Which profiles this scan was checked against. */
  profile_ids: string[];
}

export interface CompareResult {
  a: ScanResult;
  b: ScanResult;
  safer_pick: "A" | "B" | "TIE";
  reason: string;
}

/* ---------- request payloads ---------- */

export interface EvaluateRequest {
  barcode?: string;
  /** Used for label-photo scans where there is no barcode to re-fetch. */
  product?: Product;
  profile_ids: string[];
}

export interface CompareRequest {
  barcode_a: string;
  barcode_b: string;
  profile_ids: string[];
}

export type ProfileDraft = Omit<Profile, "id" | "can_edit">;

/* ---------- ui helpers ---------- */

export const SEVERITIES: Severity[] = ["MILD", "MODERATE", "SEVERE"];

export const SEVERITY_LABEL: Record<Severity, string> = {
  MILD: "Mild",
  MODERATE: "Moderate",
  SEVERE: "Severe",
};

export const VERDICT_LABEL: Record<Verdict, string> = {
  SAFE: "Safe",
  CAUTION: "Caution",
  UNSAFE: "Unsafe",
};

export const CONFIDENCE_LABEL: Record<Confidence, string> = {
  HIGH: "Good data",
  MEDIUM: "Partial data",
  LOW: "Thin data",
};

export const HOUSEHOLD_ROLE_LABEL: Record<HouseholdRole, string> = {
  ADMIN: "Admin",
  MEMBER: "Member",
  CHILD: "Child",
};

/** Worst verdict across profiles — drives the summary banner. */
export function worstVerdict(evals: ProfileEvaluation[]): Verdict {
  if (evals.some((e) => e.verdict === "UNSAFE")) return "UNSAFE";
  if (evals.some((e) => e.verdict === "CAUTION")) return "CAUTION";
  return "SAFE";
}

/** Highest severity among a profile's flags — drives visual weight. */
export function peakSeverity(flags: FlaggedIngredient[]): Severity | null {
  if (flags.some((f) => f.profile_severity === "SEVERE")) return "SEVERE";
  if (flags.some((f) => f.profile_severity === "MODERATE")) return "MODERATE";
  if (flags.some((f) => f.profile_severity === "MILD")) return "MILD";
  return null;
}
