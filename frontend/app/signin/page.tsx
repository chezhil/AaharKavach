"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/stores/useAuthStore";
import { api } from "@/lib/api";

export default function SigninPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSignin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.signIn({ email, password });
      login(data);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8 rounded-3xl bg-surface p-8 shadow-2xl border border-border-subtle">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Sign in</h1>
          <p className="mt-2 text-sm text-fg-subtle">
            Welcome back to AaharKavach.
          </p>
        </div>

        <form onSubmit={handleSignin} className="space-y-6">
          {error && (
            <div className="rounded-xl bg-unsafe-soft p-3 text-sm text-unsafe font-semibold">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="text-sm font-semibold text-fg-muted block mb-1">Email Address</label>
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 w-full rounded-xl border border-border-subtle bg-bg px-3.5 text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                placeholder="john@example.com"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-fg-muted block mb-1">Password</label>
              <input
                required
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 w-full rounded-xl border border-border-subtle bg-bg px-3.5 text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                placeholder="••••••••"
              />
            </div>
          </div>

          <Button type="submit" size="lg" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>

          <p className="text-center text-sm text-fg-subtle">
            New to AaharKavach?{" "}
            <a href="/signup" className="font-semibold text-brand hover:underline">
              Create an account
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
