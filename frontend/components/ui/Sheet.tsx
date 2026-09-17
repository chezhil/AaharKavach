"use client";

import { X } from "lucide-react";
import { useEffect, type ReactNode } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
  title: string;
  /** Sub-line under the title — usually says what the sheet is for. */
  description?: string;
  children: ReactNode;
}

/** Bottom sheet. Mobile-first: it slides from the bottom on every size. */
export function Sheet({ open, onClose, title, description, children }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <button
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="animate-sheet relative w-full max-w-[30rem] max-h-[88dvh] overflow-y-auto rounded-t-3xl border-t border-border-subtle bg-bg-elevated shadow-2xl"
      >
        <div className="sticky top-0 z-10 flex items-start gap-3 border-b border-border-subtle bg-bg-elevated/95 px-5 pb-3 pt-4 backdrop-blur">
          <div className="min-w-0 flex-1">
            <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-border-strong" />
            <h2 className="text-lg font-bold tracking-tight">{title}</h2>
            {description ? (
              <p className="mt-0.5 text-sm text-fg-subtle">{description}</p>
            ) : null}
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="mt-3 grid size-9 shrink-0 place-items-center rounded-full text-fg-subtle transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <X size={18} />
          </button>
        </div>
        <div className="px-5 pb-[calc(env(safe-area-inset-bottom,0px)+1.5rem)] pt-4">
          {children}
        </div>
      </div>
    </div>
  );
}
