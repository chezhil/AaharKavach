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
import { MOCK_PROFILES, findProduct } from "@/lib/mocks/fixtures";
import { compareVerdicts, evaluate as runEngine } from "@/lib/mocks/engine";
import { ProductNotFoundError, type AaharApi } from "./types";

/**
 * Mock backend. Profiles and history persist in localStorage so the app
 * behaves like a real one across reloads — useful for the demo video, and it
 * means none of the UI code has to know the backend isn't there yet.
 */

const PROFILES_KEY = "aahar.profiles.v1";
const HISTORY_KEY = "aahar.history.v1";

const delay = (ms = 260) => new Promise((r) => setTimeout(r, ms));

function read<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write<T>(key: string, value: T): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Private mode or a full quota — the app still works for this session.
  }
}

function profiles(): Profile[] {
  const stored = read<Profile[] | null>(PROFILES_KEY, null);
  if (stored && stored.length > 0) return stored;
  write(PROFILES_KEY, MOCK_PROFILES);
  return MOCK_PROFILES;
}

function history(): ScanResult[] {
  return read<ScanResult[]>(HISTORY_KEY, []);
}

const id = () => Math.random().toString(36).slice(2, 10);

function resolveProduct(req: EvaluateRequest): Product {
  if (req.product) return req.product;
  if (!req.barcode) throw new Error("evaluate() needs a barcode or a product");
  const product = findProduct(req.barcode);
  if (!product) throw new ProductNotFoundError(req.barcode);
  return product;
}

function selected(ids: string[]): Profile[] {
  const all = profiles();
  const picked = all.filter((p) => ids.includes(p.id));
  return picked.length > 0 ? picked : all.slice(0, 1);
}

export const mockApi: AaharApi = {
  async listProfiles() {
    await delay(120);
    return profiles();
  },

  async createProfile(draft: ProfileDraft) {
    await delay();
    const created: Profile = { ...draft, id: `p_${id()}`, can_edit: true };
    write(PROFILES_KEY, [...profiles(), created]);
    return created;
  },

  async updateProfile(profileId: string, draft: ProfileDraft) {
    await delay();
    const next = profiles().map((p) =>
      p.id === profileId
        ? { ...p, ...draft, id: p.id, can_edit: p.can_edit }
        : p,
    );
    write(PROFILES_KEY, next);
    const updated = next.find((p) => p.id === profileId);
    if (!updated) throw new Error(`No profile ${profileId}`);
    return updated;
  },

  async deleteProfile(profileId: string) {
    await delay();
    write(
      PROFILES_KEY,
      profiles().filter((p) => p.id !== profileId),
    );
  },

  async scanBarcode(barcode: string) {
    await delay(520); // a lookup round-trip feels like this
    const product = findProduct(barcode);
    if (!product) throw new ProductNotFoundError(barcode);
    return product;
  },

  async scanLabel(file: File | string) {
    await delay(1100); // OCR + vision is the slow path
    // Pretend we read a label we half-understood — exercises the LOW path.
    return {
      barcode: `photo_${id()}`,
      name: typeof file === "string" ? "Photographed label" : file.name.replace(/\.[^.]+$/, "") || "Photographed label",
      brand: null,
      categories: [],
      data_confidence: "LOW",
      source: "LABEL_PHOTO",
      image_url: null,
      ingredients: [
        { name: "Refined Wheat Flour", e_number: null, explainer: null },
        { name: "Milk Solids", e_number: null, explainer: null },
        { name: "Soy Lecithin", e_number: "E322", explainer: null },
      ],
    } satisfies Product;
  },

  async scanUrl(url: string, profile_ids: string[]) {
    await delay(1500);
    const product = {
      barcode: url,
      name: "Mock Webpage Product",
      brand: null,
      categories: [],
      data_confidence: "LOW",
      source: "URL",
      image_url: null,
      ingredients: [
        { name: "Sugar", e_number: null, explainer: null },
        { name: "Cocoa Mass", e_number: null, explainer: null },
      ],
    } as Product;
    
    const evaluation = runEngine(product, selected(profile_ids));
    
    return {
      id: `scan_${id()}`,
      scanned_at: new Date().toISOString(),
      product,
      evaluation,
      profile_ids,
    } as ScanResult;
  },

  async evaluate(req: EvaluateRequest): Promise<EvaluationResult> {
    await delay(700); // the agent is the slow bit
    return runEngine(resolveProduct(req), selected(req.profile_ids));
  },

  async compare(req: CompareRequest): Promise<CompareResult> {
    await delay(900);
    const people = selected(req.profile_ids);
    const build = (barcode: string): ScanResult => {
      const product = findProduct(barcode);
      if (!product) throw new ProductNotFoundError(barcode);
      return {
        id: `cmp_${id()}`,
        scanned_at: new Date().toISOString(),
        product,
        evaluation: runEngine(product, people),
        profile_ids: people.map((p) => p.id),
      };
    };
    const a = build(req.barcode_a);
    const b = build(req.barcode_b);
    return {
      a,
      b,
      ...compareVerdicts(
        a.evaluation.profile_evaluations,
        b.evaluation.profile_evaluations,
      ),
    };
  },

  async listHistory() {
    await delay(120);
    return history();
  },

  async recordScan(scan: ScanResult) {
    const existing = history().filter(
      (s) => s.product.barcode !== scan.product.barcode,
    );
    write(HISTORY_KEY, [scan, ...existing].slice(0, 50));
  },
};
