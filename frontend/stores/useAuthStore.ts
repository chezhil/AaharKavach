import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthSession, Biometrics } from "@/lib/types";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  householdId: string;
  role: "admin" | "member";
  biometrics?: Biometrics;
}

/**
 * Re-exported from the wire contract rather than restated here. The local copy
 * declared every biometric as a plain `number`, but the API returns null for
 * any the account never supplied — so the types said a field was always there
 * while the values said otherwise.
 */
export type AuthResponse = AuthSession;

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (data: AuthResponse) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (data: AuthResponse) => {
        // We will store the token globally, and optionally set localStorage directly
        // but Zustand persist handles saving the state.
        try {
          if (typeof window !== "undefined") {
            window.localStorage.setItem("aahar_token", data.token);
          }
        } catch {}
        
        set({
          user: {
            id: data.user_id,
            name: data.name,
            email: data.email,
            householdId: data.household_id,
            role: data.role as "admin" | "member",
            biometrics: data.biometrics,
          },
          token: data.token,
          isAuthenticated: true,
        });
      },
      logout: () => {
        try {
          if (typeof window !== "undefined") {
            window.localStorage.removeItem("aahar_token");
          }
        } catch {}

        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: "aahar_auth_session",
    }
  )
);
