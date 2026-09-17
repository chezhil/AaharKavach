import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface Props {
  icon: LucideIcon;
  title: string;
  body: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon, title, body, action }: Props) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border-strong px-6 py-12 text-center">
      <div className="grid size-12 place-items-center rounded-2xl bg-surface text-fg-subtle">
        <Icon size={22} />
      </div>
      <div>
        <p className="font-semibold">{title}</p>
        <p className="mx-auto mt-1 max-w-[26ch] text-sm text-fg-subtle">{body}</p>
      </div>
      {action}
    </div>
  );
}
