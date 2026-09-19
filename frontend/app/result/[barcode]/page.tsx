"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Columns2,
  Lightbulb,
  PackageX,
  ScanLine,
  Settings,
  ShieldAlert,
} from "lucide-react";
import { ProductHeader } from "@/components/verdict/ProductHeader";
import { VerdictCard } from "@/components/verdict/VerdictCard";
import { ConfidenceBadge } from "@/components/verdict/ConfidenceBadge";
import { IngredientChips } from "@/components/verdict/IngredientChips";
import { NutritionHexagon, type NutritionLabel } from "@/components/verdict/NutritionHexagon";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { api, ProductNotFoundError, runScan } from "@/lib/api";
import { useApp } from "@/lib/store/app-store";
import { VERDICT_LABEL, worstVerdict, type ScanResult } from "@/lib/types";
import { cn, verdictStyles } from "@/lib/utils";

const ICONS = {
  SAFE: CheckCircle2,
  CAUTION: AlertTriangle,
  UNSAFE: ShieldAlert,
} as const;

const ALL_NUTRIENTS: NutritionLabel[] = [
  { key: 'Energy_kcal', label: 'Energy', unit: 'kcal' },
  { key: 'Protein', label: 'Protein', unit: 'g' },
  { key: 'Carbs', label: 'Carbs', unit: 'g' },
  { key: 'Sugars', label: 'Sugars', unit: 'g' },
  { key: 'Fat', label: 'Fat', unit: 'g' },
  { key: 'Salt', label: 'Sodium', unit: 'mg' },
  { key: 'Fiber', label: 'Fiber', unit: 'g' },
  { key: 'SatFat', label: 'Sat Fat', unit: 'g' },
  { key: 'TransFat', label: 'Trans Fat', unit: 'g' },
];

const sameSelection = (a: string[], b: string[]) =>
  a.length === b.length && [...a].sort().join() === [...b].sort().join();

export default function ResultPage() {
  const { barcode } = useParams<{ barcode: string }>();
  const router = useRouter();
  const { activeIds, activeProfiles, profiles, history, addScan, loading } =
    useApp();
  
  const [isEditChartOpen, setIsEditChartOpen] = useState(false);
  const [chartLabels, setChartLabels] = useState<NutritionLabel[]>(ALL_NUTRIENTS.slice(0, 6));
  const [tempLabels, setTempLabels] = useState<NutritionLabel[]>(ALL_NUTRIENTS.slice(0, 6));

  // Keyed by barcode + selection so a stale answer never renders under a new
  // question; anything not resolved for the current key reads as loading.
  const key = `${barcode}|${[...activeIds].sort().join(",")}`;
  const [resolved, setResolved] = useState<{
    key: string;
    scan: ScanResult | null;
    status: "ready" | "missing" | "error";
  } | null>(null);

  // Reuse the scan we already have when it was run against this exact selection;
  // only re-evaluate when the household selection actually changed.
  const cached = useMemo(
    () =>
      history.find(
        (s) =>
          s.product.barcode === barcode &&
          sameSelection(s.profile_ids, activeIds),
      ) ?? null,
    [history, barcode, activeIds],
  );

  // A cached scan is rendered straight from the store — no effect, no
  // second render pass. The effect below only runs when there isn't one.
  useEffect(() => {
    if (loading || cached) return;

    let cancelled = false;

    (async () => {
      try {
        // A label photo has no re-fetchable barcode — re-evaluate the stored product.
        const stored = history.find((s) => s.product.barcode === barcode);
        if (barcode.startsWith("photo_")) {
          if (!stored) {
            if (!cancelled) setResolved({ key, scan: null, status: "missing" });
            return;
          }
          const evaluation = await api.evaluate({
            product: stored.product,
            profile_ids: activeIds,
          });
          if (cancelled) return;
          const next: ScanResult = {
            ...stored,
            evaluation,
            profile_ids: activeIds,
            scanned_at: new Date().toISOString(),
          };
          await api.recordScan(next);
          addScan(next);
          setResolved({ key, scan: next, status: "ready" });
          return;
        }

        const fresh = await runScan({ barcode }, activeIds);
        if (cancelled) return;
        addScan(fresh);
        setResolved({ key, scan: fresh, status: "ready" });
      } catch (err) {
        if (cancelled) return;
        setResolved({
          key,
          scan: null,
          status: err instanceof ProductNotFoundError ? "missing" : "error",
        });
      }
    })();

    return () => {
      cancelled = true;
    };
    // `history` is intentionally read but not tracked: it changes on every
    // addScan, which would re-trigger the very effect that added the scan.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [barcode, activeIds, cached, loading, addScan, key]);

  const current = resolved?.key === key ? resolved : null;
  const shown = cached ?? current?.scan ?? null;
  const view = cached ? "ready" : (current?.status ?? "loading");

  if (view === "loading") {
    return (
      <div className="space-y-4">
        <div className="flex gap-3">
          <Skeleton className="size-14 rounded-2xl" />
          <div className="flex-1 space-y-2 py-1">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-4 w-44" />
            <Skeleton className="h-3 w-32" />
          </div>
        </div>
        <Skeleton className="h-20 rounded-2xl" />
        <Skeleton className="h-36 rounded-2xl" />
        <Skeleton className="h-36 rounded-2xl" />
      </div>
    );
  }

  if (view === "missing" || !shown) {
    return (
      <EmptyState
        icon={PackageX}
        title="Not in the database"
        body={`We couldn't find ${barcode} in Open Food Facts. Photograph the ingredients panel instead and we'll read it directly.`}
        action={
          <div className="flex flex-wrap justify-center gap-2">
            <Link href="/?scan=photo">
              <Button size="sm">
                <Camera size={15} />
                Photograph the label
              </Button>
            </Link>
            <Link href="/">
              <Button variant="secondary" size="sm">
                <ScanLine size={15} />
                Back to scanning
              </Button>
            </Link>
          </div>
        }
      />
    );
  }

  if (view === "error") {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="That didn't go through"
        body="The lookup failed on the way out. Check the connection and try the scan again."
        action={
          <Button
            variant="secondary"
            size="sm"
            onClick={() => router.refresh()}
          >
            Retry
          </Button>
        }
      />
    );
  }

  const { product, evaluation } = shown;
  const verdict = worstVerdict(evaluation.profile_evaluations);
  const style = verdictStyles[verdict];
  const Icon = ICONS[verdict];
  const clearCount = evaluation.profile_evaluations.filter(
    (e) => e.verdict === "SAFE",
  ).length;
  const total = evaluation.profile_evaluations.length;

  return (
    <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_23rem] lg:items-start">
      <div className="space-y-3">
        <ProductHeader product={product} />

        <section className={cn("tile p-4", style.solid)} aria-live="polite">
          <div className="flex items-start gap-3">
            <Icon
              size={30}
              className="mt-0.5 shrink-0"
              strokeWidth={2.4}
              aria-hidden
            />
            <div className="min-w-0 flex-1">
              <p className="display text-xl">
                {verdict === "SAFE"
                  ? total === 1
                    ? "Safe for them"
                    : `Safe for all ${total}`
                  : `${VERDICT_LABEL[verdict]} for ${total - clearCount} of ${total}`}
              </p>
              <p className="mt-1.5 text-sm font-medium opacity-80">
                Checked against{" "}
                {evaluation.profile_evaluations
                  .map((e) => e.profile_name)
                  .join(", ")}
                .
              </p>
            </div>
            <ConfidenceBadge
              confidence={evaluation.confidence}
              onSolid
              className="shrink-0"
            />
          </div>

          {evaluation.data_quality_note ? (
            <p className="mt-3 rounded-xl bg-black/12 px-3 py-2.5 text-xs font-medium leading-relaxed opacity-90">
              {evaluation.data_quality_note}
            </p>
          ) : null}
        </section>

        <section
          className={cn(
            "grid gap-3",
            evaluation.profile_evaluations.length > 1 &&
              "md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2",
          )}
        >
          {evaluation.profile_evaluations.map((profileEval, i) => (
            <VerdictCard
              key={profileEval.profile_id}
              evaluation={profileEval}
              profile={
                activeProfiles.find((p) => p.id === profileEval.profile_id) ??
                profiles.find((p) => p.id === profileEval.profile_id)
              }
              index={i}
            />
          ))}
        </section>
      </div>

      <aside className="space-y-3 lg:sticky lg:top-24">
        <IngredientChips
          ingredients={product.ingredients}
          flags={evaluation.profile_evaluations.flatMap(
            (e) => e.flagged_ingredients,
          )}
        />

        <section className="tile bg-surface p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="display text-base">Nutritional Balance</h3>
            <button 
              onClick={() => {
                setTempLabels(chartLabels);
                setIsEditChartOpen(true);
              }}
              className="p-1.5 text-gray-400 hover:text-white transition-colors rounded-md bg-white/5 hover:bg-white/10"
            >
              <Settings size={16} />
            </button>
          </div>
          
          <div className="bg-white/5 rounded-xl p-4">
            <NutritionHexagon 
              currentStats={product.nutritional_stats || { Energy_kcal: 250, Protein: 12, Carbs: 30, Sugars: 18, Fat: 8, Salt: 1.2, Fiber: 4, SatFat: 3, TransFat: 0 }}
              userLimits={activeProfiles[0]?.daily_limits || { Energy_kcal: 2000, Protein: 50, Carbs: 260, Sugars: 30, Fat: 70, Salt: 6, Fiber: 30, SatFat: 20, TransFat: 2 }} 
              labels={chartLabels}
              className="w-full"
            />
            {(!product.nutritional_stats || !activeProfiles[0]?.daily_limits) && (
              <p className="text-center text-[10px] mt-2 opacity-50">Demo Data (Backend integration pending)</p>
            )}
          </div>
        </section>

        {isEditChartOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-sm p-5 shadow-2xl animate-in fade-in zoom-in-95">
               <div className="flex justify-between items-center mb-4">
                 <h4 className="text-lg font-bold text-white">Customize Chart</h4>
                 <span className="text-xs font-semibold px-2 py-1 bg-slate-800 text-slate-300 rounded-md">
                   Selected: {tempLabels.length}/6
                 </span>
               </div>
               
               <div className="space-y-2 mb-6">
                 {ALL_NUTRIENTS.map(n => {
                   const isSelected = tempLabels.some(s => s.key === n.key);
                   const isDisabled = !isSelected && tempLabels.length >= 6;
                   return (
                     <label 
                       key={n.key} 
                       className={`flex items-center gap-3 p-2.5 rounded-lg border transition-colors cursor-pointer ${
                         isSelected ? "bg-indigo-500/10 border-indigo-500/50" : "border-transparent hover:bg-white/5"
                       } ${isDisabled ? "opacity-50 cursor-not-allowed" : ""}`}
                     >
                       <input 
                         type="checkbox" 
                         className="rounded border-slate-600 bg-slate-800 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-slate-900"
                         checked={isSelected}
                         disabled={isDisabled}
                         onChange={(e) => {
                           if (e.target.checked) {
                             if (tempLabels.length < 6) setTempLabels([...tempLabels, n]);
                           } else {
                             setTempLabels(tempLabels.filter(s => s.key !== n.key));
                           }
                         }}
                       />
                       <p className={`text-sm font-medium ${isSelected ? "text-white" : "text-slate-300"}`}>
                         {n.label}
                       </p>
                     </label>
                   )
                 })}
               </div>

               <div className="flex justify-end gap-3">
                 <Button variant="secondary" onClick={() => setIsEditChartOpen(false)}>Cancel</Button>
                 <Button 
                   disabled={tempLabels.length !== 6} 
                   onClick={() => { 
                     setChartLabels(tempLabels); 
                     setIsEditChartOpen(false); 
                   }}
                 >
                   Apply
                 </Button>
               </div>
            </div>
          </div>
        )}

        {evaluation.safe_alternatives_suggestion ? (
          <section className="tile bg-surface p-4">
            <h3 className="display flex items-center gap-1.5 text-base">
              <Lightbulb size={16} className="text-brand" aria-hidden />
              Try instead
            </h3>
            <p className="mt-1.5 text-sm leading-relaxed text-fg-muted">
              {evaluation.safe_alternatives_suggestion}
            </p>
            {evaluation.safe_alternatives &&
            evaluation.safe_alternatives.length > 0 ? (
              <ul className="mt-3 space-y-1.5">
                {evaluation.safe_alternatives.map((alt) => (
                  <li key={alt.barcode}>
                    <Link
                      href={`/result/${alt.barcode}`}
                      className="flex items-center gap-2 rounded-xl bg-surface-hover px-3 py-2.5 transition-colors hover:brightness-125"
                    >
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-bold">
                          {alt.name}
                        </span>
                        {alt.brand ? (
                          <span className="block truncate text-xs text-fg-subtle">
                            {alt.brand}
                          </span>
                        ) : null}
                      </span>
                      <span className="shrink-0 rounded-full bg-safe px-2 py-0.5 text-[0.65rem] font-extrabold uppercase text-safe-fg">
                        Clear
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}

        <div className="flex gap-2">
          <Link href={`/compare?a=${product.barcode}`} className="flex-1">
            <Button variant="secondary" className="w-full">
              <Columns2 size={16} />
              Compare
            </Button>
          </Link>
          <Link href="/" className="flex-1">
            <Button className="w-full">
              <ScanLine size={16} />
              Scan another
            </Button>
          </Link>
        </div>
      </aside>
    </div>
  );
}
