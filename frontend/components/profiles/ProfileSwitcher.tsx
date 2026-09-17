"use client";

import Link from "next/link";
import { Check, Plus } from "lucide-react";
import { useApp } from "@/lib/store/app-store";
import { accentVar, cn, initials } from "@/lib/utils";
import { Skeleton } from "@/components/ui/Skeleton";

/**
 * Who this scan is being checked against. Multi-select on purpose — the whole
 * point of the app is answering for a household, not one person.
 */
export function ProfileSwitcher() {
  const { profiles, activeIds, toggleActive, setActiveIds, loading } = useApp();

  if (loading) {
    return (
      <div className="flex gap-2">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-[4.5rem] w-24 rounded-2xl" />
        ))}
      </div>
    );
  }

  const allActive = profiles.length > 0 && activeIds.length === profiles.length;

  return (
    <section aria-labelledby="who-heading">
      <div className="mb-2.5 flex items-baseline justify-between gap-3">
        <h2 id="who-heading" className="text-sm font-semibold text-fg-muted">
          Checking for
        </h2>
        <button
          onClick={() => setActiveIds(profiles.map((p) => p.id))}
          disabled={allActive}
          className="text-xs font-semibold text-brand transition-opacity disabled:opacity-40"
        >
          Select everyone
        </button>
      </div>

      <ul className="-mx-5 flex gap-2 overflow-x-auto px-5 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {profiles.map((profile) => {
          const active = activeIds.includes(profile.id);
          return (
            <li key={profile.id}>
              <button
                onClick={() => toggleActive(profile.id)}
                aria-pressed={active}
                className={cn(
                  "relative flex w-[5.5rem] flex-col items-center gap-1.5 rounded-2xl border px-2 py-3 transition-all",
                  active
                    ? "border-brand bg-brand-soft"
                    : "border-border-subtle bg-surface opacity-60 hover:opacity-100",
                )}
              >
                <span
                  className="grid size-9 place-items-center rounded-full text-sm font-bold text-bg"
                  style={{ background: accentVar[profile.accent] ?? "var(--accent-teal)" }}
                >
                  {initials(profile.name)}
                </span>
                <span className="w-full truncate text-center text-xs font-semibold">
                  {profile.name}
                </span>
                <span className="text-[0.65rem] leading-none text-fg-subtle">
                  {profile.restrictions.length} rule
                  {profile.restrictions.length === 1 ? "" : "s"}
                </span>
                {active ? (
                  <span className="absolute -right-1 -top-1 grid size-5 place-items-center rounded-full bg-brand text-brand-fg">
                    <Check size={12} strokeWidth={3.5} />
                  </span>
                ) : null}
              </button>
            </li>
          );
        })}

        <li>
          <Link
            href="/profiles"
            className="flex h-full w-[5.5rem] flex-col items-center justify-center gap-1.5 rounded-2xl border border-dashed border-border-strong px-2 py-3 text-fg-subtle transition-colors hover:border-brand hover:text-brand"
          >
            <Plus size={18} />
            <span className="text-xs font-semibold">Add</span>
          </Link>
        </li>
      </ul>
    </section>
  );
}
