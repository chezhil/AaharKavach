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
import { NutritionHexagon } from "./NutritionHexagon";

const ICONS = {
  SAFE: CheckCircle2,
  CAUTION: AlertTriangle,
  UNSAFE: ShieldAlert,
} as const;

/**
 * One person's answer, as a filled bento tile. Weight scales with severity,
 * not just verdict: a severe peanut hit gets a ring and a bigger glyph than a
 * mild soy one, even though both read "Unsafe".
 */
export function VerdictCard({
  evaluation,
  profile,
  product, // <-- New prop
  index = 0,
}: {
  evaluation: ProfileEvaluation;
  profile?: Profile;
  product?: any; // any to avoid circular import if needed, but we can import Product
  index?: number;
}) {
  const style = verdictStyles[evaluation.verdict];
  const Icon = ICONS[evaluation.verdict];
  const severity = peakSeverity(evaluation.flagged_ingredients);
  const severe = severity === "SEVERE";

  return (
    <article
      className={cn(
        "tile animate-rise p-4",
        style.solid,
        severe && "ring-2 ring-unsafe-line ring-offset-2 ring-offset-bg",
      )}
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <header className="flex items-center gap-3">
        <span
          className="grid size-10 shrink-0 place-items-center rounded-full text-sm font-extrabold text-bg"
          style={{ background: accentVar[profile?.accent ?? "teal"] }}
        >
          {initials(evaluation.profile_name)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-bold uppercase tracking-wider opacity-70">
            {evaluation.profile_name}
          </p>
          <p className="display mt-0.5 text-2xl">
            {severe ? "Severe" : VERDICT_LABEL[evaluation.verdict]}
          </p>
        </div>
        <Icon
          size={severe ? 32 : 26}
          strokeWidth={2.4}
          aria-hidden
          className="shrink-0"
        />
      </header>

      <p className="mt-3 text-sm font-medium leading-relaxed opacity-90">
        {evaluation.summary}
      </p>

        <ul className="mt-3 space-y-1.5">
          {evaluation.flagged_ingredients.map((flag, i) => (
            <FlaggedIngredientCard
              key={`${flag.ingredient}-${i}`}
              flag={flag}
            />
          ))}
        </ul>
      ) : null}

      {/* NutritionHexagon: Real data if available, otherwise mock demo */}
      {(product?.nutritional_stats || profile?.daily_limits) ? (
        <div className="mt-4 pt-4 border-t border-current/10">
          <p className="text-xs font-bold uppercase tracking-wider opacity-70 mb-2">Nutritional Balance</p>
          <div className="bg-white/5 rounded-xl p-4">
            <NutritionHexagon 
              currentStats={product?.nutritional_stats || { Energy_kcal: 250, Protein: 12, Carbs: 30, Sugars: 18, Fat: 8, Salt: 1.2 }}
              userLimits={profile?.daily_limits || { Energy_kcal: 2000, Protein: 50, Carbs: 260, Sugars: 30, Fat: 70, Salt: 6 }} 
              className="w-full"
            />
          </div>
        </div>
      ) : (
        <div className="mt-4 pt-4 border-t border-current/10">
          <p className="text-xs font-bold uppercase tracking-wider opacity-70 mb-2">Nutritional Balance</p>
          <div className="bg-white/5 rounded-xl p-4">
            <NutritionHexagon 
              currentStats={{ Energy_kcal: 250, Protein: 12, Carbs: 30, Sugars: 18, Fat: 8, Salt: 1.2 }}
              userLimits={{ Energy_kcal: 2000, Protein: 50, Carbs: 260, Sugars: 30, Fat: 70, Salt: 6 }} 
              className="w-full"
            />
            <p className="text-center text-[10px] mt-2 opacity-50">Demo Data (Backend integration pending)</p>
          </div>
        </div>
      )}
    </article>
  );
}
