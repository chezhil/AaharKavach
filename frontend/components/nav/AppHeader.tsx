import { ShieldCheck } from "lucide-react";
import { usingMocks } from "@/lib/api";

export function AppHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-border-subtle bg-bg/85 backdrop-blur-lg">
      <div className="app-shell flex items-center gap-2.5 px-5 py-3">
        <span className="grid size-8 place-items-center rounded-xl bg-brand text-brand-fg">
          <ShieldCheck size={18} strokeWidth={2.4} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[0.95rem] font-bold leading-none tracking-tight">AaharKavach</p>
          <p className="mt-1 text-[0.7rem] leading-none text-fg-subtle">आहार कवच · food shield</p>
        </div>
        {usingMocks ? (
          <span className="rounded-full border border-border-strong px-2 py-1 text-[0.65rem] font-semibold uppercase tracking-wide text-fg-subtle">
            Demo data
          </span>
        ) : null}
      </div>
    </header>
  );
}
