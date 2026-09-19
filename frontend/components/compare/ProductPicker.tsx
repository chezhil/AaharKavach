"use client";

import { useCallback, useRef, useState } from "react";
import { Camera, ImagePlus, Keyboard, Loader2 } from "lucide-react";
import { Sheet } from "@/components/ui/Sheet";
import { Button } from "@/components/ui/Button";
import { BarcodeScanner } from "@/components/scanner/BarcodeScanner";
import { MOCK_PRODUCTS } from "@/lib/mocks/fixtures";
import { usingMocks } from "@/lib/api";
import { useApp } from "@/lib/store/app-store";
import { cn, isValidBarcode } from "@/lib/utils";

type ScanMode = "camera" | "manual" | "photo";

const MODES: Array<{ id: ScanMode; label: string; icon: typeof Camera }> = [
  { id: "camera", label: "Camera", icon: Camera },
  { id: "manual", label: "Type it", icon: Keyboard },
  { id: "photo", label: "Label photo", icon: ImagePlus },
];

interface Props {
  open: boolean;
  onClose: () => void;
  onPick: (value: string | File) => void;
  exclude?: string | null;
}

export function ProductPicker({ open, onClose, onPick, exclude }: Props) {
  const { history } = useApp();
  const [mode, setMode] = useState<ScanMode>("camera");
  const [typed, setTyped] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  const recent = history
    .filter((s) => s.product.barcode !== exclude)
    .slice(0, 6);
  const catalogue = MOCK_PRODUCTS.filter(
    (p) =>
      p.barcode !== exclude &&
      !recent.some((s) => s.product.barcode === p.barcode),
  );

  const row = (barcode: string, name: string, sub: string) => (
    <li key={barcode}>
      <button
        onClick={() => {
          onPick(barcode);
          onClose();
        }}
        className="flex w-full items-center gap-3 rounded-xl border border-border-subtle bg-surface px-3 py-2.5 text-left transition-colors hover:border-brand"
      >
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold">{name}</span>
          <span className="block truncate text-xs text-fg-subtle">{sub}</span>
        </span>
      </button>
    </li>
  );

  const handleDetected = useCallback(
    (barcode: string) => {
      if (navigator.vibrate) navigator.vibrate(40);
      onPick(barcode);
      onClose();
    },
    [onPick, onClose],
  );

  const submitTyped = () => {
    if (!isValidBarcode(typed) && !typed.startsWith("http")) return;
    onPick(typed.trim());
    onClose();
  };

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title="Pick a product"
      description="Scan, type, or pick from recent history."
    >
      <div className="space-y-5">
        <div
          role="tablist"
          className="grid grid-cols-3 gap-1 rounded-xl bg-bg p-1"
        >
          {MODES.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              role="tab"
              aria-selected={mode === id}
              onClick={() => setMode(id)}
              className={cn(
                "flex items-center justify-center gap-1.5 rounded-lg px-2 py-2 text-xs font-semibold transition-colors",
                mode === id
                  ? "bg-brand text-brand-fg"
                  : "text-fg-subtle hover:text-fg-muted",
              )}
            >
              <Icon size={14} aria-hidden />
              {label}
            </button>
          ))}
        </div>

        {mode === "camera" ? (
          <BarcodeScanner onDetected={handleDetected} onCaptureLabel={(f) => { onPick(f); onClose(); }} />
        ) : null}

        {mode === "manual" ? (
          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                value={typed}
                onChange={(e) => setTyped(e.target.value.trim())}
                onKeyDown={(e) => {
                  if (e.key === "Enter") submitTyped();
                }}
                inputMode="text"
                placeholder="Barcode number or https://..."
                className="h-11 flex-1 rounded-xl border border-border-subtle bg-bg px-3.5 font-mono text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
              />
              <Button
                disabled={(!isValidBarcode(typed) && !typed.startsWith("http")) || !typed}
                onClick={submitTyped}
              >
                Use
              </Button>
            </div>
            <p className="text-xs text-fg-subtle">
              8 to 14 digits, printed under the bars.
            </p>
          </div>
        ) : null}

        {mode === "photo" ? (
          <div className="space-y-3">
            <button
              onClick={() => fileInput.current?.click()}
              className="flex w-full flex-col items-center gap-2 rounded-2xl border border-dashed border-border-strong px-5 py-10 text-center transition-colors hover:border-brand"
            >
              <ImagePlus size={24} className="text-fg-subtle" aria-hidden />
              <span className="text-sm font-semibold">
                Upload or snap a photo
              </span>
            </button>
            <input
              ref={fileInput}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  onPick(file);
                  onClose();
                }
              }}
            />
          </div>
        ) : null}

        {recent.length > 0 ? (
          <section className="space-y-2 mt-4">
            <h3 className="text-sm font-semibold text-fg-muted">
              Recently scanned
            </h3>
            <ul className="space-y-1.5">
              {recent.map((scan) =>
                row(
                  scan.product.barcode,
                  scan.product.name,
                  scan.product.brand ?? scan.product.barcode,
                ),
              )}
            </ul>
          </section>
        ) : null}

        {usingMocks && catalogue.length > 0 ? (
          <section className="space-y-2">
            <h3 className="text-sm font-semibold text-fg-muted">
              Demo catalogue
            </h3>
            <ul className="space-y-1.5">
              {catalogue.map((product) =>
                row(
                  product.barcode,
                  product.name,
                  product.brand ?? product.barcode,
                ),
              )}
            </ul>
          </section>
        ) : null}
      </div>
    </Sheet>
  );
}
