"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Loader2, Plus, Trophy, X } from "lucide-react";
import { ProductPicker } from "@/components/compare/ProductPicker";
import { ConfidenceBadge } from "@/components/verdict/ConfidenceBadge";
import { Button } from "@/components/ui/Button";
import { api, ProductNotFoundError } from "@/lib/api";
import { useApp } from "@/lib/store/app-store";
import { VERDICT_LABEL, type CompareResult, type Verdict } from "@/lib/types";
import { cn, verdictStyles } from "@/lib/utils";

type Slot = "A" | "B";

function VerdictPill({ verdict, dim }: { verdict: Verdict; dim?: boolean }) {
  const style = verdictStyles[verdict];
  return (
    <span
      className={cn(
        "inline-flex w-full items-center justify-center rounded-lg border px-2 py-1.5 text-xs font-bold transition-opacity",
        style.bg,
        style.text,
        style.border,
        dim && "opacity-55",
      )}
    >
      {VERDICT_LABEL[verdict]}
    </span>
  );
}

function CompareInner() {
  const params = useSearchParams();
  const { activeIds, activeProfiles, loading } = useApp();

  const [a, setA] = useState<string | null>(params.get("a"));
  const [b, setB] = useState<string | null>(params.get("b"));
  const [picking, setPicking] = useState<Slot | null>(null);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Derived rather than stored: two products picked and no answer yet *is*
  // the busy state, so there's nothing to keep in sync.
  const busy = Boolean(a && b) && !result && !error;

  useEffect(() => {
    if (!a || !b || loading) return;
    let cancelled = false;

    (async () => {
      try {
        const compared = await api.compare({
          barcode_a: a,
          barcode_b: b,
          profile_ids: activeIds,
        });
        if (!cancelled) setResult(compared);
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ProductNotFoundError
            ? `Barcode ${err.barcode} isn't in the database.`
            : "Couldn't run the comparison. Try again.",
        );
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [a, b, activeIds, loading]);

  // Changing either slot invalidates the comparison on the spot, so the old
  // result never sits under a product that is no longer selected.
  const choose = (which: Slot, barcode: string | null) => {
    setResult(null);
    setError(null);
    if (which === "A") setA(barcode);
    else setB(barcode);
  };

  const slot = (which: Slot, barcode: string | null) => {
    const product = which === "A" ? result?.a.product : result?.b.product;
    const winner = result?.safer_pick === which;

    return (
      <div
        className={cn(
          "relative flex min-h-[7rem] flex-col rounded-2xl border p-3 transition-colors",
          winner ? "border-safe-border bg-safe-soft" : "border-border-subtle bg-surface",
        )}
      >
        {winner ? (
          <span className="absolute -top-2.5 left-1/2 flex -translate-x-1/2 items-center gap-1 whitespace-nowrap rounded-full bg-safe px-2 py-0.5 text-[0.65rem] font-bold text-bg">
            <Trophy size={10} aria-hidden />
            Safer pick
          </span>
        ) : null}

        {barcode ? (
          <>
            <button
              onClick={() => choose(which, null)}
              aria-label={`Clear product ${which}`}
              className="absolute right-1.5 top-1.5 grid size-7 place-items-center rounded-full text-fg-subtle transition-colors hover:bg-surface-hover hover:text-fg"
            >
              <X size={14} />
            </button>
            <p className="mt-2 pr-6 text-sm font-bold leading-snug">
              {product?.name ?? "Loading…"}
            </p>
            <p className="mt-0.5 text-xs text-fg-subtle">{product?.brand ?? barcode}</p>
            <span className="mt-auto pt-2">
              {which === "A" && result ? (
                <ConfidenceBadge confidence={result.a.evaluation.confidence} />
              ) : null}
              {which === "B" && result ? (
                <ConfidenceBadge confidence={result.b.evaluation.confidence} />
              ) : null}
            </span>
          </>
        ) : (
          <button
            onClick={() => setPicking(which)}
            className="flex flex-1 flex-col items-center justify-center gap-1.5 rounded-xl border border-dashed border-border-strong text-fg-subtle transition-colors hover:border-brand hover:text-brand"
          >
            <Plus size={18} aria-hidden />
            <span className="text-xs font-semibold">Product {which}</span>
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-bold tracking-tight">Compare two products</h1>
        <p className="mt-1 text-sm text-fg-subtle">
          Checked against{" "}
          {activeProfiles.length > 0
            ? activeProfiles.map((p) => p.name).join(", ")
            : "your household"}
          .
        </p>
      </header>

      <div className="grid grid-cols-2 gap-3">
        {slot("A", a)}
        {slot("B", b)}
      </div>

      {error ? (
        <p role="alert" className="rounded-xl border border-unsafe-border bg-unsafe-soft px-3 py-2.5 text-sm text-unsafe">
          {error}
        </p>
      ) : null}

      {busy ? (
        <p className="flex items-center justify-center gap-2 py-6 text-sm text-fg-subtle">
          <Loader2 size={16} className="animate-spin" aria-hidden />
          Running both past everyone…
        </p>
      ) : null}

      {result && a && b && !busy ? (
        <>
          <section className="animate-rise rounded-2xl border border-border-subtle bg-surface p-4">
            <p className="text-sm font-bold">
              {result.safer_pick === "TIE"
                ? "It's a tie"
                : `${result.safer_pick === "A" ? result.a.product.name : result.b.product.name} is the safer pick`}
            </p>
            <p className="mt-1 text-sm leading-relaxed text-fg-muted">{result.reason}</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-fg-muted">Person by person</h2>
            <ul className="space-y-2">
              {result.a.evaluation.profile_evaluations.map((evalA) => {
                const evalB = result.b.evaluation.profile_evaluations.find(
                  (e) => e.profile_id === evalA.profile_id,
                );
                if (!evalB) return null;
                return (
                  <li
                    key={evalA.profile_id}
                    className="rounded-2xl border border-border-subtle bg-surface p-3"
                  >
                    <p className="mb-2 text-sm font-semibold">{evalA.profile_name}</p>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="space-y-1.5">
                        <VerdictPill
                          verdict={evalA.verdict}
                          dim={result.safer_pick === "B"}
                        />
                        <p className="text-xs leading-relaxed text-fg-subtle">
                          {evalA.flagged_ingredients.length > 0
                            ? evalA.flagged_ingredients.map((f) => f.ingredient).join(", ")
                            : "No matches"}
                        </p>
                      </div>
                      <div className="space-y-1.5">
                        <VerdictPill
                          verdict={evalB.verdict}
                          dim={result.safer_pick === "A"}
                        />
                        <p className="text-xs leading-relaxed text-fg-subtle">
                          {evalB.flagged_ingredients.length > 0
                            ? evalB.flagged_ingredients.map((f) => f.ingredient).join(", ")
                            : "No matches"}
                        </p>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>

          <div className="flex gap-2">
            <Link href={`/result/${result.a.product.barcode}`} className="flex-1">
              <Button variant="secondary" size="sm" className="w-full">
                Full detail A <ArrowRight size={14} />
              </Button>
            </Link>
            <Link href={`/result/${result.b.product.barcode}`} className="flex-1">
              <Button variant="secondary" size="sm" className="w-full">
                Full detail B <ArrowRight size={14} />
              </Button>
            </Link>
          </div>
        </>
      ) : null}

      {!a || !b ? (
        <p className="rounded-2xl border border-dashed border-border-strong px-4 py-6 text-center text-sm text-fg-subtle">
          Pick two products to see which one clears more of your household.
        </p>
      ) : null}

      <ProductPicker
        open={picking !== null}
        onClose={() => setPicking(null)}
        exclude={picking === "A" ? b : a}
        onPick={(barcode) => picking && choose(picking, barcode)}
      />
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<p className="py-10 text-center text-sm text-fg-subtle">Loading…</p>}>
      <CompareInner />
    </Suspense>
  );
}
