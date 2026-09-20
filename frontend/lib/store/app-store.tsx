"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/useAuthStore";
import type { Profile, ProfileDraft, ScanResult } from "@/lib/types";

const ACTIVE_KEY = "aahar.active.v1";

interface AppState {
  profiles: Profile[];
  loading: boolean;
  /** Set when the household couldn't be loaded at all. */
  error: string | null;
  activeIds: string[];
  activeProfiles: Profile[];
  toggleActive: (id: string) => void;
  setActiveIds: (ids: string[]) => void;
  createProfile: (draft: ProfileDraft) => Promise<Profile>;
  updateProfile: (id: string, draft: ProfileDraft) => Promise<Profile>;
  deleteProfile: (id: string) => Promise<void>;
  history: ScanResult[];
  refreshHistory: () => Promise<void>;
  addScan: (scan: ScanResult) => void;
}

const AppContext = createContext<AppState | null>(null);

function persistActive(ids: string[]): void {
  try {
    window.localStorage.setItem(ACTIVE_KEY, JSON.stringify(ids));
  } catch {
    // Private mode or a full quota — the selection just won't survive a reload.
  }
}

function readActive(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(ACTIVE_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

/**
 * Everything below is scoped to whoever is signed in, so signing in or out has
 * to discard all of it — profiles, history and the selection alike.
 *
 * That is done by remounting on the token rather than by clearing five pieces
 * of state at the top of the loader: a `key` change gives the provider fresh
 * initial state for free, which is React's own idiom for "different identity,
 * different state", and it lets the loader below keep an empty dependency
 * array instead of setting state synchronously inside an effect.
 */
export function AppProvider({ children }: { children: ReactNode }) {
  const token = useAuthStore((state) => state.token);
  return (
    <HouseholdProvider key={token ?? "anonymous"}>{children}</HouseholdProvider>
  );
}

function HouseholdProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeIds, setActiveIdsState] = useState<string[]>([]);
  const [history, setHistory] = useState<ScanResult[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [loaded, pastScans] = await Promise.all([
          api.listProfiles(),
          api.listHistory(),
        ]);
        if (cancelled) return;
        setProfiles(loaded);
        setHistory(pastScans);
        const stored = readActive().filter((id) =>
          loaded.some((p) => p.id === id),
        );
        // Default to everyone: checking the whole household is the safer default.
        const initial = stored.length > 0 ? stored : loaded.map((p) => p.id);
        setActiveIdsState(initial);
        persistActive(initial);
      } catch (err) {
        // An unreachable API used to leave `loading` true forever, and every
        // screen that waits on it sat on skeletons with no error and no retry —
        // the result page even has an error state it never got to render.
        if (!cancelled) {
          console.error("Could not load the household:", err);
          setError(
            err instanceof Error && err.message
              ? err.message
              : "Couldn't reach the server.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const setActiveIds = useCallback((ids: string[]) => {
    setActiveIdsState(ids);
    persistActive(ids);
  }, []);

  const toggleActive = useCallback((id: string) => {
    setActiveIdsState((current) => {
      // Never let the selection empty out — there'd be nothing to check against.
      const next = current.includes(id)
        ? current.length > 1
          ? current.filter((x) => x !== id)
          : current
        : [...current, id];
      persistActive(next);
      return next;
    });
  }, []);

  const createProfile = useCallback(async (draft: ProfileDraft) => {
    const created = await api.createProfile(draft);
    setProfiles((current) => [...current, created]);
    // A new member has to be persisted into the selection too, or a reload
    // silently drops them from every check.
    setActiveIdsState((current) => {
      const next = [...current, created.id];
      persistActive(next);
      return next;
    });
    return created;
  }, []);

  const updateProfile = useCallback(async (id: string, draft: ProfileDraft) => {
    const updated = await api.updateProfile(id, draft);
    setProfiles((current) => current.map((p) => (p.id === id ? updated : p)));
    return updated;
  }, []);

  const deleteProfile = useCallback(async (id: string) => {
    await api.deleteProfile(id);
    setProfiles((current) => current.filter((p) => p.id !== id));
    setActiveIdsState((current) => {
      const next = current.filter((x) => x !== id);
      persistActive(next);
      return next;
    });
  }, []);

  const refreshHistory = useCallback(async () => {
    setHistory(await api.listHistory());
  }, []);

  const addScan = useCallback((scan: ScanResult) => {
    setHistory((current) => [
      scan,
      ...current.filter((s) => s.product.barcode !== scan.product.barcode),
    ]);
  }, []);

  const value = useMemo<AppState>(
    () => ({
      profiles,
      loading,
      error,
      activeIds,
      activeProfiles: profiles.filter((p) => activeIds.includes(p.id)),
      toggleActive,
      setActiveIds,
      createProfile,
      updateProfile,
      deleteProfile,
      history,
      refreshHistory,
      addScan,
    }),
    [
      profiles,
      loading,
      error,
      activeIds,
      toggleActive,
      setActiveIds,
      createProfile,
      updateProfile,
      deleteProfile,
      history,
      refreshHistory,
      addScan,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside <AppProvider>");
  return ctx;
}
