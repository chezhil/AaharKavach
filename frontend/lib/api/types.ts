import type {
  BatchAuditResult,
  CompareRequest,
  CompareResult,
  EvaluateRequest,
  EvaluationResult,
  Product,
  Profile,
  ProfileDraft,
  ScanResult,
} from "@/lib/types";

/**
 * The surface Role 3's API has to satisfy. Components only ever talk to this,
 * so swapping mocks for the real Lambda endpoints is a one-line env change.
 */
export interface AaharApi {
  /** GET /api/profiles */
  listProfiles(): Promise<Profile[]>;
  /** POST /api/profiles */
  createProfile(draft: ProfileDraft): Promise<Profile>;
  /** PUT /api/profiles/{id} */
  updateProfile(id: string, draft: ProfileDraft): Promise<Profile>;
  /** DELETE /api/profiles/{id} */
  deleteProfile(id: string): Promise<void>;
  /** GET /api/scan/barcode?code={barcode} */
  scanBarcode(barcode: string): Promise<Product>;
  /** POST /api/scan/label (multipart: image or json {image_data}) */
  scanLabel(file: File | string): Promise<Product>;
  /** POST /api/scan/url */
  scanUrl(url: string, profile_ids: string[]): Promise<ScanResult>;
  /** POST /api/evaluate */
  evaluate(req: EvaluateRequest): Promise<EvaluationResult>;
  /** POST /api/compare */
  compare(req: CompareRequest): Promise<CompareResult>;
  /** POST /api/audit/batch */
  auditBatch(barcodes: string[]): Promise<BatchAuditResult>;
  /** GET /api/history */
  listHistory(): Promise<ScanResult[]>;
  /**
   * GET /api/explain?ingredient={name} — for a token the curated knowledge
   * base has no write-up for. The backend caches whatever the model returns,
   * so a second ask for the same ingredient never re-invokes it.
   */
  explainIngredient(name: string): Promise<{ explainer: string | null }>;
  /** Log a scan manually (noop on client). */
  recordScan(result: ScanResult): Promise<void>;
  /** POST /api/auth/signin */
  signIn(req: any): Promise<any>;
  /** GET /api/auth/me */
  getMe(): Promise<any>;
  /**
   * POST /api/history — the real backend logs a scan as a side effect of
   * /api/evaluate, so the HTTP client makes this a no-op. The mock needs it.
   */
  recordScan(scan: ScanResult): Promise<void>;
}

export class ProductNotFoundError extends Error {
  constructor(public barcode: string) {
    super(`No product found for barcode ${barcode}`);
    this.name = "ProductNotFoundError";
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
