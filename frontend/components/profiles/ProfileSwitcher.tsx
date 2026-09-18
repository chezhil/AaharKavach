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
      <div className="tile bg-surface p-3.5">
        <Skeleton className="h-3 w-24" />
        <div className="mt-3 flex gap-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-[4.5rem] w-[4.75rem] rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  const allActive = profiles.length > 0 && activeIds.length === profiles.length;

  return (
    <section aria-labelledby="who-heading" className="tile bg-surface p-3.5">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id="who-heading" className="display text-sm">
          Checking for
        </h2>
        <button
          onClick={() => setActiveIds(profiles.map((p) => p.id))}
          disabled={allActive}
          className="text-xs font-bold text-brand-line transition-opacity disabled:opacity-35"
        >
          Everyone
        </button>
      </div>

      <ul className="-mx-3.5 mt-3 flex gap-2 overflow-x-auto px-3.5 pb-1 [scrollbar-width:none] md:mx-0 md:flex-wrap md:overflow-visible md:px-0 [&::-webkit-scrollbar]:hidden">
        {profiles.map((profile) => {
          const active = activeIds.includes(profile.id);
          return (
            <li key={profile.id} className="md:min-w-[6rem] md:flex-1">
              <button
                onClick={() => toggleActive(profile.id)}
                aria-pressed={active}
                className={cn(
                  "relative flex w-[4.75rem] flex-col items-center gap-1.5 rounded-2xl px-2 py-3 transition-all md:w-full",
                  active
                    ? "bg-sky text-sky-fg"
                    : "bg-surface-hover text-fg-subtle hover:text-fg-muted",
                )}
              >
                <span
                  className={cn(
                    "grid size-9 place-items-center rounded-full text-sm font-extrabold text-bg transition-opacity",
                    !active && "opacity-45",
                  )}
                  style={{
                    background:
                      accentVar[profile.accent] ?? "var(--accent-teal)",
                  }}
                >
                  {initials(profile.name)}
                </span>
                <span className="w-full truncate text-center text-xs font-bold">
                  {profile.name}
                </span>
                <span className="text-[0.62rem] font-semibold leading-none opacity-70">
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

        <li className="md:min-w-[6rem] md:flex-1">
          <Link
            href="/profiles"
            className="flex h-full w-[4.75rem] flex-col items-center justify-center gap-1.5 rounded-2xl border border-dashed border-border-strong px-2 py-3 text-fg-subtle transition-colors hover:border-brand hover:text-brand-line md:w-full"
          >
            <Plus size={18} />
            <span className="text-xs font-bold">Add</span>
          </Link>
        </li>
      </ul>
    </section>
  );
}
