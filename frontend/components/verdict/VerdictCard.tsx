"use client";

import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import {
  VERDICT_LABEL,
  peakSeverity,
  type Profile,
  type ProfileEvaluation,
} from "@/lib/types";
import { accentVar, cn, initials, verdictStyles } from "@/lib/utils";
import { FlaggedIngredientCard } from "./FlaggedIngredientCard";

const ICONS = {
  SAFE: CheckCircle2,
  CAUTION: AlertTriangle,
  UNSAFE: ShieldAlert,
} as const;

/**
 * One person's answer. Visual weight scales with severity, not just verdict:
 * a severe peanut hit gets a heavier border and a filled header than a mild
 * soy one, even though both read "Unsafe".
 */
export function VerdictCard({
  evaluation,
  profile,
  index = 0,
}: {
  evaluation: ProfileEvaluation;
  profile?: Profile;
  index?: number;
}) {
  const style = verdictStyles[evaluation.verdict];
  const Icon = ICONS[evaluation.verdict];
  const severity = peakSeverity(evaluation.flagged_ingredients);
  const severe = severity === "SEVERE";

  return (
    <article
      className={cn(
        "animate-rise overflow-hidden rounded-2xl border bg-surface",
        style.border,
        severe && "border-2 shadow-[0_0_0_4px_var(--unsafe-soft)]",
      )}
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <header className={cn("flex items-center gap-3 px-4 py-3", style.bg)}>
        <span
          className="grid size-9 shrink-0 place-items-center rounded-full text-sm font-bold text-bg"
          style={{ background: accentVar[profile?.accent ?? "teal"] }}
        >
          {initials(evaluation.profile_name)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-bold">{evaluation.profile_name}</p>
          <p className={cn("mt-0.5 text-xs font-semibold", style.text)}>
            {severe ? "Severe risk" : VERDICT_LABEL[evaluation.verdict]}
          </p>
        </div>
        <Icon size={severe ? 26 : 22} className={style.text} strokeWidth={2.2} aria-hidden />
      </header>

      <div className="space-y-3 px-4 py-3.5">
        <p className="text-sm leading-relaxed">{evaluation.summary}</p>

        {evaluation.flagged_ingredients.length > 0 ? (
          <ul className="space-y-1.5">
            {evaluation.flagged_ingredients.map((flag, i) => (
              <FlaggedIngredientCard key={`${flag.ingredient}-${i}`} flag={flag} />
            ))}
          </ul>
        ) : null}
      </div>
    </article>
  );
}
