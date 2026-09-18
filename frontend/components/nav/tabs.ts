import { Columns2, History, ScanLine, Users, type LucideIcon } from "lucide-react";

export interface Tab {
  href: string;
  label: string;
  icon: LucideIcon;
}

/** Shared by the phone's bottom pill and the laptop's header row. */
export const TABS: Tab[] = [
  { href: "/", label: "Scan", icon: ScanLine },
  { href: "/compare", label: "Compare", icon: Columns2 },
  { href: "/history", label: "History", icon: History },
  { href: "/profiles", label: "Household", icon: Users },
];

export function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}
