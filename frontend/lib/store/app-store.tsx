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
import type { Profile, ProfileDraft, ScanResult } from "@/lib/types";

const ACTIVE_KEY = "aahar.active.v1";

interface AppState {
  profiles: Profile[];
  loading: boolean;
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

function readActive(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(ACTIVE_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeIds, setActiveIdsState] = useState<string[]>([]);
  const [history, setHistory] = useState<ScanResult[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [loaded, pastScans] = await Promise.all([api.listProfiles(), api.listHistory()]);
      if (cancelled) return;
      setProfiles(loaded);
      setHistory(pastScans);
      const stored = readActive().filter((id) => loaded.some((p) => p.id === id));
      // Default to everyone: checking the whole household is the safer default.
      setActiveIdsState(stored.length > 0 ? stored : loaded.map((p) => p.id));
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const setActiveIds = useCallback((ids: string[]) => {
    setActiveIdsState(ids);
    try {
      window.localStorage.setItem(ACTIVE_KEY, JSON.stringify(ids));
    } catch {
      // Non-fatal: the selection just won't survive a reload.
    }
  }, []);

  const toggleActive = useCallback(
    (id: string) => {
      setActiveIdsState((current) => {
        // Never let the selection empty out — there'd be nothing to check against.
        const next = current.includes(id)
          ? current.length > 1
            ? current.filter((x) => x !== id)
            : current
          : [...current, id];
        try {
          window.localStorage.setItem(ACTIVE_KEY, JSON.stringify(next));
        } catch {
          // ignore
        }
        return next;
      });
    },
    [],
  );

  const createProfile = useCallback(
    async (draft: ProfileDraft) => {
      const created = await api.createProfile(draft);
      setProfiles((current) => [...current, created]);
      setActiveIdsState((current) => [...current, created.id]);
      return created;
    },
    [],
  );

  const updateProfile = useCallback(async (id: string, draft: ProfileDraft) => {
    const updated = await api.updateProfile(id, draft);
    setProfiles((current) => current.map((p) => (p.id === id ? updated : p)));
    return updated;
  }, []);

  const deleteProfile = useCallback(async (id: string) => {
    await api.deleteProfile(id);
    setProfiles((current) => current.filter((p) => p.id !== id));
    setActiveIdsState((current) => current.filter((x) => x !== id));
  }, []);

  const refreshHistory = useCallback(async () => {
    setHistory(await api.listHistory());
  }, []);

  const addScan = useCallback((scan: ScanResult) => {
    setHistory((current) => [scan, ...current.filter((s) => s.product.barcode !== scan.product.barcode)]);
  }, []);

  const value = useMemo<AppState>(
    () => ({
      profiles,
      loading,
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
