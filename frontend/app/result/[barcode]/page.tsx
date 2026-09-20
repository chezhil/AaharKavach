"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
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
  const { activeIds, activeProfiles, profiles, history, addScan, loading } =
    useApp();
  
  const [isEditChartOpen, setIsEditChartOpen] = useState(false);
  const [chartLabels, setChartLabels] = useState<NutritionLabel[]>(ALL_NUTRIENTS.slice(0, 6));
  const [tempLabels, setTempLabels] = useState<NutritionLabel[]>(ALL_NUTRIENTS.slice(0, 6));

  // Escape closes the nutrient picker, like every other dialog in the app.
  useEffect(() => {
    if (!isEditChartOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsEditChartOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [isEditChartOpen]);

  // Keyed by barcode + selection so a stale answer never renders under a new
  // question; anything not resolved for the current key reads as loading.
  const key = `${barcode}|${[...activeIds].sort().join(",")}`;
  const [resolved, setResolved] = useState<{
    key: string;
    scan: ScanResult | null;
    status: "ready" | "missing" | "error";
  } | null>(null);
  // Bumped by the Retry button. router.refresh() only re-renders server
  // components, so it could never re-run the client effect below — the button
  // looked live and did nothing. This is what actually re-asks the question.
  const [attempt, setAttempt] = useState(0);

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
  }, [barcode, activeIds, cached, loading, addScan, key, attempt]);

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

  // Checked before "missing": a failed lookup also leaves `shown` null, so
  // the !shown test below would otherwise claim the product simply isn't in
  // the database and send people off to photograph a label for no reason.
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
            onClick={() => {
              // Drop the failed answer first so the page falls back to the
              // skeletons while the retry is in flight, instead of sitting on
              // the error until it resolves.
              setResolved(null);
              setAttempt((n) => n + 1);
            }}
          >
            Retry
          </Button>
        }
      />
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

  const { product, evaluation } = shown;

  // Does this product record actually carry a nutrition panel, and do we have
  // the selected person's own daily limits to measure it against?
  const hasStats =
    !!product.nutritional_stats &&
    Object.keys(product.nutritional_stats).length > 0;
  const hasLimits = !!activeProfiles[0]?.daily_limits;
  // FSSAI/Codex-style adult reference values, used only to give the chart a
  // scale when the selected person has no limits of their own. The caption
  // below says which of the two is in play.
  const limits = hasLimits
    ? activeProfiles[0]!.daily_limits!
    : { Energy_kcal: 2000, Protein: 50, Carbs: 260, Sugars: 30, Fat: 70, Salt: 2000, Fiber: 30, SatFat: 20, TransFat: 2 };

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
          <div className="mb-3 flex items-center justify-between">
            <h3 className="display text-base">Nutritional balance</h3>
            {hasStats ? (
              <button
                onClick={() => {
                  setTempLabels(chartLabels);
                  setIsEditChartOpen(true);
                }}
                aria-label="Choose which nutrients to chart"
                className="rounded-md bg-surface-hover p-1.5 text-fg-subtle transition-colors hover:text-fg"
              >
                <Settings size={16} />
              </button>
            ) : null}
          </div>

          {/* An empty {} is truthy in JS, so `nutritional_stats || fallback`
              never actually falls back. The old fallback filled the gap with
              invented numbers (250 kcal, 12 g protein…) and labelled them
              "Demo Data" in 10px grey — on a food-safety screen, next to real
              per-person verdicts, that reads as this product's nutrition.
              A product record with no nutrition panel now says exactly that. */}
          {hasStats ? (
            <div className="overflow-hidden rounded-xl bg-bg px-6 py-4">
              <NutritionHexagon
                currentStats={product.nutritional_stats!}
                userLimits={limits}
                labels={chartLabels}
                className="w-full"
              />
              <p className="mt-2 text-center text-[0.65rem] text-fg-subtle">
                {hasLimits
                  ? `Per serving, against ${activeProfiles[0]!.name}'s daily limits.`
                  : "Per serving, against general adult daily reference values."}
              </p>
            </div>
          ) : (
            <div className="rounded-xl bg-bg px-4 py-5 text-center">
              <p className="text-sm font-semibold text-fg-muted">
                No nutrition panel on record
              </p>
              <p className="mx-auto mt-1 max-w-[34ch] text-xs leading-relaxed text-fg-subtle">
                This product&apos;s record carries ingredients but no per-serving
                figures, so there is nothing to chart. The allergen check above is
                unaffected.
              </p>
            </div>
          )}
        </section>

        {/* Themed off the design tokens, not hardcoded slate/indigo: this was
            a dark slab floating in the light theme. */}
        {isEditChartOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <button
              aria-label="Cancel"
              onClick={() => setIsEditChartOpen(false)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Choose which nutrients to chart"
              className="animate-rise relative w-full max-w-sm rounded-2xl border border-border bg-bg-elevated p-5 shadow-2xl"
            >
              <div className="mb-4 flex items-center justify-between gap-3">
                <h4 className="display text-base">Customise the chart</h4>
                <span className="shrink-0 rounded-md bg-surface-hover px-2 py-1 text-xs font-semibold text-fg-subtle">
                  {tempLabels.length}/6 picked
                </span>
              </div>

              <div className="mb-5 space-y-1.5">
                {ALL_NUTRIENTS.map((n) => {
                  const isSelected = tempLabels.some((t) => t.key === n.key);
                  const isDisabled = !isSelected && tempLabels.length >= 6;
                  return (
                    <label
                      key={n.key}
                      className={cn(
                        "flex cursor-pointer items-center gap-3 rounded-lg border px-2.5 py-2 transition-colors",
                        isSelected
                          ? "border-brand/50 bg-brand-soft/60 text-fg"
                          : "border-transparent text-fg-muted hover:bg-surface-hover",
                        isDisabled && "cursor-not-allowed opacity-45",
                      )}
                    >
                      <input
                        type="checkbox"
                        className="size-4 accent-[var(--brand)]"
                        checked={isSelected}
                        disabled={isDisabled}
                        onChange={(e) => {
                          if (e.target.checked) {
                            if (tempLabels.length < 6)
                              setTempLabels([...tempLabels, n]);
                          } else {
                            setTempLabels(
                              tempLabels.filter((t) => t.key !== n.key),
                            );
                          }
                        }}
                      />
                      <span className="text-sm font-medium">{n.label}</span>
                    </label>
                  );
                })}
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsEditChartOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
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

        {/* Gated on having something to show, not on the prose line: the agent
            leaves safe_alternatives_suggestion null while still returning real
            alternatives, and keying the section off the sentence meant a safer
            product was found and then never shown. */}
        {evaluation.safe_alternatives_suggestion ||
        (evaluation.safe_alternatives?.length ?? 0) > 0 ? (
          <section className="tile bg-surface p-4">
            <h3 className="display flex items-center gap-1.5 text-base">
              <Lightbulb size={16} className="text-brand" aria-hidden />
              Try instead
            </h3>
            <p className="mt-1.5 text-sm leading-relaxed text-fg-muted">
              {evaluation.safe_alternatives_suggestion ??
                `Safer picks: ${evaluation.safe_alternatives
                  ?.map((a) => a.name)
                  .join(", ")}.`}
            </p>
            {evaluation.safe_alternatives?.some((a) =>
              a.barcode.startsWith("synth_"),
            ) ? (
              <p className="mt-2 rounded-lg bg-caution-soft px-2.5 py-1.5 text-[0.7rem] leading-relaxed text-caution">
                Items marked <strong>Unverified</strong> are suggestions from the
                assistant, not products we have checked. Read the label before
                you buy.
              </p>
            ) : null}
            {evaluation.safe_alternatives &&
            evaluation.safe_alternatives.length > 0 ? (
              <ul className="mt-3 space-y-3">
                {evaluation.safe_alternatives.map((alt) => {
                  const isSynth = alt.barcode.startsWith("synth_");
                  return (
                    <li key={alt.barcode} className="flex flex-col gap-2 rounded-xl bg-surface-hover px-3 py-2.5 transition-colors">
                      <div className="flex items-start gap-2">
                        {alt.image_url ? (
                          <img src={alt.image_url} alt={alt.name} className="size-10 shrink-0 rounded object-cover" />
                        ) : null}
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
                        {/* A synth_ barcode means the model suggested this
                            product from memory — nothing checked its actual
                            ingredients, so it must not wear the same green
                            badge as a catalogue pick that was run through the
                            matcher. On an allergen app that is the difference
                            between a verified answer and a guess. */}
                        {isSynth ? (
                          <span
                            className="shrink-0 rounded-full bg-caution-soft px-2 py-0.5 text-[0.65rem] font-extrabold uppercase text-caution"
                            title="Suggested by the assistant — we have not checked this product's ingredients. Verify the label before buying."
                          >
                            Unverified
                          </span>
                        ) : alt.household_cleared ? (
                          <span className="shrink-0 rounded-full bg-safe px-2 py-0.5 text-[0.65rem] font-extrabold uppercase text-safe-fg" title={alt.household_status || ""}>
                            Safe for All
                          </span>
                        ) : (
                          <span className="shrink-0 rounded-full bg-safe px-2 py-0.5 text-[0.65rem] font-extrabold uppercase text-safe-fg">
                            Clear
                          </span>
                        )}
                      </div>
                      
                      {alt.eliminated_allergens && alt.eliminated_allergens.length > 0 && (
                        <div className="text-xs text-fg-subtle">
                          <span className="font-semibold text-safe">Eliminates:</span> {alt.eliminated_allergens.join(", ")}
                        </div>
                      )}
                      
                      {alt.why_it_works && (
                        <div className="text-xs italic text-fg-subtle">
                          {alt.why_it_works}
                        </div>
                      )}
                      
                      {!isSynth && (
                         <div className="mt-1 flex gap-2">
                           <Link href={`/result/${alt.barcode}`} className="flex-1 text-center rounded bg-black/10 py-1.5 text-xs font-semibold hover:bg-black/20">
                             View Details
                           </Link>
                           <Link href={`/compare?a=${product.barcode}&b=${alt.barcode}`} className="flex-1 text-center rounded bg-black/10 py-1.5 text-xs font-semibold hover:bg-black/20">
                             Compare Side-by-Side
                           </Link>
                         </div>
                      )}
                    </li>
                  );
                })}
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
