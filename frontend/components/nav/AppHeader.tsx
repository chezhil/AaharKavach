"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { usingMocks } from "@/lib/api";
import { cn } from "@/lib/utils";
import { TABS, isActive } from "./tabs";

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 bg-bg/90 backdrop-blur-lg">
      <div className="app-shell flex items-center gap-3 px-3 py-3">
        <Link href="/" className="flex min-w-0 items-center gap-2.5">
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand text-brand-fg">
            <ShieldCheck size={19} strokeWidth={2.6} />
          </span>
          <span className="min-w-0">
            <span className="display block text-[1.05rem] leading-none">
              AaharKavach
            </span>
            <span className="mt-1 block text-[0.68rem] leading-none text-fg-subtle">
              आहार कवच · food shield
            </span>
          </span>
        </Link>

        {/* On a phone this row is the floating pill at the bottom instead. */}
        <nav aria-label="Main" className="ml-auto hidden md:block">
          <ul className="flex gap-1 rounded-full bg-surface p-1">
            {TABS.map(({ href, label, icon: Icon }) => {
              const active = isActive(pathname, href);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-1.5 rounded-full px-3.5 py-2 text-xs font-bold transition-colors",
                      active
                        ? "bg-brand text-brand-fg"
                        : "text-fg-subtle hover:bg-surface-hover hover:text-fg",
                    )}
                  >
                    <Icon size={15} strokeWidth={active ? 2.6 : 2} />
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {usingMocks ? (
          <span className="ml-auto shrink-0 rounded-full bg-surface px-2.5 py-1 text-[0.62rem] font-bold uppercase tracking-wider text-fg-subtle md:ml-0">
            Demo data
          </span>
        ) : null}
      </div>
    </header>
  );
}
