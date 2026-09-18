import type {
  CompareRequest,
  CompareResult,
  EvaluateRequest,
  EvaluationResult,
  Product,
  Profile,
  ProfileDraft,
  ScanResult,
} from "@/lib/types";
import { ApiError, ProductNotFoundError, type AaharApi } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:3001";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      `Can't reach the API at ${BASE}. Is \`sam local start-api\` running?`,
    );
  }
  if (res.status === 404) throw new ApiError("Not found", 404);
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(body || `Request failed with ${res.status}`, res.status);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Talks to Role 3's SAM API. Selected when NEXT_PUBLIC_USE_MOCKS is not "true". */
export const httpApi: AaharApi = {
  listProfiles: () => request<Profile[]>("/api/profiles"),

  createProfile: (draft: ProfileDraft) =>
    request<Profile>("/api/profiles", {
      method: "POST",
      body: JSON.stringify(draft),
    }),

  updateProfile: (id: string, draft: ProfileDraft) =>
    request<Profile>(`/api/profiles/${id}`, {
      method: "PUT",
      body: JSON.stringify(draft),
    }),

  deleteProfile: (id: string) =>
    request<void>(`/api/profiles/${id}`, { method: "DELETE" }),

  async scanBarcode(barcode: string) {
    try {
      return await request<Product>(
        `/api/scan/barcode?code=${encodeURIComponent(barcode)}`,
      );
    } catch (err) {
      if (err instanceof ApiError && err.status === 404)
        throw new ProductNotFoundError(barcode);
      throw err;
    }
  },

  scanLabel(file: File) {
    const form = new FormData();
    form.append("image", file);
    return request<Product>("/api/scan/label", { method: "POST", body: form });
  },

  scanUrl(url: string, profile_ids: string[]) {
    return request<ScanResult>("/api/scan/url", { 
      method: "POST", 
      body: JSON.stringify({ url, profile_ids }) 
    });
  },

  evaluate: (req: EvaluateRequest) =>
    request<EvaluationResult>("/api/evaluate", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  compare: (req: CompareRequest) =>
    request<CompareResult>("/api/compare", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  listHistory: () => request<ScanResult[]>("/api/history"),

  // /api/evaluate writes history server-side; nothing to do from the client.
  async recordScan() {},
};
