"use client";

import { SEVERITIES, SEVERITY_LABEL, type Severity } from "@/lib/types";
import { cn, severityStyles } from "@/lib/utils";

interface Props {
  value: Severity;
  onChange: (next: Severity) => void;
  /** Rendered as a label for screen readers when the picker sits in a row. */
  label?: string;
}

export function SeverityPicker({ value, onChange, label }: Props) {
  return (
    <div
      role="radiogroup"
      aria-label={label ?? "Severity"}
      className="grid grid-cols-3 gap-1 rounded-xl bg-bg p-1"
    >
      {SEVERITIES.map((severity) => {
        const active = severity === value;
        return (
          <button
            key={severity}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(severity)}
            className={cn(
              "rounded-lg px-2 py-1.5 text-xs font-bold transition-all",
              active
                ? severityStyles[severity].solid
                : "text-fg-subtle hover:text-fg-muted",
            )}
          >
            {SEVERITY_LABEL[severity]}
          </button>
        );
      })}
    </div>
  );
}
