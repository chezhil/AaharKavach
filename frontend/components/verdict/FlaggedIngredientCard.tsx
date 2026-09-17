"use client";

import { useState } from "react";
import { ChevronDown, GitBranch } from "lucide-react";
import { SEVERITY_LABEL, type FlaggedIngredient } from "@/lib/types";
import { cn, severityStyles } from "@/lib/utils";

/** One flagged ingredient. Collapsed it states the fact; open it says why. */
export function FlaggedIngredientCard({ flag }: { flag: FlaggedIngredient }) {
  const [open, setOpen] = useState(false);
  const style = severityStyles[flag.profile_severity];

  return (
    <li className={cn("overflow-hidden rounded-xl border bg-bg", style.border)}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left transition-colors hover:bg-surface-hover"
      >
        <span
          aria-hidden
          className={cn("mt-px size-2 shrink-0 rounded-full bg-current", style.text)}
        />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold">{flag.ingredient}</span>
          <span className="mt-0.5 flex items-center gap-1.5 text-xs text-fg-subtle">
            {flag.cross_reactive ? (
              <GitBranch size={11} className="shrink-0" aria-hidden />
            ) : null}
            <span className="truncate">{flag.matched_allergen}</span>
          </span>
        </span>
        <span
          className={cn(
            "shrink-0 rounded-full border px-2 py-0.5 text-[0.65rem] font-bold uppercase tracking-wide",
            style.bg,
            style.text,
            style.border,
          )}
        >
          {SEVERITY_LABEL[flag.profile_severity]}
        </span>
        <ChevronDown
          size={15}
          aria-hidden
          className={cn(
            "shrink-0 text-fg-subtle transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {open ? (
        <p className="animate-rise border-t border-border-subtle bg-surface px-3 py-2.5 text-sm leading-relaxed text-fg-muted">
          {flag.explanation}
        </p>
      ) : null}
    </li>
  );
}
