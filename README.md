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
| **Strands Agents SDK** | The reasoning path that cross-checks ingredients against each profile and writes the explanations. Optional at runtime — see *Reasoning* below. The model behind it is Groq, not an AWS model. |
| **OpenSearch** | Indexes the allergen ontology, E-number table, cross-reactivity map and ingredient descriptions. The same data resolves locally when no cluster is attached. |
| **Textract** | Reads the ingredients panel from a label photo. Currently stood in for by Tesseract locally — `AAHAR_OCR=textract` switches it. |
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

### Fallbacks

Both paths degrade to a local engine rather than failing the request, and the
response always says which one answered:

| Configured | Falls back to | Reported as |
|---|---|---|
| Groq (Strands agent) | The deterministic rulebook | `strands:groq` / `deterministic` |
| Textract | Tesseract | `engine` on the OCR result |

The retry wraps the whole call, not just client construction: a provider can
build fine and then have the call refused or rate-limited, so retrying
construction alone would never reach the next one.

`AAHAR_MODEL_FALLBACK` and `AAHAR_OCR_FALLBACK` override the chains; set either
to `""` to disable.

### Caching

**Off by default** — a real run should exercise the real fallback path, and a
cache hides which one answered. Turn it on for repeated testing, where
re-billing Textract and the model for identical inputs buys nothing:

```bash
AAHAR_CACHE=on
```

When on, results are stored in `.cache/` (gitignored) and reused:

| Cached | Why |
|---|---|
| Open Food Facts lookups | the API rate-limits, and a rehearsal rescans the same products |
| Textract OCR, keyed on the image | billed per page; the same demo label gets scanned repeatedly |
| Agent evaluations, keyed on ingredients + household | billed per token, and unchanged ingredients give the same answer |

Deterministic reasoning is not cached — it is already instant and free. A second
scan of the same product makes **no network calls at all**: a label photo goes
from 2.3s to 2ms.

```bash
rm -rf .cache          # start fresh
```

### Switching the label reader to Textract

Label OCR runs on Tesseract locally and on **AWS Textract** when credentials are
present — one environment variable, the code is written for both.

```bash
brew install awscli
aws configure                 # Access Key ID + Secret from the IAM console
./scripts/check_aws.sh        # read-only pre-flight: credentials and region
```

Then in `.env`:

```bash
AAHAR_OCR=textract            # was tesseract
AWS_REGION=<your region>
```

The OCR result carries the `engine` that answered, so you can tell a Textract
read from a Tesseract one. For reasoning, check `"reasoning"` in any evaluate
response: `"strands:groq"` means the agent ran, `"deterministic"` means it fell
back to the rulebook.

### Deploying

```bash
cd backend && sam build
python ../scripts/check_lambda_package.py   # verify before you deploy
sam deploy --guided
```

Then point `NEXT_PUBLIC_API_BASE_URL` at the `ApiEndpoint` output.

`sam build` only resolves pip dependencies — it cannot tell you that a handler
imports something outside `CodeUri`, which deploys cleanly and then fails on
every request. `backend/src/Makefile` is a custom builder that packages `data/`
and `agent/` alongside the handlers, and `check_lambda_package.py` imports each
handler with only the package on `sys.path`, the way Lambda does.

### Reasoning: agent or rulebook

Evaluation runs through Role 1's Strands agent when a model provider is
configured:

```bash
AAHAR_USE_AGENT=true

# The default. Free tier at console.groq.com/keys.
AAHAR_MODEL_PROVIDER=groq       # pip install openai, set GROQ_API_KEY

# The same agent runs on any of these — Strands abstracts the provider.
AAHAR_MODEL_PROVIDER=ollama     # pip install ollama, then `ollama serve` (local, free)
AAHAR_MODEL_PROVIDER=anthropic  # pip install anthropic, set ANTHROPIC_API_KEY
AAHAR_MODEL_PROVIDER=litellm    # anything LiteLLM supports, set AAHAR_MODEL_ID
```

Put credentials in a `.env` at the repo root (`cp .env.example .env`) — it is
gitignored and loaded on startup. Without one the agent is skipped and the
deterministic rulebook answers, so a fresh clone still works.

Strands drives all of these behind one `Agent` API, so the prompts, the tools
and the structured-output schema are identical whichever you pick — changing
provider is one environment variable rather than a rewrite.

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

- **Label-photo OCR runs on AWS Textract** (`AAHAR_OCR=textract`), with
  Tesseract as the local fallback. Tesseract needs `brew install tesseract`;
  without it and without credentials the endpoint returns 503 rather than
  guessing.
- **The reasoning model is Groq, not an AWS model.** Bedrock model access could
  not be granted on this account inside the event, so the agent runs on Groq
  through the same Strands API. The AWS surface is Textract, Lambda, API
  Gateway, DynamoDB, Cedar and SAM — the model is not part of it, and the
  `reasoning` field on every response says so.
- Caller identity is passed via headers rather than Cognito, so the Cedar rules can be
  demonstrated by switching roles. Wiring a JWT authorizer is the next step.
- Open Food Facts coverage of Indian products is patchy; that is exactly why the
  confidence signal and the label-photo fallback exist.
