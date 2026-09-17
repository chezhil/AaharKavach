"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { TABS, isActive } from "./tabs";

/**
 * Floating pill, phones only — on md and up the same tabs live in the header,
 * where there is room for them and no thumb to reach.
 */
export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-40 pb-[calc(env(safe-area-inset-bottom,0px)+0.75rem)] md:hidden"
    >
      <ul className="mx-auto flex w-fit gap-1 rounded-full border border-border-subtle bg-bg-elevated/95 p-1.5 shadow-[0_8px_32px_-8px_rgba(0,0,0,0.8)] backdrop-blur-xl">
        {TABS.map(({ href, label, icon: Icon }) => {
          const active = isActive(pathname, href);
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-1.5 rounded-full px-3.5 py-2.5 text-xs font-bold transition-colors",
                  active
                    ? "bg-brand text-brand-fg"
                    : "text-fg-subtle hover:bg-surface-hover hover:text-fg",
                )}
              >
                <Icon size={17} strokeWidth={active ? 2.6 : 2} />
                <span className={cn(!active && "sr-only")}>{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
