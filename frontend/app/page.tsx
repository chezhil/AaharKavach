"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, ScanLine, Sparkles } from "lucide-react";
import { ProfileSwitcher } from "@/components/profiles/ProfileSwitcher";
import { ScanSheet } from "@/components/scanner/ScanSheet";
import { HistoryRow } from "@/components/history/HistoryRow";
import { Button } from "@/components/ui/Button";
import { api, ProductNotFoundError, runScan } from "@/lib/api";
import { useApp } from "@/lib/store/app-store";

export default function ScanPage() {
  const router = useRouter();
  const { activeIds, activeProfiles, addScan, history } = useApp();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBarcode = useCallback(
    async (barcode: string) => {
      setBusy(true);
      setError(null);
      try {
        const scan = await runScan({ barcode }, activeIds);
        addScan(scan);
        setOpen(false);
        router.push(`/result/${scan.product.barcode}`);
      } catch (err) {
        setError(
          err instanceof ProductNotFoundError
            ? `Barcode ${err.barcode} isn't in Open Food Facts. Try photographing the label instead.`
            : "Something went wrong looking that up. Try again in a moment.",
        );
      } finally {
        setBusy(false);
      }
    },
    [activeIds, addScan, router],
  );

  const handleLabelPhoto = useCallback(
    async (file: File) => {
      setBusy(true);
      setError(null);
      try {
        const product = await api.scanLabel(file);
        const scan = await runScan({ product }, activeIds);
        addScan(scan);
        setOpen(false);
        router.push(`/result/${scan.product.barcode}`);
      } catch {
        setError("We couldn't read that label. Try a straighter, brighter photo.");
      } finally {
        setBusy(false);
      }
    },
    [activeIds, addScan, router],
  );

  const names = activeProfiles.map((p) => p.name);
  const checkingLine =
    names.length === 0
      ? "Pick who this is for"
      : names.length === 1
        ? `Checking for ${names[0]}`
        : names.length === 2
          ? `Checking for ${names[0]} and ${names[1]}`
          : `Checking for ${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;

  const recent = history.slice(0, 3);

  return (
    <div className="space-y-7">
      <ProfileSwitcher />

      <section className="space-y-3">
        <button
          onClick={() => {
            setError(null);
            setOpen(true);
          }}
          className="group relative w-full overflow-hidden rounded-3xl border border-border-subtle bg-surface px-6 py-9 text-center transition-colors hover:border-brand"
        >
          <span
            aria-hidden
            className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-brand-soft to-transparent opacity-60"
          />
          <span className="relative flex flex-col items-center gap-3">
            <span className="grid size-16 place-items-center rounded-2xl bg-brand text-brand-fg transition-transform group-hover:scale-105">
              <ScanLine size={30} strokeWidth={2.2} />
            </span>
            <span className="text-lg font-bold tracking-tight">Scan a product</span>
            <span className="max-w-[28ch] text-sm text-fg-subtle">{checkingLine}</span>
          </span>
        </button>

        <p className="flex items-center justify-center gap-1.5 text-xs text-fg-subtle">
          <Sparkles size={12} aria-hidden />
          Hidden names, E-numbers and cross-reactions, all explained
        </p>
      </section>

      {recent.length > 0 ? (
        <section className="space-y-2.5">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="text-sm font-semibold text-fg-muted">Recent scans</h2>
            <Link
              href="/history"
              className="flex items-center gap-1 text-xs font-semibold text-brand"
            >
              See all <ArrowRight size={12} />
            </Link>
          </div>
          <ul className="space-y-2">
            {recent.map((scan) => (
              <HistoryRow key={scan.id} scan={scan} />
            ))}
          </ul>
        </section>
      ) : (
        <section className="rounded-2xl border border-border-subtle bg-surface p-4">
          <h2 className="text-sm font-bold">How it reads a label</h2>
          <ol className="mt-3 space-y-2.5 text-sm text-fg-muted">
            {[
              "Looks the barcode up in Open Food Facts.",
              "Expands every ingredient through an allergen synonym index — casein becomes dairy, E120 becomes carmine.",
              "Checks each selected person separately, and scales the warning to their severity.",
              "Tells you how sure it is, so a thin record never reads as a confident all-clear.",
            ].map((step, i) => (
              <li key={i} className="flex gap-2.5">
                <span className="grid size-5 shrink-0 place-items-center rounded-full bg-brand-soft text-[0.65rem] font-bold text-brand">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
          <Button
            variant="secondary"
            className="mt-4 w-full"
            onClick={() => {
              setError(null);
              setOpen(true);
            }}
          >
            Try it with the demo catalogue
          </Button>
        </section>
      )}

      <ScanSheet
        open={open}
        onClose={() => setOpen(false)}
        onBarcode={handleBarcode}
        onLabelPhoto={handleLabelPhoto}
        busy={busy}
        error={error}
      />
    </div>
  );
}
