# AaharKavach — आहार कवच

**Scan a barcode. See, in plain English, whether a product is safe for everyone in your
household — not just for you.**

Built for **First Commit** (WeMakeDevs Bharat Builds Tour × AWS), 17–20 September 2026,
by team **Push Masters**.

---

## The problem

Reading an Indian food label is slow and error-prone even when you know what you are
looking for.

- **Allergens hide behind other names.** Casein and whey are milk. Maida and suji are
  wheat. Kaju is cashew. A parent scanning for "dairy" will not find "sodium caseinate".
- **E-numbers say nothing.** E120 is carmine, made from insects. E631 can be fish-derived.
  Neither label tells a vegetarian that.
- **Cross-reactions are invisible.** A latex allergy means banana, avocado and potato can
  trigger a reaction, and no label mentions latex.
- **Households are not one person.** A parent shops for a child with a severe peanut
  allergy, a partner avoiding gluten, and themselves. Existing apps answer for one
  profile at a time.
- **Confidence is never stated.** A tool that says "safe" from a half-empty database
  record is more dangerous than one that admits it does not know.

## What it does

1. Set up the people in your household, each with their own restrictions, tagged
   **Mild / Moderate / Severe**.
2. Pick who this scan is for — one person, several, or everyone.
3. Scan a barcode, type it, or photograph the ingredients panel.
4. Get **one verdict per person**, never a merged answer, with:
   - the specific ingredient that tripped it and *why*, in plain language
   - warning weight scaled to that person's severity
   - cross-reactive risks flagged separately from direct hits
   - an explicit **data-confidence** badge, so a thin record never reads as a confident
     all-clear
5. Tap any ingredient — flagged or not — for a one-line explanation of what it actually is.
6. Compare two products side by side, and keep a history of what you have scanned.

## Where AWS fits

| Component | What it does here |
|---|---|
| **Cedar** | Policy-as-code for the household. Admins manage everyone; members edit only themselves; a child's restrictions are read-only. Enforced server-side on every profile request — the UI only reflects the decision. |
| **AWS SAM** | `template.yaml` defines the API Gateway routes, five Lambda functions and two DynamoDB tables. `sam deploy` stands the whole backend up. |
| **AWS Lambda + API Gateway** | Every endpoint: profiles, barcode lookup, label photo, evaluate, compare, history. |
| **DynamoDB** | Household profiles and scan history, keyed by household. |
| **Strands Agents SDK** | The reasoning path that cross-checks ingredients against each profile and writes the explanations. Optional at runtime — see *Reasoning* below. |
| **Amazon Bedrock** | Hosts the model the Strands agent calls. |
| **OpenSearch** | Indexes the allergen ontology, E-number table, cross-reactivity map and ingredient descriptions. The same data resolves locally when no cluster is attached. |
| **Open Food Facts** | Public barcode database for product records (not AWS, but the external data source).

## Running it

Two processes. Nothing else to install — no Docker, no AWS account.

```bash
# 1. Backend  (http://localhost:3001)
python3 -m venv .venv
.venv/bin/pip install -r data/requirements.txt -r backend/src/requirements.txt
.venv/bin/python backend/local_server.py

# 2. Frontend (http://localhost:3000)
cd frontend && npm install && npm run dev
```

The frontend reads `frontend/.env.local`:

```bash
NEXT_PUBLIC_USE_MOCKS=false                     # true → run the UI standalone
NEXT_PUBLIC_API_BASE_URL=http://localhost:3001  # or the API Gateway URL
```

### Deploying

```bash
cd backend && sam build && sam deploy --guided
```

Then point `NEXT_PUBLIC_API_BASE_URL` at the `ApiEndpoint` output.

### Reasoning: agent or rulebook

Evaluation runs through Role 1's Strands agent when you set:

```bash
AAHAR_USE_AGENT=true
AAHAR_BEDROCK_MODEL=<a model id enabled in your Bedrock account>
```

Otherwise — and whenever the agent errors — a **deterministic rulebook** resolves every
ingredient through the same knowledge base and applies the same severity rules. Each
response says which path produced it in its `reasoning` field.

This is deliberate. For an allergen app, an answer derived from a rulebook beats
"service unavailable", and the demo has to work on conference wifi.

Product lookups behave the same way: Open Food Facts first, a bundled catalogue of 13
products as the fallback, and the response says which was used.

## Layout

```
agent/     Role 1 — Strands agent, prompts, structured output schema
data/      Role 2 — allergen ontology, E-numbers, cross-reactivity, OFF client, confidence
backend/   Role 3 — SAM template, Cedar policies, Lambda handlers, shared integration layer
frontend/  Role 4 — Next.js app (see frontend/README.md)
```

`frontend/lib/types.ts` and `backend/src/shared/contracts.py` are the same contract in two
languages. Everything on the wire conforms to it; `backend/src/shared/adapters.py` is the
only place that translates between a role's internal shape and that contract.

## Tests

```bash
.venv/bin/python -m pytest          # 54 tests (paths come from pytest.ini)
cd frontend && npm run build && npx eslint .
```

Role 1's agent tests skip themselves unless you also install
`agent/requirements.txt`, since the Strands SDK is optional at runtime.

Worth checking by hand, all against the bundled catalogue so they are stable:

| Scan | Expect |
|---|---|
| `5000159461122` Snickers | Severe for a peanut allergy, caution for soy and egg |
| `8901063152762` Good Day | Maida caught as gluten; butter *and* milk solids as dairy |
| `8901030865278` Banana chips | Latex cross-reaction, severity softened to mild |
| `8901491101837` Lay's | E627/E631 flagged as possibly animal-derived for a vegetarian |
| `8904004401234` Namkeen | "Thin data" — low confidence, with the double-check note |
| `8908003847412` Dark chocolate | Clear — cocoa butter is *not* treated as dairy |

## Team — Push Masters

| | |
|---|---|
| **Chezhil S** | Frontend, scanner and UX; integration |
| **Aaditya Arunpal** | Strands agent and reasoning schema |
| **Naman Raghav** | SAM template, Cedar policies, Lambda handlers |
| **Jyothi Xavier Rodrigues** | Allergen knowledge base, Open Food Facts client, confidence scoring |

## Honest limits

- The label-photo path returns a low-confidence placeholder record; OCR/vision is not
  wired up yet, but the confidence warning it triggers is real.
- The Strands agent path is implemented and importable but has not been run against a
  live Bedrock model — the deterministic path is what the demo shows.
- Caller identity is passed via headers rather than Cognito, so the Cedar rules can be
  demonstrated by switching roles. Wiring a JWT authorizer is the next step.
- Open Food Facts coverage of Indian products is patchy; that is exactly why the
  confidence signal and the label-photo fallback exist.
