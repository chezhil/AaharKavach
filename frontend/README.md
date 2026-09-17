# AaharKavach — frontend (Role 4)

Mobile-first Next.js app: scan a barcode, get a plain-English verdict per household
member, with severity-scaled warnings and an honest confidence signal.

It runs **standalone against mocks**, so nothing here is blocked on Roles 1–3.

## Run it

```bash
npm install
npm run dev
```

Open <http://localhost:3000>. Mocks are on by default — there is a seeded household
(Aaditya / Aryan / Naman) and a 13-product demo catalogue.

The camera needs HTTPS or localhost. On a phone, use `npm run dev -- -H 0.0.0.0` and
reach it over the LAN; if the browser blocks the camera, the **Type it** and
**Label photo** tabs still work.

## Layout

```
frontend/
├── app/
│   ├── page.tsx                 scan screen (bento home)
│   ├── result/[barcode]/        per-profile verdicts, ingredients, alternatives
│   ├── compare/                 two products side by side
│   ├── history/                 past scans
│   ├── profiles/                household management
│   ├── layout.tsx               shell: header, nav, providers
│   └── globals.css              design tokens (see "Design")
├── components/
│   ├── scanner/                 BarcodeScanner (html5-qrcode), ScanSheet
│   ├── profiles/                ProfileSwitcher, ProfileEditor, SeverityPicker
│   ├── verdict/                 VerdictCard, ConfidenceBadge, IngredientChips
│   ├── compare/                 ProductPicker
│   ├── history/                 HistoryRow
│   ├── nav/                     AppHeader, BottomNav
│   └── ui/                      Button, Sheet, EmptyState, Skeleton
└── lib/
    ├── types.ts                 ⚠️ the wire contract — see below
    ├── api/{index,client,mock,types}.ts
    ├── mocks/{fixtures,knowledge,engine}.ts
    ├── store/app-store.tsx      profiles + active selection + history
    └── utils.ts                 verdict/severity/confidence class maps
```

Dependencies beyond the Next scaffold: `lucide-react` (icons), `html5-qrcode` (scanner).
No state library — one React context is enough at this size.

## Switching to the real backend

```bash
# .env.local
NEXT_PUBLIC_USE_MOCKS=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:3001
```

`lib/api/index.ts` picks `httpApi` instead of `mockApi`. **No component changes** —
every screen talks to the `AaharApi` interface in `lib/api/types.ts`.

## Contract with Roles 1–3

`lib/types.ts` is the frontend's half. Everything on the wire is `snake_case`.

| Endpoint | Owner | Request | Response |
|---|---|---|---|
| `GET /api/profiles` | Role 3 | — | `Profile[]` |
| `POST /api/profiles` | Role 3 | `ProfileDraft` | `Profile` |
| `PUT /api/profiles/{id}` | Role 3 | `ProfileDraft` | `Profile` |
| `DELETE /api/profiles/{id}` | Role 3 | — | `204` |
| `GET /api/scan/barcode?code=` | Role 2 | — | `Product`, or `404` if unlisted |
| `POST /api/scan/label` | Role 2 | multipart `image` | `Product` (`source: "LABEL_PHOTO"`) |
| `POST /api/evaluate` | Role 1 | `{barcode?, product?, profile_ids[]}` | `EvaluationResult` |
| `POST /api/compare` | Role 3 | `{barcode_a, barcode_b, profile_ids[]}` | `CompareResult` |
| `GET /api/history` | Role 3 | — | `ScanResult[]`, newest first |

Things the UI depends on:

- **`Profile.can_edit`** — set it from the Cedar decision for the *calling* user. The
  profiles screen greys out edit/delete on `false`; it never decides this itself.
- **`EvaluationResult.confidence`** and **`data_quality_note`** — rendered next to the
  verdict, not buried. A `LOW` here visibly weakens an otherwise-clean result.
- **`profile_evaluations`** — one entry per requested profile, in any order. A scan
  against three people must return three verdicts, never one merged answer.
- **`profile_severity`** on each flag — drives visual weight. `SEVERE` gets a ring and
  a heavier glyph, not just a red tint.
- **`cross_reactive: true`** — marks a flag as a related risk rather than a direct hit,
  and gets a branch icon plus a softened severity.
- **404 on an unknown barcode** — the UI routes that to the label-photo fallback.
  Don't return an empty `Product` instead.

`lib/mocks/engine.ts` is a deterministic stand-in for Role 1 (synonym + cross-reactivity
matching, no LLM) and `lib/mocks/knowledge.ts` for Role 2's OpenSearch index. Both exist
only so the UI has something honest to render; delete them once the real services land.

## Design

Dark-only bento: black canvas, saturated solid tiles, wide/heavy display type.
Tokens live at the top of `app/globals.css`; each semantic colour has four parts
(`--x` fill, `--x-fg` text on that fill, `--x-soft` dark tint, `--x-line` readable
against black). Class maps in `lib/utils.ts` are the only place verdict colours are
chosen — change them there, not in components.

Verdict colour is never the sole signal: every verdict also carries an icon and a word,
and brand orange sits far from unsafe crimson in hue so the two don't read as the same
alarm.

## Checks

```bash
npm run build     # typecheck + production build
npx eslint .      # lint
```

Worth clicking through by hand: scan `5000159461122` (Snickers) with all three profiles
selected — it should return severe for Aryan, caution for Aaditya and Naman, good data
confidence, and suggest the nut-free dark chocolate as an alternative. Then scan
`8904004401234` (a sparse local record) to see the low-confidence path.
