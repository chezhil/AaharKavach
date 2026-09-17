"use client";

import { useState } from "react";
import { Lock, Pencil, Plus, Trash2, Users } from "lucide-react";
import { ProfileEditor } from "@/components/profiles/ProfileEditor";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { useApp } from "@/lib/store/app-store";
import {
  HOUSEHOLD_ROLE_LABEL,
  SEVERITY_LABEL,
  type Profile,
} from "@/lib/types";
import { accentVar, cn, initials, severityStyles } from "@/lib/utils";

export default function ProfilesPage() {
  const { profiles, createProfile, updateProfile, deleteProfile, loading } =
    useApp();
  const [editing, setEditing] = useState<Profile | null>(null);
  const [adding, setAdding] = useState(false);
  const [confirming, setConfirming] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <header className="flex items-start justify-between gap-3 px-1">
        <div>
          <h1 className="display text-2xl">Household</h1>
          <p className="mt-1 text-sm text-fg-subtle">
            Everyone you check products against, and how serious each
            restriction is.
          </p>
        </div>
        <Button size="sm" onClick={() => setAdding(true)} className="shrink-0">
          <Plus size={15} />
          Add
        </Button>
      </header>

      {!loading && profiles.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No one here yet"
          body="Add the people you shop for. Each can have their own restrictions and severities."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setAdding(true)}
            >
              <Plus size={15} />
              Add a person
            </Button>
          }
        />
      ) : null}

      <ul className="grid gap-3 md:grid-cols-2">
        {profiles.map((profile) => (
          <li key={profile.id} className="tile bg-surface p-4">
            <div className="flex items-start gap-3">
              <span
                className="grid size-10 shrink-0 place-items-center rounded-full text-sm font-bold text-bg"
                style={{
                  background: accentVar[profile.accent] ?? "var(--accent-teal)",
                }}
              >
                {initials(profile.name)}
              </span>

              <div className="min-w-0 flex-1">
                <p className="display truncate text-base">{profile.name}</p>
                <p className="mt-0.5 flex items-center gap-1.5 text-xs text-fg-subtle">
                  {HOUSEHOLD_ROLE_LABEL[profile.household_role]}
                  {!profile.can_edit ? (
                    <>
                      <span aria-hidden>·</span>
                      <Lock size={11} aria-hidden />
                      Locked by household policy
                    </>
                  ) : null}
                </p>
              </div>

              <div className="flex shrink-0 gap-1">
                <button
                  onClick={() => setEditing(profile)}
                  disabled={!profile.can_edit}
                  aria-label={`Edit ${profile.name}`}
                  title={
                    profile.can_edit
                      ? `Edit ${profile.name}`
                      : "Cedar policy: only an admin can edit this profile"
                  }
                  className="grid size-9 place-items-center rounded-lg text-fg-subtle transition-colors hover:bg-surface-hover hover:text-fg disabled:pointer-events-none disabled:opacity-35"
                >
                  <Pencil size={15} />
                </button>
                <button
                  onClick={() => setConfirming(profile.id)}
                  disabled={!profile.can_edit}
                  aria-label={`Remove ${profile.name}`}
                  className="grid size-9 place-items-center rounded-lg text-fg-subtle transition-colors hover:bg-unsafe-soft hover:text-unsafe disabled:pointer-events-none disabled:opacity-35"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>

            {profile.restrictions.length > 0 ? (
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {profile.restrictions.map((restriction) => {
                  const style = severityStyles[restriction.severity];
                  return (
                    <li
                      key={restriction.id}
                      className={cn(
                        "rounded-full px-2.5 py-1 text-xs font-bold",
                        style.solid,
                      )}
                    >
                      {restriction.label}
                      <span className="ml-1.5 opacity-70">
                        {SEVERITY_LABEL[restriction.severity]}
                      </span>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="mt-3 text-xs text-fg-subtle">
                No restrictions set.
              </p>
            )}

            {confirming === profile.id ? (
              <div className="animate-rise mt-3 flex items-center gap-2 rounded-xl border border-unsafe-border bg-unsafe-soft p-2.5">
                <p className="flex-1 text-xs text-unsafe">
                  Remove {profile.name}?
                </p>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setConfirming(null)}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={async () => {
                    await deleteProfile(profile.id);
                    setConfirming(null);
                  }}
                >
                  Remove
                </Button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>

      <p className="tile bg-surface p-3.5 text-xs leading-relaxed text-fg-subtle">
        Who can edit whose restrictions is decided by Cedar policy on the
        backend, not by this screen. A child&apos;s profile stays read-only here
        even if you are signed in as them.
      </p>

      {adding ? (
        <ProfileEditor
          open
          onClose={() => setAdding(false)}
          onSave={async (draft) => {
            await createProfile(draft);
          }}
        />
      ) : null}

      {editing ? (
        <ProfileEditor
          key={editing.id}
          open
          profile={editing}
          onClose={() => setEditing(null)}
          onSave={async (draft) => {
            await updateProfile(editing.id, draft);
          }}
        />
      ) : null}
    </div>
  );
}
