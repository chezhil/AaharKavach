import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { VERDICT_LABEL, worstVerdict, type ScanResult } from "@/lib/types";
import { cn, relativeTime, verdictStyles } from "@/lib/utils";

export function HistoryRow({ scan }: { scan: ScanResult }) {
  const verdict = worstVerdict(scan.evaluation.profile_evaluations);
  const style = verdictStyles[verdict];
  const flagged = scan.evaluation.profile_evaluations.filter(
    (e) => e.verdict !== "SAFE",
  );

  return (
    <li>
      <Link
        href={`/result/${scan.product.barcode}`}
        className="tile flex items-center gap-3 bg-surface p-2.5 transition-colors hover:bg-surface-hover"
      >
        <span
          className={cn(
            "grid size-12 shrink-0 place-items-center rounded-xl text-[0.6rem] font-extrabold uppercase leading-none tracking-tight",
            style.solid,
          )}
          aria-hidden
        >
          {VERDICT_LABEL[verdict]}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-bold">
            {scan.product.name}
          </span>
          <span className="mt-0.5 block truncate text-xs text-fg-subtle">
            {flagged.length > 0
              ? `Flagged for ${flagged.map((e) => e.profile_name).join(", ")}`
              : `All ${scan.evaluation.profile_evaluations.length} clear`}
            {" · "}
            {relativeTime(scan.scanned_at)}
          </span>
        </span>
        <ChevronRight
          size={16}
          className="shrink-0 text-fg-subtle"
          aria-hidden
        />
      </Link>
    </li>
  );
}
