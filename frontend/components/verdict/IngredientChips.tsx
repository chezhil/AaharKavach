"use client";

import { useState } from "react";
import { Info } from "lucide-react";
import type { FlaggedIngredient, Ingredient } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Every ingredient, flagged or not, is tappable. Non-flagged ones get a calm,
 * factual explainer — the point is to teach the label, not to alarm.
 */
export function IngredientChips({
  ingredients,
  flags,
}: {
  ingredients: Ingredient[];
  flags: FlaggedIngredient[];
}) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const flaggedNames = new Set(
    flags.map((f) => f.ingredient.replace(/\s*\([^)]*\)\s*$/, "").toLowerCase()),
  );

  const explainerFor = (ingredient: Ingredient): string => {
    const flag = flags.find((f) =>
      f.ingredient.toLowerCase().includes(ingredient.name.toLowerCase()),
    );
    if (flag) return flag.explanation;
    if (ingredient.explainer) return ingredient.explainer;
    return `No plain-language entry for ${ingredient.name} yet — it isn't matched to any of your restrictions.`;
  };

  return (
    <section className="tile bg-surface p-4">
      <div className="flex items-baseline gap-2">
        <h3 className="display text-base">Ingredients</h3>
        <span className="text-xs text-fg-subtle">tap any to explain</span>
      </div>

      <ul className="mt-3 flex flex-wrap gap-1.5">
        {ingredients.map((ingredient, i) => {
          const flagged = flaggedNames.has(ingredient.name.toLowerCase());
          const open = openIndex === i;
          return (
            <li key={`${ingredient.name}-${i}`}>
              <button
                onClick={() => setOpenIndex(open ? null : i)}
                aria-expanded={open}
                className={cn(
                  "rounded-full px-3 py-1.5 text-xs font-bold transition-all",
                  flagged
                    ? "bg-unsafe text-unsafe-fg"
                    : "bg-surface-hover text-fg-muted hover:text-fg",
                  open && "ring-2 ring-sky ring-offset-2 ring-offset-surface",
                )}
              >
                {ingredient.name}
                {ingredient.e_number ? (
                  <span className="ml-1 font-mono opacity-70">{ingredient.e_number}</span>
                ) : null}
              </button>
            </li>
          );
        })}
      </ul>

      {openIndex !== null ? (
        <div className="animate-rise mt-3 flex gap-2.5 rounded-2xl bg-sky p-3.5 text-sky-fg">
          <Info size={17} className="mt-0.5 shrink-0" aria-hidden />
          <div className="min-w-0">
            <p className="text-sm font-extrabold">{ingredients[openIndex].name}</p>
            <p className="mt-1 text-sm font-medium leading-relaxed opacity-80">
              {explainerFor(ingredients[openIndex])}
            </p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
