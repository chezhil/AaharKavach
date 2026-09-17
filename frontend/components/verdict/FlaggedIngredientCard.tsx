"use client";

import { useState } from "react";
import { ChevronDown, GitBranch } from "lucide-react";
import { SEVERITY_LABEL, type FlaggedIngredient } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * One flagged ingredient, inset into a filled verdict tile. Collapsed it
 * states the fact; open it says why. Colours come from the parent tile via
 * `currentColor`, so this reads correctly on green, yellow and crimson alike.
 */
export function FlaggedIngredientCard({ flag }: { flag: FlaggedIngredient }) {
  const [open, setOpen] = useState(false);

  return (
    <li className="overflow-hidden rounded-xl bg-black/10">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left transition-colors hover:bg-black/10"
      >
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-bold">{flag.ingredient}</span>
          <span className="mt-0.5 flex items-center gap-1.5 text-xs opacity-75">
            {flag.cross_reactive ? (
              <GitBranch size={11} className="shrink-0" aria-hidden />
            ) : null}
            <span className="truncate">{flag.matched_allergen}</span>
          </span>
        </span>
        <span className="shrink-0 rounded-full bg-black/15 px-2 py-0.5 text-[0.62rem] font-extrabold uppercase tracking-wider">
          {SEVERITY_LABEL[flag.profile_severity]}
        </span>
        <ChevronDown
          size={15}
          aria-hidden
          className={cn("shrink-0 opacity-60 transition-transform", open && "rotate-180")}
        />
      </button>
      {open ? (
        <p className="animate-rise bg-black/10 px-3 py-2.5 text-sm leading-relaxed opacity-90">
          {flag.explanation}
        </p>
      ) : null}
    </li>
  );
}
