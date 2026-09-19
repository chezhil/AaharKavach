"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, AlertTriangle, CheckCircle, Package } from "lucide-react";
import { useCartStore } from "@/stores/useCartStore";
import { api } from "@/lib/api";
import { useApp } from "@/lib/store/app-store";
import { Button } from "@/components/ui/Button";
import { HouseholdSafetyMatrix } from "@/components/result/HouseholdSafetyMatrix";
import { cn } from "@/lib/utils";

export default function BatchResultPage() {
  const router = useRouter();
  const { items, clearCart } = useCartStore();
  const { profiles } = useApp(); // We need profiles to render the matrix columns
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (items.length === 0) {
      router.replace("/");
      return;
    }

    let cancelled = false;

    const runAudit = async () => {
      try {
        const barcodes = items.map(i => i.barcode);
        const householdId = "hh_1";
        
        const res = await api.auditBatch(barcodes, householdId);
        // Guard: do not update state if component unmounted during fetch
        if (!cancelled) setData(res);
      } catch (err: any) {
        if (!cancelled) setError(err.message || "Failed to run batch audit");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    runAudit();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center gap-4 text-center">
        <Loader2 className="animate-spin text-brand" size={32} />
        <p className="text-sm font-semibold">Running Household Safety Audit...</p>
        <p className="text-xs text-fg-subtle">Checking {items.length} items against all profiles.</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 text-center">
        <p className="mb-4 text-unsafe">{error}</p>
        <Button onClick={() => router.push("/")}>Go Back</Button>
      </div>
    );
  }

  const { summary, items: matrixItems } = data;
  const isSafe = summary.household_verdict === "SAFE";

  return (
    <div className="space-y-6 pb-20">
      <header className="flex items-center gap-3">
        <button
          onClick={() => router.push("/")}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface transition-colors hover:bg-surface-hover"
          aria-label="Go back"
        >
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-xl font-bold">Batch Audit Results</h1>
      </header>

      {/* Bento Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <div className={cn(
          "col-span-2 sm:col-span-1 rounded-3xl p-5 flex flex-col justify-between aspect-[2/1] sm:aspect-square",
          isSafe ? "bg-safe-soft text-safe border border-safe-border" : "bg-unsafe-soft text-unsafe border border-unsafe-border"
        )}>
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-current/80">Household Clear</h2>
            {isSafe ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
          </div>
          <p className="text-3xl font-black mt-2 tracking-tight">
            {isSafe ? "SAFE" : summary.household_verdict}
          </p>
        </div>
        
        <div className="rounded-3xl bg-surface border border-border p-5 flex flex-col justify-between aspect-square">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-fg-subtle">Total Scanned</h2>
            <Package size={20} className="text-fg-subtle" />
          </div>
          <p className="text-4xl font-bold">{summary.total_scanned}</p>
        </div>
        
        <div className="rounded-3xl bg-surface border border-border p-5 flex flex-col justify-between aspect-square">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-fg-subtle">Flagged Items</h2>
            <AlertTriangle size={20} className={summary.flagged_items > 0 ? "text-unsafe" : "text-fg-subtle"} />
          </div>
          <p className="text-4xl font-bold">{summary.flagged_items}</p>
        </div>
      </div>

      <HouseholdSafetyMatrix items={matrixItems} profiles={profiles} />
      
      <div className="flex gap-3">
        <Button 
          variant="secondary"
          onClick={() => router.push("/")} 
          className="flex-1"
        >
          Scan More
        </Button>
        <Button 
          onClick={() => {
            clearCart();
            router.push("/");
          }} 
          className="flex-1"
        >
          Clear Cart & Done
        </Button>
      </div>
    </div>
  );
}
