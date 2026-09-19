"use client";

import { useCallback, useRef, useState, useEffect } from "react";
import { Camera, ImagePlus, Keyboard, Loader2, ShoppingCart, X, ArrowRight } from "lucide-react";
import { Sheet } from "@/components/ui/Sheet";
import { Button } from "@/components/ui/Button";
import { BarcodeScanner } from "./BarcodeScanner";
import { MOCK_PRODUCTS } from "@/lib/mocks/fixtures";
import { usingMocks } from "@/lib/api";
import { cn, isValidBarcode } from "@/lib/utils";
import { useCartStore } from "@/stores/useCartStore";
import { useRouter } from "next/navigation";

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
  onLabelPhoto: (file: File | string) => void;
  busy?: boolean;
  busyMessage?: { title: string, desc: string };
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
  busyMessage,
  error,
  initialMode = "camera",
}: Props) {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [typed, setTyped] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  
  const { batchMode, toggleBatchMode, items, addItem, removeItem, clearCart } = useCartStore();
  const router = useRouter();

  const handleAuditBatch = () => {
    if (items.length === 0) return;
    onClose();
    router.push("/batch-result");
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64 = event.target?.result as string;
      if (base64) {
        onLabelPhoto(base64);
      }
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file || !file.type.startsWith("image/")) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64 = event.target?.result as string;
      if (base64) {
        onLabelPhoto(base64);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleTabChange = (newTab: Mode) => {
    if (newTab !== "camera") {
      if (typeof document !== "undefined") {
        document.querySelectorAll("video").forEach((v) => {
          if (v.srcObject) {
            (v.srcObject as MediaStream).getTracks().forEach((t) => t.stop());
            v.srcObject = null;
          }
        });
      }
    }
    setMode(newTab);
  };

  const handleClose = useCallback(() => {
    if (typeof document !== "undefined") {
      document.querySelectorAll("video").forEach((v) => {
        if (v.srcObject) {
          (v.srcObject as MediaStream).getTracks().forEach((t) => t.stop());
          v.srcObject = null;
        }
      });
    }
    onClose();
  }, [onClose]);

  // Stable identity: BarcodeScanner restarts the camera when this changes.
  const handleDetected = useCallback(
    (barcode: string) => {
      if (navigator.vibrate) navigator.vibrate(40);
      
      if (batchMode) {
        addItem(barcode);
        setToastMessage(`Added ${barcode} to Cart`);
        setTimeout(() => setToastMessage(null), 2000);
      } else {
        onBarcode(barcode);
      }
    },
    [onBarcode, batchMode, addItem],
  );

  const submitTyped = () => {
    if ((!isValidBarcode(typed) && !typed.startsWith("http")) || !typed) return;
    onBarcode(typed.trim());
  };

  return (
    <Sheet
      open={open}
      onClose={handleClose}
      title="Scan a product"
      description="Point at the barcode, type it, or photograph the ingredients panel."
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <div
            role="tablist"
            aria-label="Scan method"
            className="flex w-[200px] gap-1 rounded-xl bg-bg p-1"
          >
            {MODES.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                role="tab"
                aria-selected={mode === id}
                onClick={() => handleTabChange(id)}
                className={cn(
                  "flex flex-1 items-center justify-center gap-1.5 rounded-lg px-2 py-2 text-xs font-semibold transition-colors",
                  mode === id
                    ? "bg-brand text-brand-fg"
                    : "text-fg-subtle hover:text-fg-muted",
                )}
              >
                <Icon size={14} aria-hidden />
                <span className="sr-only sm:not-sr-only sm:inline-block">{label}</span>
              </button>
            ))}
          </div>
          
          <button
            onClick={toggleBatchMode}
            className={cn(
              "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors border",
              batchMode 
                ? "bg-brand/10 border-brand text-brand"
                : "bg-surface border-border-subtle text-fg-subtle hover:bg-surface-hover"
            )}
          >
            <ShoppingCart size={14} />
            {batchMode ? "Batch Mode ON" : "Batch Mode OFF"}
          </button>
        </div>

        {error && !busy ? (
          error.includes("isn't in Open Food Facts") ? (
            <div className="rounded-xl border border-border bg-surface p-4 text-center">
              <h3 className="font-semibold mb-1">Product not in database yet</h3>
              <p className="text-sm text-fg-subtle mb-4">
                Snap a photo of the ingredients list on the back of the package to evaluate it now.
              </p>
              <Button onClick={() => setMode("camera")} className="w-full">
                Open Camera & Snap Ingredients
              </Button>
            </div>
          ) : (
            <p
              role="alert"
              className="rounded-xl border border-unsafe-border bg-unsafe-soft px-3 py-2.5 text-sm text-unsafe"
            >
              {error}
            </p>
          )
        ) : null}

        {busy ? (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-border-subtle bg-surface px-5 py-10 text-center">
            <Loader2
              size={22}
              className="animate-spin text-brand"
              aria-hidden
            />
            <p className="text-sm font-semibold">
              {busyMessage?.title || "Checking against your household?"}
            </p>
            <p className="text-xs text-fg-subtle">
              {busyMessage?.desc || "Looking up the product, then reasoning over every ingredient."}
            </p>
          </div>
        ) : (
          <div className="relative">
            {mode === "camera" ? (
              <BarcodeScanner onDetected={handleDetected} onCaptureLabel={onLabelPhoto} batchMode={batchMode} />
            ) : null}

            {batchMode && items.length > 0 && mode === "camera" && (
              <div className="absolute bottom-4 left-4 right-4 z-10 flex flex-col gap-2 rounded-2xl border border-border bg-surface/95 backdrop-blur shadow-lg p-3">
                <div className="flex items-center justify-between text-sm font-semibold">
                  <span>🛒 {items.length} {items.length === 1 ? "Item" : "Items"} in Cart</span>
                  <button onClick={clearCart} className="text-xs text-fg-subtle hover:text-fg-muted underline">Clear</button>
                </div>
                
                <div className="flex overflow-x-auto gap-2 pb-1 scrollbar-hide">
                  {items.map((item) => (
                    <div key={item.barcode} className="relative flex shrink-0 items-center justify-center h-12 w-12 rounded-lg bg-bg border border-border-subtle">
                      <span className="text-[10px] text-fg-muted">{item.barcode.slice(-4)}</span>
                      <button 
                        onClick={() => removeItem(item.barcode)}
                        className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-fg text-bg"
                      >
                        <X size={10} />
                      </button>
                    </div>
                  ))}
                </div>
                
                <Button onClick={handleAuditBatch} className="w-full h-10 mt-1 shadow-sm">
                  Audit Household Cart <ArrowRight size={16} className="ml-1" />
                </Button>
              </div>
            )}
            
            {toastMessage && (
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 rounded-full bg-brand px-4 py-1.5 text-xs font-semibold text-brand-fg shadow-lg animate-in fade-in slide-in-from-top-2">
                {toastMessage}
              </div>
            )}

            {mode === "manual" ? (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <input
                    value={typed}
                    onChange={(e) =>
                      // Allow typing non-digits if the user might be typing a URL, 
                      // or just remove the replace restriction to support URLs and 
                      // rely on isValidBarcode or startsWith("http") for submission validation.
                      setTyped(e.target.value.trim())
                    }
                    onKeyDown={(e) => e.key === "Enter" && submitTyped()}
                    inputMode="text"
                    autoFocus
                    placeholder="8901063152762 or https://..."
                    aria-label="Barcode number or URL"
                    className="h-12 flex-1 rounded-xl border border-border-subtle bg-bg px-3.5 font-mono text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                  />
                  <Button
                    onClick={submitTyped}
                    disabled={(!isValidBarcode(typed) && !typed.startsWith("http")) || !typed}
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
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                  onClick={() => cameraInputRef.current?.click()}
                  className="group flex w-full cursor-pointer flex-col items-center gap-2 rounded-2xl border border-dashed border-border-strong px-5 py-8 text-center transition-colors hover:border-brand bg-bg/50 hover:bg-surface"
                >
                  <ImagePlus size={32} className="text-fg-subtle group-hover:text-brand transition-colors" aria-hidden />
                  <span className="text-base font-semibold">
                    Snap or Drop Ingredients
                  </span>
                  <span className="max-w-[32ch] text-xs text-fg-subtle">
                    Take a photo of the ingredients list on the back of the package.
                  </span>
                  
                  <div className="flex w-full gap-2 mt-4" onClick={(e) => e.stopPropagation()}>
                    <Button onClick={() => cameraInputRef.current?.click()} className="flex-1 text-sm bg-brand text-brand-fg">
                      Take Photo
                    </Button>
                    <Button variant="secondary" onClick={() => fileInputRef.current?.click()} className="flex-1 text-sm bg-surface hover:bg-surface-hover">
                      Choose File
                    </Button>
                  </div>
                </div>

                <input
                  ref={cameraInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileChange}
                />
                
                <p className="rounded-xl border border-caution-border bg-caution-soft px-3 py-2 text-xs text-caution">
                  Photo reads come back with low confidence — we&apos;ll say so on the result.
                </p>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </Sheet>
  );
}
