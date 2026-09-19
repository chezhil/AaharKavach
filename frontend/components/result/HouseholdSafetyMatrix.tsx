import React, { useState } from "react";
import { ChevronDown, ChevronUp, AlertTriangle, CheckCircle, Info } from "lucide-react";
import type { BatchAuditItem, Profile, Verdict } from "@/lib/types";
import { cn } from "@/lib/utils";

/** The household column is the worst verdict any member got for this item. */
const householdVerdict = (item: BatchAuditItem): Verdict => {
  const all = Object.values(item.member_verdicts ?? {}).map((m) => m.verdict);
  if (all.includes("UNSAFE")) return "UNSAFE";
  if (all.includes("CAUTION")) return "CAUTION";
  return "SAFE";
};

interface Props {
  items: BatchAuditItem[];
  profiles: Profile[];
}

const VerdictIcon = ({ verdict, size = 16 }: { verdict: string, size?: number }) => {
  if (verdict === "SAFE") return <CheckCircle size={size} className="text-safe" />;
  if (verdict === "CAUTION") return <AlertTriangle size={size} className="text-caution" />;
  if (verdict === "UNSAFE") return <AlertTriangle size={size} className="text-unsafe" />;
  return <Info size={size} className="text-fg-subtle" />;
};

export function HouseholdSafetyMatrix({ items, profiles }: Props) {
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const toggleRow = (barcode: string) => {
    setExpandedRow(prev => prev === barcode ? null : barcode);
  };

  return (
    <div className="rounded-2xl border border-border bg-surface overflow-hidden">
      <div className="p-4 border-b border-border bg-bg/50">
        <h3 className="font-semibold">Household Safety Matrix</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-bg/50">
            <tr>
              <th className="px-4 py-3 font-medium text-fg-subtle">Product</th>
              <th className="px-4 py-3 font-medium text-fg-subtle text-center">Overall</th>
              {profiles.map(p => (
                <th key={p.id} className="px-4 py-3 font-medium text-fg-subtle text-center">
                  <div className="flex flex-col items-center gap-1">
                    <span 
                      className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white shadow-sm"
                      style={{ backgroundColor: p.accent }}
                    >
                      {p.name.charAt(0).toUpperCase()}
                    </span>
                    <span className="text-[10px] truncate max-w-[50px]">{p.name}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.map((item, idx) => (
              <React.Fragment key={`${item.barcode}-${idx}`}>
                <tr 
                  className={cn(
                    "transition-colors hover:bg-surface-hover cursor-pointer",
                    expandedRow === item.barcode ? "bg-surface-hover" : ""
                  )}
                  onClick={() => toggleRow(item.barcode)}
                >
                  <td className="px-4 py-3 max-w-[150px]">
                    <div className="flex items-center gap-3">
                      {item.image_url ? (
                        <img src={item.image_url} alt="" className="h-10 w-10 rounded object-cover shrink-0 border border-border" />
                      ) : (
                        <div className="h-10 w-10 flex shrink-0 items-center justify-center rounded bg-bg border border-border text-xs text-fg-muted font-mono">
                          {item.barcode.slice(-4)}
                        </div>
                      )}
                      <div className="min-w-0">
                        <p className="truncate font-semibold text-sm">
                          {item.product_name || "Unknown Product"}
                        </p>
                        {item.brand && <p className="truncate text-xs text-fg-subtle">{item.brand}</p>}
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-4 py-3 text-center">
                    {item.status !== "KNOWN" ? (
                      <span className="inline-flex items-center justify-center rounded-full bg-bg px-2 py-1 text-xs text-fg-muted">
                        {item.status === "UNKNOWN" ? "Unknown" : "Unavailable"}
                      </span>
                    ) : (
                      <div className="flex justify-center">
                        <VerdictIcon verdict={householdVerdict(item)} size={20} />
                      </div>
                    )}
                  </td>

                  {profiles.map(p => (
                    <td key={p.id} className="px-4 py-3 text-center">
                      {item.status === "KNOWN" && item.member_verdicts && (
                        <div className="flex justify-center">
                          <VerdictIcon verdict={item.member_verdicts[p.id]?.verdict || "SAFE"} size={16} />
                        </div>
                      )}
                    </td>
                  ))}
                </tr>
                
                {/* Expanded Details Row */}
                {expandedRow === item.barcode && item.status === "KNOWN" && (
                  <tr className="bg-bg/30">
                    <td colSpan={profiles.length + 2} className="px-4 py-3">
                      <div className="flex flex-col gap-2 rounded-xl border border-border-subtle bg-bg p-3">
                        <p className="text-xs font-semibold uppercase text-fg-subtle">Household Conflicts</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {profiles.map(p => {
                            const member = item.member_verdicts?.[p.id];
                            if (!member || member.verdict === "SAFE") return null;
                            const flagged = member.flagged_ingredients ?? [];
                            return (
                              <div key={p.id} className="flex items-start gap-2 rounded-lg border border-border-subtle p-2">
                                <VerdictIcon verdict={member.verdict} size={14} />
                                <div>
                                  <span className="text-xs font-medium">{p.name}: </span>
                                  <span className="text-xs text-fg-subtle">
                                    {flagged.length > 0
                                      ? flagged.map(f => `${f.ingredient} (${f.reason})`).join(", ")
                                      : `Flagged for ${member.verdict === "UNSAFE" ? "danger" : "caution"}.`}
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                          {Object.values(item.member_verdicts || {}).every(m => m.verdict === "SAFE") && (
                            <p className="text-xs text-safe">Safe for all members.</p>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
