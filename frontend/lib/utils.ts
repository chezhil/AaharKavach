import type { Confidence, Severity, Verdict } from "@/lib/types";

export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/** Tailwind classes per verdict — one place, so the traffic light stays consistent. */
export const verdictStyles: Record<
  Verdict,
  { text: string; bg: string; border: string; dot: string }
> = {
  SAFE: {
    text: "text-safe",
    bg: "bg-safe-soft",
    border: "border-safe-border",
    dot: "bg-safe",
  },
  CAUTION: {
    text: "text-caution",
    bg: "bg-caution-soft",
    border: "border-caution-border",
    dot: "bg-caution",
  },
  UNSAFE: {
    text: "text-unsafe",
    bg: "bg-unsafe-soft",
    border: "border-unsafe-border",
    dot: "bg-unsafe",
  },
};

export const severityStyles: Record<Severity, { text: string; bg: string; border: string }> = {
  MILD: { text: "text-fg-muted", bg: "bg-surface-hover", border: "border-border-strong" },
  MODERATE: { text: "text-caution", bg: "bg-caution-soft", border: "border-caution-border" },
  SEVERE: { text: "text-unsafe", bg: "bg-unsafe-soft", border: "border-unsafe-border" },
};

export const confidenceStyles: Record<Confidence, { text: string; bg: string; bars: number }> = {
  HIGH: { text: "text-safe", bg: "bg-safe", bars: 3 },
  MEDIUM: { text: "text-caution", bg: "bg-caution", bars: 2 },
  LOW: { text: "text-unsafe", bg: "bg-unsafe", bars: 1 },
};

export const accentVar: Record<string, string> = {
  violet: "var(--accent-violet)",
  amber: "var(--accent-amber)",
  teal: "var(--accent-teal)",
  rose: "var(--accent-rose)",
  sky: "var(--accent-sky)",
};

export const ACCENTS = ["violet", "amber", "teal", "rose", "sky"] as const;

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr${hours > 1 ? "s" : ""} ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days} day${days > 1 ? "s" : ""} ago`;
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

/** Barcodes are 8–14 digits (EAN-8 through GTIN-14). */
export function isValidBarcode(value: string): boolean {
  return /^\d{8,14}$/.test(value.trim());
}
