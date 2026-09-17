"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Columns2, History, ScanLine, Users } from "lucide-react";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/", label: "Scan", icon: ScanLine },
  { href: "/compare", label: "Compare", icon: Columns2 },
  { href: "/history", label: "History", icon: History },
  { href: "/profiles", label: "Household", icon: Users },
] as const;

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border-subtle bg-bg-elevated/90 backdrop-blur-lg"
    >
      <ul className="app-shell grid grid-cols-4 pb-[env(safe-area-inset-bottom,0px)]">
        {TABS.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex flex-col items-center gap-1 px-2 py-2.5 text-[0.7rem] font-medium transition-colors",
                  active ? "text-brand" : "text-fg-subtle hover:text-fg-muted",
                )}
              >
                <span
                  className={cn(
                    "grid h-8 w-14 place-items-center rounded-full transition-colors",
                    active && "bg-brand-soft",
                  )}
                >
                  <Icon size={19} strokeWidth={active ? 2.4 : 1.9} />
                </span>
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
