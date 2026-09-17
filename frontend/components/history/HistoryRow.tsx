import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { VERDICT_LABEL, worstVerdict, type ScanResult } from "@/lib/types";
import { cn, relativeTime, verdictStyles } from "@/lib/utils";

export function HistoryRow({ scan }: { scan: ScanResult }) {
  const verdict = worstVerdict(scan.evaluation.profile_evaluations);
  const style = verdictStyles[verdict];
  const flagged = scan.evaluation.profile_evaluations.filter((e) => e.verdict !== "SAFE");

  return (
    <li>
      <Link
        href={`/result/${scan.product.barcode}`}
        className="flex items-center gap-3 rounded-2xl border border-border-subtle bg-surface p-3 transition-colors hover:bg-surface-hover"
      >
        <span
          className={cn("h-11 w-1.5 shrink-0 rounded-full", style.dot)}
          aria-hidden
        />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold">{scan.product.name}</span>
          <span className="mt-0.5 block truncate text-xs text-fg-subtle">
            {scan.product.brand ? `${scan.product.brand} · ` : ""}
            {relativeTime(scan.scanned_at)}
          </span>
        </span>
        <span className="shrink-0 text-right">
          <span className={cn("block text-xs font-bold", style.text)}>
            {VERDICT_LABEL[verdict]}
          </span>
          {flagged.length > 0 ? (
            <span className="mt-0.5 block text-[0.65rem] text-fg-subtle">
              for {flagged.map((e) => e.profile_name).join(", ")}
            </span>
          ) : (
            <span className="mt-0.5 block text-[0.65rem] text-fg-subtle">
              all {scan.evaluation.profile_evaluations.length} clear
            </span>
          )}
        </span>
        <ChevronRight size={16} className="shrink-0 text-fg-subtle" aria-hidden />
      </Link>
    </li>
  );
}
