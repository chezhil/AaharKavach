"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, Sun, Moon, LogOut } from "lucide-react";
import { usingMocks } from "@/lib/api";
import { cn } from "@/lib/utils";
import { TABS, isActive } from "./tabs";
import { useAuthStore } from "@/stores/useAuthStore";
import { useEffect, useState } from "react";

/**
 * The theme lives on <html class="dark">, put there by the blocking script in
 * layout.tsx before first paint. That makes it external state React doesn't
 * own, so it's read through useSyncExternalStore rather than mirrored into
 * useState from an effect — which is what lets the server render "dark" (the
 * script's default) and the client correct it during hydration without a
 * render-phase setState.
 */
const subscribeToTheme = (onChange: () => void) => {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class"],
  });
  return () => observer.disconnect();
};

const getTheme = () =>
  document.documentElement.classList.contains("dark") ? "dark" : "light";

// layout.tsx adds `dark` unless localStorage says otherwise, so dark is what
// the server-rendered markup corresponds to.
const getServerTheme = () => "dark" as const;

export function AppHeader() {
  const pathname = usePathname();
  const theme = useSyncExternalStore(subscribeToTheme, getTheme, getServerTheme);
  const { user, isAuthenticated, logout } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.classList.toggle("dark", next === "dark");
    try {
      localStorage.setItem("theme", next);
    } catch {
      // Private mode or a full quota — the toggle still works for this session.
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-bg/90 backdrop-blur-lg">
      <div className="app-shell flex items-center gap-3 px-3 py-3">
        <Link href="/" className="flex min-w-0 items-center gap-2.5">
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand text-brand-fg">
            <ShieldCheck size={19} strokeWidth={2.6} />
          </span>
          <span className="min-w-0 hidden sm:block">
            <span className="display block text-[1.05rem] leading-none">
              AaharKavach
            </span>
            <span className="mt-1 block text-[0.68rem] leading-none text-fg-subtle">
              आहार कवच · Food Shield
            </span>
          </span>
        </Link>

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

        <div className={cn("flex items-center gap-2", !usingMocks && "ml-auto md:ml-0")}>
          {usingMocks && (
            <span className="ml-auto shrink-0 rounded-full bg-surface px-2.5 py-1 text-[0.62rem] font-bold uppercase tracking-wider text-fg-subtle md:ml-0">
              Demo data
            </span>
          )}
          <button
            onClick={toggleTheme}
            className="flex size-9 shrink-0 items-center justify-center rounded-full bg-surface text-fg-subtle hover:bg-surface-hover hover:text-fg transition-colors"
            title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          {mounted && (
            <div className="flex items-center gap-2 ml-1 border-l border-border pl-3">
              {isAuthenticated && user ? (
                <div className="flex items-center gap-2">
                  <div className="hidden sm:flex size-9 items-center justify-center rounded-full bg-orange-100 text-orange-600 dark:bg-orange-950 dark:text-orange-400 font-bold text-sm">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <button
                    onClick={logout}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-fg-subtle hover:text-unsafe transition-colors"
                  >
                    <LogOut size={14} />
                    <span className="hidden sm:inline">Sign Out</span>
                  </button>
                </div>
              ) : (
                <>
                  <Link
                    href="/signin"
                    className="px-3 py-1.5 text-xs font-semibold text-fg-muted hover:text-fg transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/signup"
                    className="rounded-full bg-brand px-4 py-1.5 text-xs font-bold text-brand-fg transition-transform hover:scale-105 active:scale-95"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
