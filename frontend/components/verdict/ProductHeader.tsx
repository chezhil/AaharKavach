import { Camera, Database, Package, ScanBarcode } from "lucide-react";
import type { Product } from "@/lib/types";

const SOURCE_LABEL: Record<string, { icon: typeof Package; text: string }> = {
  OPEN_FOOD_FACTS: { icon: ScanBarcode, text: "Open Food Facts" },
  LABEL_PHOTO: { icon: Camera, text: "Read from label photo" },
  MANUAL: { icon: Package, text: "Entered manually" },
  OFFLINE_CATALOGUE: { icon: Database, text: "Offline catalogue" },
};

// A source the backend adds later must not white-screen the result page.
const UNKNOWN_SOURCE = { icon: Package, text: "Unknown source" };

export function ProductHeader({ product }: { product: Product }) {
  const source = SOURCE_LABEL[product.source] ?? UNKNOWN_SOURCE;
  const Icon = source.icon;

  return (
    <div className="tile flex items-center gap-3.5 bg-surface p-4">
      <div className="grid size-14 shrink-0 place-items-center rounded-2xl bg-brand text-brand-fg">
        <Package size={24} strokeWidth={2.2} />
      </div>
      <div className="min-w-0 flex-1">
        {product.brand ? (
          <p className="text-[0.68rem] font-bold uppercase tracking-wider text-brand-line">
            {product.brand}
          </p>
        ) : null}
        <h1 className="display mt-1 text-xl">{product.name}</h1>
        <p className="mt-1.5 flex items-center gap-1.5 text-xs text-fg-subtle">
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
