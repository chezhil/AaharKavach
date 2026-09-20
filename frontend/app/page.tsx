"use client";

import { Suspense, useCallback, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Columns2, ScanLine, UserPlus, Users } from "lucide-react";
import { ProfileSwitcher } from "@/components/profiles/ProfileSwitcher";
import { ScanSheet, type ScanMode } from "@/components/scanner/ScanSheet";
import { HistoryRow } from "@/components/history/HistoryRow";
import { Button } from "@/components/ui/Button";
import { ApiError, ProductNotFoundError, api, runScan, runUrlScan } from "@/lib/api";
import { useApp } from "@/lib/store/app-store";

// Distinct alias/synonym strings across data/mappings/allergen_synonyms.py's
// ALLERGENS (aliases + synonym_terms) and e_numbers.py's E_NUMBERS aliases —
// i.e. label words that actually resolve to a hidden allergen, which is what
// this stat claims. Recompute after editing either table:
//   names = {a.lower() for entry in ALLERGENS.values()
//            for a in entry["aliases"] + [t["term"] for t in entry["synonym_terms"]]}
//   names |= {a.lower() for e in E_NUMBERS for a in e["aliases"]}
//   len(names)
const SYNONYM_COUNT = 302;

function ScanHome() {
  const router = useRouter();
  const params = useSearchParams();
  const { activeIds, activeProfiles, addScan, history, profiles, loading, error: loadError } = useApp();

  // `/?scan=photo` is how the "not in the database" screen hands over.
  const requested = params.get("scan");
  const initialMode: ScanMode =
    requested === "photo" ? "photo" : requested === "manual" ? "manual" : "camera";
  const [open, setOpen] = useState(requested !== null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyMessage, setBusyMessage] = useState<{title: string, desc: string} | undefined>(undefined);

  const handleBarcode = useCallback(
    async (barcode: string) => {
      setBusy(true);
      setError(null);
      try {
        let scan;
        if (barcode.startsWith("http://") || barcode.startsWith("https://")) {
            setBusyMessage({
                title: "Smart QR Code detected! Analyzing product page...",
                desc: "Extracting ingredients from the webpage and reasoning over them."
            });
            scan = await runUrlScan(barcode, activeIds);
        } else {
            setBusyMessage(undefined);
            scan = await runScan({ barcode }, activeIds);
        }
        addScan(scan);
        setOpen(false);
        router.push(`/result/${encodeURIComponent(scan.product.barcode)}`);
      } catch (err) {
        // The API's messages are written for people — "that link points to a
        // private address", "the AI reader isn't switched on". Burying them
        // behind one generic line sends users to debug the wrong thing.
        setError(
          err instanceof ProductNotFoundError
            ? `Barcode ${err.barcode} isn't in Open Food Facts. Try photographing the label instead.`
            : err instanceof ApiError && err.message
              ? err.message
              : "Something went wrong looking that up. Try again in a moment.",
        );
      } finally {
        setBusy(false);
        setBusyMessage(undefined);
      }
    },
    [activeIds, addScan, router],
  );

  const handleLabelPhoto = useCallback(
    async (file: File | string) => {
      setBusy(true);
      setError(null);
      try {
        const product = await api.scanLabel(file);
        const scan = await runScan({ product }, activeIds);
        addScan(scan);
        setOpen(false);
        router.push(`/result/${encodeURIComponent(scan.product.barcode)}`);
      } catch {
        setError(
          "We couldn't read that label. Try a straighter, brighter photo.",
        );
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
        ? `for ${names[0]}`
        : names.length === 2
          ? `for ${names[0]} and ${names[1]}`
          : `for ${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;

  const recent = history.slice(0, 3);
  const noProfiles = !loading && profiles.length === 0;
  const launch = () => {
    setError(null);
    setOpen(true);
  };

  return (
    <div className="space-y-3">
      {/* The household couldn't be fetched at all — say so instead of showing
          an app that looks empty for no reason. */}
      {loadError ? (
        <p
          role="alert"
          className="rounded-xl border border-unsafe-border bg-unsafe-soft px-3 py-2.5 text-sm text-unsafe"
        >
          {loadError} Your household and history couldn&apos;t be loaded — check the
          connection and reload.
        </p>
      ) : null}

      <ProfileSwitcher />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {noProfiles ? (
          <Link
            href="/profiles"
            className="tile group relative col-span-2 flex min-h-[11.5rem] flex-col bg-brand p-5 text-brand-fg md:row-span-2 md:min-h-[21rem] md:p-6"
          >
            <span className="grid size-14 place-items-center rounded-2xl bg-brand-fg/15 transition-transform group-hover:scale-105">
              <UserPlus size={28} strokeWidth={2.5} />
            </span>
            <span className="display mt-auto pt-6 text-[2rem] md:text-[3rem]">
              Add someone
              <br />
              first
            </span>
            <span className="mt-1.5 text-sm font-bold opacity-75">
              There&apos;s nobody to check a product against yet.
            </span>
          </Link>
        ) : (
          <button
            onClick={launch}
            className="tile group relative col-span-2 min-h-[11.5rem] bg-brand p-5 text-left text-brand-fg md:row-span-2 md:min-h-[21rem] md:p-6"
          >
            <span
              aria-hidden
              className="display pointer-events-none absolute -right-4 bottom-0 select-none text-[5.5rem] leading-none opacity-[0.11] md:text-[9rem]"
            >
              कवच
            </span>
            <span className="relative flex h-full flex-col">
              <span className="grid size-14 place-items-center rounded-2xl bg-brand-fg/15 transition-transform group-hover:scale-105">
                <ScanLine size={28} strokeWidth={2.5} />
              </span>
              <span className="display mt-auto pt-6 text-[2rem] md:text-[3rem]">
                Scan a
                <br />
                product
              </span>
              <span className="mt-1.5 text-sm font-bold opacity-75">{checkingLine}</span>
            </span>
          </button>
        )}

        <Link
          href="/profiles"
          className="tile flex flex-col bg-sky p-4 text-sky-fg transition-[filter] hover:brightness-105"
        >
          <Users size={20} strokeWidth={2.5} />
          <p className="display mt-auto pt-6 text-[2.5rem]">
            {profiles.length}
          </p>
          <p className="text-xs font-bold uppercase tracking-wider opacity-70">
            in the household
          </p>
        </Link>

        <div className="tile flex flex-col bg-surface p-4">
          <p className="display text-[2.5rem] text-brand-line">
            {SYNONYM_COUNT}
          </p>
          <p className="text-xs font-bold uppercase tracking-wider text-fg-subtle">
            hidden allergen names indexed
          </p>
          <p className="mt-2 text-xs leading-relaxed text-fg-subtle">
            Casein, whey, maida, E322 — all traced back to the allergen they
            are.
          </p>
        </div>

        <Link
          href="/compare"
          className="tile col-span-2 flex items-center gap-3 bg-surface p-4 transition-colors hover:bg-surface-hover md:col-span-2"
        >
          <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-sky text-sky-fg">
            <Columns2 size={20} strokeWidth={2.5} />
          </span>
          <span className="min-w-0 flex-1">
            <span className="display block text-base">
              Compare two products
            </span>
            <span className="mt-0.5 block text-xs text-fg-subtle">
              See which one clears more of your household
            </span>
          </span>
          <ArrowRight
            size={18}
            className="shrink-0 text-fg-subtle"
            aria-hidden
          />
        </Link>
      </div>

      {recent.length > 0 ? (
        <section className="tile bg-surface p-3.5">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="display text-sm">Recent scans</h2>
            <Link href="/history" className="text-xs font-bold text-brand-line">
              See all
            </Link>
          </div>
          <ul className="mt-3 grid gap-2 md:grid-cols-2 lg:grid-cols-3">
            {recent.map((scan) => (
              <HistoryRow key={scan.id} scan={scan} />
            ))}
          </ul>
        </section>
      ) : (
        <section className="tile bg-surface p-4">
          <h2 className="display text-base">How it reads a label</h2>
          <ol className="mt-3 grid gap-2.5 text-sm text-fg-muted md:grid-cols-2">
            {[
              "Looks the barcode up in Open Food Facts.",
              "Expands every ingredient through an allergen synonym index — casein becomes dairy, E120 becomes carmine.",
              "Checks each selected person separately, and scales the warning to their severity.",
              "Tells you how sure it is, so a thin record never reads as a confident all-clear.",
            ].map((step, i) => (
              <li key={i} className="flex gap-2.5">
                <span className="grid size-5 shrink-0 place-items-center rounded-md bg-brand text-[0.65rem] font-extrabold text-brand-fg">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{step}</span>
              </li>
            ))}
          </ol>
          <Button
            variant="sky"
            className="mt-4 w-full md:w-auto"
            onClick={launch}
          >
            Try it with the demo catalogue
          </Button>
        </section>
      )}

      <ScanSheet
        // Remount when the deep link asks for a different tab.
        key={initialMode}
        open={open}
        onClose={() => setOpen(false)}
        onBarcode={handleBarcode}
        onLabelPhoto={handleLabelPhoto}
        busy={busy}
        busyMessage={busyMessage}
        error={error}
        initialMode={initialMode}
      />
    </div>
  );
}

export default function ScanPage() {
  return (
    <Suspense fallback={<p className="py-10 text-center text-sm text-fg-subtle">Loading…</p>}>
      <ScanHome />
    </Suspense>
  );
}
