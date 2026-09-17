import { Camera, Package, ScanBarcode } from "lucide-react";
import type { Product } from "@/lib/types";

const SOURCE_LABEL = {
  OPEN_FOOD_FACTS: { icon: ScanBarcode, text: "Open Food Facts" },
  LABEL_PHOTO: { icon: Camera, text: "Read from label photo" },
  MANUAL: { icon: Package, text: "Entered manually" },
} as const;

export function ProductHeader({ product }: { product: Product }) {
  const source = SOURCE_LABEL[product.source];
  const Icon = source.icon;

  return (
    <div className="flex items-start gap-3">
      <div className="grid size-14 shrink-0 place-items-center rounded-2xl border border-border-subtle bg-surface text-fg-subtle">
        <Package size={22} />
      </div>
      <div className="min-w-0 flex-1">
        {product.brand ? (
          <p className="text-xs font-semibold uppercase tracking-wide text-fg-subtle">
            {product.brand}
          </p>
        ) : null}
        <h1 className="mt-0.5 text-lg font-bold leading-tight tracking-tight">
          {product.name}
        </h1>
        <p className="mt-1 flex items-center gap-1.5 text-xs text-fg-subtle">
          <Icon size={12} aria-hidden />
          {source.text}
          {product.source !== "LABEL_PHOTO" ? (
            <span className="font-mono">· {product.barcode}</span>
          ) : null}
        </p>
      </div>
    </div>
  );
}
