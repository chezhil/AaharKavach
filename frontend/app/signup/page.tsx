"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/stores/useAuthStore";

export default function SignupPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  
  const [age, setAge] = useState("");
  const [gender, setGender] = useState<"male" | "female" | "other" | "prefer_not_to_say">("male");
  const [weightKg, setWeightKg] = useState("");
  const [heightCm, setHeightCm] = useState("");
  const [allergiesText, setAllergiesText] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  let bmiValue: number | null = null;
  let bmiLabel = "";
  let bmiColor = "text-fg-subtle";
  if (weightKg && heightCm) {
    const w = parseFloat(weightKg);
    const h = parseFloat(heightCm) / 100;
    if (w > 0 && h > 0) {
      bmiValue = w / (h * h);
      if (bmiValue < 18.5) { bmiLabel = "Underweight"; bmiColor = "text-blue-500 dark:text-blue-400"; }
      else if (bmiValue < 25) { bmiLabel = "Normal"; bmiColor = "text-green-600 dark:text-green-400"; }
      else if (bmiValue < 30) { bmiLabel = "Overweight"; bmiColor = "text-amber-500 dark:text-amber-400"; }
      else { bmiLabel = "Obese"; bmiColor = "text-red-500 dark:text-red-400"; }
    }
  }

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const payload = {
      name,
      email,
      password,
      age: age ? parseInt(age, 10) : undefined,
      gender,
      weight_kg: weightKg ? parseFloat(weightKg) : undefined,
      height_cm: heightCm ? parseFloat(heightCm) : undefined,
      initial_allergies: allergiesText.split(",").map((a) => a.trim()).filter(Boolean),
    };

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:3001";
      const res = await fetch(`${baseUrl}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Signup failed");
      }

      const data = await res.json();
      login(data);
      router.push("/");
    } catch (err) {
      setError(
        err instanceof Error && err.message
          ? err.message
          : "Couldn't create that account. Try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8 rounded-3xl bg-surface p-8 shadow-2xl border border-border-subtle">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Create your account</h1>
          <p className="mt-2 text-sm text-fg-subtle">
            Join AaharKavach and personalize your nutrition tracking.
          </p>
        </div>

        <form onSubmit={handleSignup} className="space-y-6">
          {error && (
            <div className="rounded-xl bg-unsafe-soft p-3 text-sm text-unsafe font-semibold">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="text-sm font-semibold text-fg-muted block mb-1">Full Name</label>
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-11 w-full rounded-xl border border-border-subtle bg-bg px-3.5 text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                placeholder="John Doe"
              />
            </div>
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

            <div className="space-y-4 rounded-xl border border-border-subtle bg-bg p-4">
              <span className="text-sm font-semibold text-fg-muted block">Physical Attributes</span>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-fg-subtle block mb-1">Age</label>
                  <input
                    required
                    type="number"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="Years"
                    className="h-10 w-full rounded-lg border border-border-subtle bg-surface px-3 text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-fg-subtle block mb-1">Height (cm)</label>
                  <input
                    required
                    type="number"
                    value={heightCm}
                    onChange={(e) => setHeightCm(e.target.value)}
                    placeholder="cm"
                    className="h-10 w-full rounded-lg border border-border-subtle bg-surface px-3 text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-fg-subtle block mb-1">Weight (kg)</label>
                  <input
                    required
                    type="number"
                    value={weightKg}
                    onChange={(e) => setWeightKg(e.target.value)}
                    placeholder="kg"
                    className="h-10 w-full rounded-lg border border-border-subtle bg-surface px-3 text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-fg-subtle block mb-1">Gender</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value as typeof gender)}
                    className="h-10 w-full rounded-lg border border-border-subtle bg-surface px-3 text-sm outline-none focus:border-brand"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                    <option value="prefer_not_to_say">Prefer not to say</option>
                  </select>
                </div>
              </div>

              {bmiValue !== null && (
                <div className="flex items-center justify-between rounded-lg bg-surface border border-border-subtle p-3 text-sm">
                  <span className="text-fg-subtle">BMI Calculation</span>
                  <span className={`font-semibold ${bmiColor}`}>
                    {bmiValue.toFixed(1)} ({bmiLabel})
                  </span>
                </div>
              )}
            </div>

            <div>
              <label className="text-sm font-semibold text-fg-muted block mb-1">Allergies (comma-separated)</label>
              <input
                value={allergiesText}
                onChange={(e) => setAllergiesText(e.target.value)}
                className="h-11 w-full rounded-xl border border-border-subtle bg-bg px-3.5 text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
                placeholder="Peanuts, Gluten, Dairy"
              />
            </div>
          </div>

          <Button type="submit" size="lg" className="w-full" disabled={loading}>
            {loading ? "Creating account..." : "Sign up"}
          </Button>

          <p className="text-center text-sm text-fg-subtle">
            Already have an account?{" "}
            <a href="/signin" className="font-semibold text-brand hover:underline">
              Sign in
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
