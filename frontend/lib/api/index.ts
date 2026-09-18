import type { EvaluateRequest, Product, ScanResult } from "@/lib/types";
import { httpApi } from "./client";
import { mockApi } from "./mock";
import type { AaharApi } from "./types";

const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";

/**
 * Mocks are the default so `npm run dev` works with nothing else running.
 * Set NEXT_PUBLIC_USE_MOCKS=false once Role 3's API is up.
 */
export const api: AaharApi = useMocks ? mockApi : httpApi;

export const usingMocks = useMocks;

/** Scan + evaluate + log, as one call, since every screen wants all three. */
export async function runScan(
  input: { barcode: string } | { product: Product },
  profileIds: string[],
): Promise<ScanResult> {
  const product =
    "product" in input ? input.product : await api.scanBarcode(input.barcode);
  const req: EvaluateRequest =
    product.source === "LABEL_PHOTO"
      ? { product, profile_ids: profileIds }
      : { barcode: product.barcode, profile_ids: profileIds };
  const evaluation = await api.evaluate(req);
  const scan: ScanResult = {
    id: `scan_${Math.random().toString(36).slice(2, 10)}`,
    scanned_at: new Date().toISOString(),
    product,
    evaluation,
    profile_ids: profileIds,
  };
  await api.recordScan(scan);
  return scan;
}

export { ProductNotFoundError, ApiError } from "./types";
export type { AaharApi } from "./types";
