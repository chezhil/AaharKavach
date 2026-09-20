import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  householdId: string;
  role: "admin" | "member";
  biometrics?: {
    age: number;
    gender: string;
    height: number;
    weight: number;
    bmi: number;
  };
}

export interface AuthResponse {
  token: string;
  user_id: string;
  name: string;
  email: string;
  household_id: string;
  role: string;
  biometrics: {
    age: number;
    gender: string;
    height: number;
    weight: number;
    bmi: number;
  };
}

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
        } catch (e) {}
        
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
        } catch (e) {}

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
