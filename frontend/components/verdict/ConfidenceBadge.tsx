import { CONFIDENCE_LABEL, type Confidence } from "@/lib/types";
import { cn, confidenceStyles } from "@/lib/utils";

/**
 * Data quality, shown next to the verdict rather than buried. A confident-
 * looking "Safe" on a half-empty record is the failure mode this guards.
 *
 * `onSolid` puts it on a filled verdict tile, where it borrows the tile's own
 * text colour instead of the hue that only reads against black.
 */
export function ConfidenceBadge({
  confidence,
  onSolid = false,
  className,
}: {
  confidence: Confidence;
  onSolid?: boolean;
  className?: string;
}) {
  const style = confidenceStyles[confidence];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1",
        onSolid ? "bg-black/12" : "bg-surface",
        className,
      )}
      title={`Data quality: ${CONFIDENCE_LABEL[confidence].toLowerCase()}`}
    >
      <span className="flex items-end gap-[2px]" aria-hidden>
        {[1, 2, 3].map((bar) => (
          <span
            key={bar}
            className={cn(
              "w-[3px] rounded-sm",
              bar === 1 ? "h-1.5" : bar === 2 ? "h-2.5" : "h-3.5",
              bar <= style.bars
                ? onSolid
                  ? "bg-current opacity-90"
                  : style.bar
                : onSolid
                  ? "bg-current opacity-25"
                  : "bg-border-strong",
            )}
          />
        ))}
      </span>
      <span
        className={cn(
          "text-[0.68rem] font-bold uppercase tracking-wide",
          onSolid ? "opacity-90" : style.line,
        )}
      >
        {CONFIDENCE_LABEL[confidence]}
      </span>
    </span>
  );
}
