"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Sheet } from "@/components/ui/Sheet";
import { Button } from "@/components/ui/Button";
import { SeverityPicker } from "./SeverityPicker";
import {
  HOUSEHOLD_ROLE_LABEL,
  type HouseholdRole,
  type Profile,
  type ProfileDraft,
  type Restriction,
} from "@/lib/types";
import { ACCENTS, accentVar, cn } from "@/lib/utils";

const COMMON = [
  "Gluten",
  "Dairy",
  "Peanuts",
  "Tree Nuts",
  "Soy",
  "Egg",
  "Sesame",
  "Shellfish",
  "Vegetarian",
  "Vegan",
  "Jain",
  "Latex",
];

const ROLES: HouseholdRole[] = ["ADMIN", "MEMBER", "CHILD"];

interface Props {
  open: boolean;
  onClose: () => void;
  /** Absent when creating. */
  profile?: Profile;
  onSave: (draft: ProfileDraft) => Promise<void>;
}

const newId = () => `r_${Math.random().toString(36).slice(2, 8)}`;

export function ProfileEditor({ open, onClose, profile, onSave }: Props) {
  const [name, setName] = useState(profile?.name ?? "");
  const [role, setRole] = useState<HouseholdRole>(
    profile?.household_role ?? "MEMBER",
  );
  const [accent, setAccent] = useState(profile?.accent ?? "teal");
  const [restrictions, setRestrictions] = useState<Restriction[]>(
    profile?.restrictions ?? [],
  );
  
  const [age, setAge] = useState(profile?.age?.toString() ?? "");
  const [gender, setGender] = useState<"male" | "female" | "other">(profile?.gender ?? "male");
  const [weightKg, setWeightKg] = useState(profile?.weight_kg?.toString() ?? "");
  const [heightCm, setHeightCm] = useState(profile?.height_cm?.toString() ?? "");

  const [draftLabel, setDraftLabel] = useState("");
  const [saving, setSaving] = useState(false);

  const addRestriction = (label: string) => {
    const clean = label.trim();
    if (!clean) return;
    if (restrictions.some((r) => r.label.toLowerCase() === clean.toLowerCase()))
      return;
    setRestrictions((current) => [
      ...current,
      { id: newId(), label: clean, severity: "MODERATE" },
    ]);
    setDraftLabel("");
  };

  const save = async () => {
    if (!name.trim() || saving) return;
    setSaving(true);
    try {
      await onSave({
        name: name.trim(),
        household_role: role,
        accent,
        restrictions,
        age: age ? parseInt(age, 10) : undefined,
        gender: gender,
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
        height_cm: heightCm ? parseFloat(heightCm) : undefined,
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const unused = COMMON.filter(
    (c) => !restrictions.some((r) => r.label.toLowerCase() === c.toLowerCase()),
  );

  let bmiValue: number | null = null;
  let bmiLabel = "";
  let bmiColor = "text-fg-subtle";
  
  if (weightKg && heightCm) {
    const w = parseFloat(weightKg);
    const h = parseFloat(heightCm) / 100;
    if (w > 0 && h > 0) {
      bmiValue = w / (h * h);
      if (bmiValue < 18.5) { bmiLabel = "Underweight"; bmiColor = "text-blue-400"; }
      else if (bmiValue < 25) { bmiLabel = "Normal"; bmiColor = "text-green-400"; }
      else if (bmiValue < 30) { bmiLabel = "Overweight"; bmiColor = "text-yellow-400"; }
      else { bmiLabel = "Obese"; bmiColor = "text-red-400"; }
    }
  }

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title={profile ? `Edit ${profile.name}` : "Add a person"}
      description="Tag each restriction with how serious a reaction is — the warnings scale to match."
    >
      <div className="space-y-6">
        <div className="space-y-2">
          <label
            htmlFor="profile-name"
            className="text-sm font-semibold text-fg-muted"
          >
            Name
          </label>
          <input
            id="profile-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Aryan"
            className="h-11 w-full rounded-xl border border-border-subtle bg-bg px-3.5 text-sm outline-none transition-colors placeholder:text-fg-subtle focus:border-brand"
          />
        </div>

        <div className="space-y-2">
          <span className="text-sm font-semibold text-fg-muted">Colour</span>
          <div className="flex gap-2">
            {ACCENTS.map((option) => (
              <button
                key={option}
                type="button"
                aria-label={option}
                aria-pressed={accent === option}
                onClick={() => setAccent(option)}
                className={cn(
                  "size-8 rounded-full transition-all",
                  accent === option
                    ? "ring-2 ring-fg ring-offset-2 ring-offset-bg-elevated"
                    : "opacity-70 hover:opacity-100",
                )}
                style={{ background: accentVar[option] }}
              />
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-sm font-semibold text-fg-muted">
            Household role
          </span>
          <div className="grid grid-cols-3 gap-1 rounded-xl bg-bg p-1">
            {ROLES.map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={role === option}
                onClick={() => setRole(option)}
                className={cn(
                  "rounded-lg px-2 py-1.5 text-xs font-semibold transition-colors",
                  role === option
                    ? "bg-brand text-brand-fg"
                    : "text-fg-subtle hover:text-fg-muted",
                )}
              >
                {HOUSEHOLD_ROLE_LABEL[option]}
              </button>
            ))}
          </div>
          <p className="text-xs text-fg-subtle">
            {role === "ADMIN"
              ? "Can edit everyone's restrictions, including children's."
              : role === "MEMBER"
                ? "Can edit only their own restrictions."
                : "Read-only — an admin has to make changes for them."}
          </p>
        </div>

        <div className="space-y-4 rounded-xl border border-border-subtle bg-surface p-4">
          <span className="text-sm font-semibold text-fg-muted">
            Physical Attributes (for nutrition math)
          </span>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="profile-age" className="text-xs font-semibold text-fg-subtle">Age</label>
              <input id="profile-age" type="number" value={age} onChange={(e) => setAge(e.target.value)} placeholder="Years" className="h-10 w-full rounded-lg border border-border-subtle bg-bg px-3 text-sm outline-none placeholder:text-fg-subtle focus:border-brand" />
            </div>
            <div className="space-y-2">
              <label htmlFor="profile-gender" className="text-xs font-semibold text-fg-subtle">Gender</label>
              <select id="profile-gender" value={gender} onChange={(e) => setGender(e.target.value as any)} className="h-10 w-full rounded-lg border border-border-subtle bg-bg px-3 text-sm outline-none focus:border-brand">
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="space-y-2">
              <label htmlFor="profile-weight" className="text-xs font-semibold text-fg-subtle">Weight (kg)</label>
              <input id="profile-weight" type="number" value={weightKg} onChange={(e) => setWeightKg(e.target.value)} placeholder="kg" className="h-10 w-full rounded-lg border border-border-subtle bg-bg px-3 text-sm outline-none placeholder:text-fg-subtle focus:border-brand" />
            </div>
            <div className="space-y-2">
              <label htmlFor="profile-height" className="text-xs font-semibold text-fg-subtle">Height (cm)</label>
              <input id="profile-height" type="number" value={heightCm} onChange={(e) => setHeightCm(e.target.value)} placeholder="cm" className="h-10 w-full rounded-lg border border-border-subtle bg-bg px-3 text-sm outline-none placeholder:text-fg-subtle focus:border-brand" />
            </div>
          </div>
          {bmiValue !== null && (
            <div className="flex items-center justify-between rounded-lg bg-bg p-3 text-sm">
              <span className="text-fg-subtle">BMI Calculation</span>
              <span className={`font-semibold ${bmiColor}`}>
                {bmiValue.toFixed(1)} ({bmiLabel})
              </span>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <span className="text-sm font-semibold text-fg-muted">
            Restrictions
          </span>

          {restrictions.length > 0 ? (
            <ul className="space-y-2">
              {restrictions.map((restriction) => (
                <li
                  key={restriction.id}
                  className="rounded-xl border border-border-subtle bg-surface p-3"
                >
                  <div className="mb-2 flex items-center gap-2">
                    <span className="flex-1 truncate text-sm font-semibold">
                      {restriction.label}
                    </span>
                    <button
                      type="button"
                      aria-label={`Remove ${restriction.label}`}
                      onClick={() =>
                        setRestrictions((current) =>
                          current.filter((r) => r.id !== restriction.id),
                        )
                      }
                      className="grid size-8 place-items-center rounded-lg text-fg-subtle transition-colors hover:bg-unsafe-soft hover:text-unsafe"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                  <SeverityPicker
                    label={`Severity for ${restriction.label}`}
                    value={restriction.severity}
                    onChange={(severity) =>
                      setRestrictions((current) =>
                        current.map((r) =>
                          r.id === restriction.id ? { ...r, severity } : r,
                        ),
                      )
                    }
                  />
                </li>
              ))}
            </ul>
          ) : (
            <p className="rounded-xl border border-dashed border-border-strong px-3 py-4 text-center text-sm text-fg-subtle">
              No restrictions yet — every scan will come back safe.
            </p>
          )}

          <div className="flex gap-2">
            <input
              value={draftLabel}
              onChange={(e) => setDraftLabel(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addRestriction(draftLabel);
                }
              }}
              placeholder="Add another…"
              aria-label="New restriction"
              className="h-11 flex-1 rounded-xl border border-border-subtle bg-bg px-3.5 text-sm outline-none placeholder:text-fg-subtle focus:border-brand"
            />
            <Button
              variant="secondary"
              onClick={() => addRestriction(draftLabel)}
              disabled={!draftLabel.trim()}
              aria-label="Add restriction"
            >
              <Plus size={16} />
            </Button>
          </div>

          {unused.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {unused.slice(0, 8).map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => addRestriction(suggestion)}
                  className="rounded-full border border-border-subtle bg-surface px-3 py-1.5 text-xs font-medium text-fg-muted transition-colors hover:border-brand hover:text-brand"
                >
                  + {suggestion}
                </button>
              ))}
            </div>
          ) : null}
        </div>

        <Button
          size="lg"
          className="w-full"
          onClick={save}
          disabled={!name.trim() || saving}
        >
          {saving ? "Saving…" : profile ? "Save changes" : "Add to household"}
        </Button>
      </div>
    </Sheet>
  );
}
