"use client";

import { useState } from "react";
import { Sheet } from "@/components/ui/Sheet";
import { Button } from "@/components/ui/Button";
import { MOCK_PRODUCTS } from "@/lib/mocks/fixtures";
import { usingMocks } from "@/lib/api";
import { useApp } from "@/lib/store/app-store";
import { isValidBarcode } from "@/lib/utils";

interface Props {
  open: boolean;
  onClose: () => void;
  onPick: (barcode: string) => void;
  /** Already chosen in the other slot — hidden so you can't compare a thing to itself. */
  exclude?: string | null;
}

export function ProductPicker({ open, onClose, onPick, exclude }: Props) {
  const { history } = useApp();
  const [typed, setTyped] = useState("");

  const recent = history.filter((s) => s.product.barcode !== exclude).slice(0, 6);
  const catalogue = MOCK_PRODUCTS.filter(
    (p) => p.barcode !== exclude && !recent.some((s) => s.product.barcode === p.barcode),
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

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title="Pick a product"
      description="Choose from what you've scanned, or enter a barcode."
    >
      <div className="space-y-5">
        <div className="flex gap-2">
          <input
            value={typed}
            onChange={(e) => setTyped(e.target.value.replace(/\D/g, ""))}
            onKeyDown={(e) => {
              if (e.key === "Enter" && isValidBarcode(typed)) {
                onPick(typed.trim());
                onClose();
              }
            }}
            inputMode="numeric"
            placeholder="Barcode number"
            aria-label="Barcode number"
            className="h-11 flex-1 rounded-xl border border-border-subtle bg-bg px-3.5 font-mono text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
          />
          <Button
            disabled={!isValidBarcode(typed)}
            onClick={() => {
              onPick(typed.trim());
              onClose();
            }}
          >
            Use
          </Button>
        </div>

        {recent.length > 0 ? (
          <section className="space-y-2">
            <h3 className="text-sm font-semibold text-fg-muted">Recently scanned</h3>
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
            <h3 className="text-sm font-semibold text-fg-muted">Demo catalogue</h3>
            <ul className="space-y-1.5">
              {catalogue.map((product) =>
                row(product.barcode, product.name, product.brand ?? product.barcode),
              )}
            </ul>
          </section>
        ) : null}
      </div>
    </Sheet>
  );
}
