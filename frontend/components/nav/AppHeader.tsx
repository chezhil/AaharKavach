import { ShieldCheck } from "lucide-react";
import { usingMocks } from "@/lib/api";

export function AppHeader() {
  return (
    <header className="sticky top-0 z-30 bg-bg/90 backdrop-blur-lg">
      <div className="app-shell flex items-center gap-2.5 px-3 py-3">
        <span className="grid size-9 place-items-center rounded-xl bg-brand text-brand-fg">
          <ShieldCheck size={19} strokeWidth={2.6} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="display text-[1.05rem] leading-none">AaharKavach</p>
          <p className="mt-1 text-[0.68rem] leading-none text-fg-subtle">
            आहार कवच · food shield
          </p>
        </div>
        {usingMocks ? (
          <span className="rounded-full bg-surface px-2.5 py-1 text-[0.62rem] font-bold uppercase tracking-wider text-fg-subtle">
            Demo data
          </span>
        ) : null}
      </div>
    </header>
  );
}
