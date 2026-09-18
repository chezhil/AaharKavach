import type { Confidence, Severity, Verdict } from "@/lib/types";

export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/**
 * Tailwind classes per verdict, in two registers:
 *   solid — a filled bento tile (saturated fill, dark or light text on it)
 *   soft  — the same meaning on a dark card (tinted background, readable hue)
 * One place, so the traffic light never drifts between screens.
 */
export const verdictStyles: Record<
  Verdict,
  { solid: string; soft: string; line: string; border: string; dot: string }
> = {
  SAFE: {
    solid: "bg-safe text-safe-fg",
    soft: "bg-safe-soft text-safe-line",
    line: "text-safe-line",
    border: "border-safe-line/35",
    dot: "bg-safe",
  },
  CAUTION: {
    solid: "bg-caution text-caution-fg",
    soft: "bg-caution-soft text-caution-line",
    line: "text-caution-line",
    border: "border-caution-line/35",
    dot: "bg-caution",
  },
  UNSAFE: {
    solid: "bg-unsafe text-unsafe-fg",
    soft: "bg-unsafe-soft text-unsafe-line",
    line: "text-unsafe-line",
    border: "border-unsafe-line/40",
    dot: "bg-unsafe",
  },
};

export const severityStyles: Record<
  Severity,
  { solid: string; soft: string; line: string; border: string }
> = {
  MILD: {
    solid: "bg-surface-hover text-fg",
    soft: "bg-surface-hover text-fg-muted",
    line: "text-fg-muted",
    border: "border-border-strong",
  },
  MODERATE: {
    solid: "bg-caution text-caution-fg",
    soft: "bg-caution-soft text-caution-line",
    line: "text-caution-line",
    border: "border-caution-line/35",
  },
  SEVERE: {
    solid: "bg-unsafe text-unsafe-fg",
    soft: "bg-unsafe-soft text-unsafe-line",
    line: "text-unsafe-line",
    border: "border-unsafe-line/40",
  },
};

export const confidenceStyles: Record<
  Confidence,
  { line: string; bar: string; bars: number }
> = {
  HIGH: { line: "text-safe-line", bar: "bg-safe", bars: 3 },
  MEDIUM: { line: "text-caution-line", bar: "bg-caution", bars: 2 },
  LOW: { line: "text-unsafe-line", bar: "bg-unsafe", bars: 1 },
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
  return new Date(iso).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
  });
}

/** Barcodes are 8–14 digits (EAN-8 through GTIN-14). */
export function isValidBarcode(value: string): boolean {
  return /^\d{8,14}$/.test(value.trim());
}
