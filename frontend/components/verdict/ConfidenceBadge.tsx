import { CONFIDENCE_LABEL, type Confidence } from "@/lib/types";
import { cn, confidenceStyles } from "@/lib/utils";

/**
 * Data quality, shown next to the verdict rather than buried. A confident-
 * looking "Safe" on a half-empty record is the failure mode this guards.
 */
export function ConfidenceBadge({
  confidence,
  className,
}: {
  confidence: Confidence;
  className?: string;
}) {
  const style = confidenceStyles[confidence];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border-subtle bg-surface px-2.5 py-1",
        className,
      )}
      title={`Data quality: ${CONFIDENCE_LABEL[confidence].toLowerCase()}`}
    >
      <span className="flex items-end gap-[2px]" aria-hidden>
        {[1, 2, 3].map((bar) => (
          <span
            key={bar}
            className={cn(
              "w-[3px] rounded-sm transition-colors",
              bar === 1 ? "h-1.5" : bar === 2 ? "h-2.5" : "h-3.5",
              bar <= style.bars ? style.bg : "bg-border-strong",
            )}
          />
        ))}
      </span>
      <span className={cn("text-[0.7rem] font-semibold", style.text)}>
        {CONFIDENCE_LABEL[confidence]}
      </span>
    </span>
  );
}
