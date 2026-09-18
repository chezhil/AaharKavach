"use client";

import { useCallback, useRef, useState } from "react";
import { Camera, ImagePlus, Keyboard, Loader2 } from "lucide-react";
import { Sheet } from "@/components/ui/Sheet";
import { Button } from "@/components/ui/Button";
import { BarcodeScanner } from "./BarcodeScanner";
import { MOCK_PRODUCTS } from "@/lib/mocks/fixtures";
import { usingMocks } from "@/lib/api";
import { cn, isValidBarcode } from "@/lib/utils";

export type ScanMode = "camera" | "manual" | "photo";
type Mode = ScanMode;

const MODES: Array<{ id: Mode; label: string; icon: typeof Camera }> = [
  { id: "camera", label: "Camera", icon: Camera },
  { id: "manual", label: "Type it", icon: Keyboard },
  { id: "photo", label: "Label photo", icon: ImagePlus },
];

interface Props {
  open: boolean;
  onClose: () => void;
  onBarcode: (barcode: string) => void;
  onLabelPhoto: (file: File) => void;
  busy?: boolean;
  error?: string | null;
  /** Opens on this tab — used by the "photograph the label" deep link. */
  initialMode?: Mode;
}

export function ScanSheet({
  open,
  onClose,
  onBarcode,
  onLabelPhoto,
  busy,
  error,
  initialMode = "camera",
}: Props) {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [typed, setTyped] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  // Stable identity: BarcodeScanner restarts the camera when this changes.
  const handleDetected = useCallback(
    (barcode: string) => {
      if (navigator.vibrate) navigator.vibrate(40);
      onBarcode(barcode);
    },
    [onBarcode],
  );

  const submitTyped = () => {
    if (!isValidBarcode(typed)) return;
    onBarcode(typed.trim());
  };

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title="Scan a product"
      description="Point at the barcode, type it, or photograph the ingredients panel."
    >
      <div className="space-y-4">
        <div
          role="tablist"
          aria-label="Scan method"
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

        {error && !busy ? (
          <p
            role="alert"
            className="rounded-xl border border-unsafe-border bg-unsafe-soft px-3 py-2.5 text-sm text-unsafe"
          >
            {error}
          </p>
        ) : null}

        {busy ? (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-border-subtle bg-surface px-5 py-10 text-center">
            <Loader2
              size={22}
              className="animate-spin text-brand"
              aria-hidden
            />
            <p className="text-sm font-semibold">
              Checking against your household…
            </p>
            <p className="text-xs text-fg-subtle">
              Looking up the product, then reasoning over every ingredient.
            </p>
          </div>
        ) : (
          <>
            {mode === "camera" ? (
              <BarcodeScanner onDetected={handleDetected} />
            ) : null}

            {mode === "manual" ? (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <input
                    value={typed}
                    onChange={(e) =>
                      setTyped(e.target.value.replace(/\D/g, ""))
                    }
                    onKeyDown={(e) => e.key === "Enter" && submitTyped()}
                    inputMode="numeric"
                    autoFocus
                    placeholder="8901063152762"
                    aria-label="Barcode number"
                    className="h-12 flex-1 rounded-xl border border-border-subtle bg-bg px-3.5 font-mono text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                  />
                  <Button
                    onClick={submitTyped}
                    disabled={!isValidBarcode(typed)}
                  >
                    Check
                  </Button>
                </div>
                <p className="text-xs text-fg-subtle">
                  8 to 14 digits, printed under the bars.
                </p>

                {usingMocks ? (
                  <div className="space-y-2 rounded-xl border border-border-subtle bg-surface p-3">
                    <p className="text-xs font-semibold text-fg-muted">
                      Demo catalogue — tap to try
                    </p>
                    <ul className="space-y-1">
                      {MOCK_PRODUCTS.slice(0, 5).map((product) => (
                        <li key={product.barcode}>
                          <button
                            onClick={() => onBarcode(product.barcode)}
                            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-surface-hover"
                          >
                            <span className="min-w-0 flex-1 truncate text-sm">
                              {product.name}
                            </span>
                            <span className="shrink-0 font-mono text-[0.65rem] text-fg-subtle">
                              {product.barcode}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
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
                    Photograph the ingredients panel
                  </span>
                  <span className="max-w-[32ch] text-xs text-fg-subtle">
                    For loose or unlisted products with no barcode in the
                    database.
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
                    if (file) onLabelPhoto(file);
                    e.target.value = "";
                  }}
                />
                <p className="rounded-xl border border-caution-border bg-caution-soft px-3 py-2 text-xs text-caution">
                  Photo reads come back with low confidence — we&apos;ll say so
                  on the result.
                </p>
              </div>
            ) : null}
          </>
        )}
      </div>
    </Sheet>
  );
}
