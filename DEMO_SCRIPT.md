# Demo video script — 3 minutes, First Commit

The video is the only thing judges see. A feature not shown here does not count,
even if it is in the repo. The rules also say the video must **show** AWS usage —
naming AWS in the writeup is not enough.

Everything below is verified working as of 20 Sept 2026. The AWS service shown
on camera is **Textract**, which does the label OCR on a real call; the
reasoning model is Groq via the Strands Agents SDK, and the script never claims
otherwise.

---

## Before you record

```bash
# 1. cluster up + seeded (84 docs across 4 indices)
curl -s localhost:9200/_cat/indices?v

# 2. if it is empty, reseed — idempotent, safe to re-run
.venv/bin/python -m data.seed.seed_opensearch

# 3. real agent, real Textract
export AAHAR_USE_AGENT=true AAHAR_MODEL_PROVIDER=groq AAHAR_OCR=textract

# 4. start both
./dev.sh
```

Have ready: a **physical product** with a real ingredients label, and the
household set up with at least two people whose restrictions differ (one severe
dairy, one mild soy). The contrast between the two is the product.

---

## 0:00 – 0:20 — The problem, with a face on it

Hold the packet. Read one line of the ingredients list aloud — the unreadable
part, "sodium caseinate, E322, hydrolysed vegetable protein".

> "My cousin is severely allergic to dairy. This says 'sodium caseinate'. That
> *is* dairy. Nothing on this packet tells her that."

Do not explain the architecture yet. Show the problem first.

## 0:20 – 0:50 — Scan a real label → **AWS Textract**

Photograph the label in the app.

**Say the service name out loud while the spinner is up:** "That photo goes to
**AWS Textract**, which reads the ingredient text off the packaging."

**On screen, show the evidence:** the returned blocks with their confidence
scores. Textract returns 91–99% on a flat label; that number on screen is the
proof the call was real. If you have a curved/shiny packet, use it — that is
where Textract visibly beats local OCR, and it is worth 5 seconds.

## 0:50 – 1:30 — The verdict, per person → **Strands Agents SDK**

This is the heart of the product. Show the **per-person** verdict cards, not a
single pass/fail.

- Cousin (severe dairy) → **UNSAFE**, "contains skimmed milk powder"
- You (mild soy) → **CAUTION**, "soy lecithin (E322)"

> "Same product, two different answers, because it knows who is eating it."

**Say it accurately:** "The reasoning runs through the **Strands Agents SDK** —
AWS's open-source agent framework — over our allergen knowledge base." Strands
is the AWS open-source project here; do not name an AWS *model*, because the
model is Groq.

**Show the evidence:** the `reasoning` field in the response. `"strands:groq"`
means the agent answered. `"deterministic"` means the rulebook did — still a
correct verdict, but then do not claim the agent ran.

## 1:30 – 2:00 — Cross-reactivity + confidence — the bit nobody else has

Pick the feature that makes this more than a lookup table:

- **Cross-reactivity**: a latex allergy flags banana. Explain in one line that
  this is a real clinical association most apps miss.
- **Confidence**: show a thin-data product returning LOW and saying so, instead
  of guessing. "It tells you when it does not know" is a trust feature, and
  judges notice it.

## 2:00 – 2:25 — Tap-to-explain → **OpenSearch**

Tap an ingredient you cannot pronounce. Plain-English answer appears.

Now the moment that shows OpenSearch is real: the label you scanned says
**"XANTHAM GUM"** — a misspelling of xanthan gum. The curated index has no such
entry, so exact lookup finds nothing.

> "The local index has no match for that spelling. **Amazon OpenSearch** does a
> fuzzy search across the knowledge base and finds it anyway."

**Show the evidence:** `resolved_via: "opensearch"` in the response. Known
ingredients come back `"catalogue"` or `"local"`; only the rescue says
`"opensearch"`. That difference on screen is the proof.

## 2:25 – 2:45 — Household permissions → **Cedar**

Switch to the child profile and try to edit a parent's restrictions. Denied.

> "Who may edit whose profile is a **Cedar** policy, not an if-statement — and
> it fails closed."

Show `backend/policies/policies.cedar` on screen for two seconds. Real policy
text reads as real.

## 2:45 – 3:00 — Close

One sentence on impact, one on the stack:

> "AaharKavach turns a label you cannot read into a straight answer for each
> person in your house. Textract reads it, a Strands agent reasons about it,
> OpenSearch explains it, Cedar decides who can change it."

---

## Rules checklist before you upload

- [ ] Under 3:00. Hard limit.
- [ ] Every AWS service **named out loud** *and* shown on screen with evidence.
- [ ] No claim made that the run did not actually demonstrate.
- [ ] AI coding tools listed in the writeup (required).
- [ ] Repo is public and its history sits inside 17–20 Sept 2026.
- [ ] Submitted early — you can keep editing until the deadline, but not after.

## Do not say any of this unless it is true on the day

- **Any AWS model.** The reasoning runs on **Groq**, which is not AWS. Bedrock
  was removed from the project on 20 Sept — model access could not be granted
  on this account in time. Name **Strands Agents SDK** (an AWS open-source
  project) for the reasoning step, never an AWS model.
- **Lambda / API Gateway / DynamoDB** — nothing is deployed: 0 CloudFormation
  stacks, 0 functions, 0 tables. Do not imply a live cloud deployment.
- **OpenSearch on AWS** — the cluster is local. It is a genuine OpenSearch
  cluster and genuinely queried, which counts for the Build It track; it is not
  Amazon OpenSearch Service. Say "OpenSearch", not "Amazon OpenSearch Service",
  unless you move it.

## Why there is no AWS model in this demo

Amazon Bedrock was the original reasoning target and has been removed from the
project. `get_foundation_model_availability` reported `authorizationStatus:
NOT_AUTHORIZED` on every model in every region, with `agreementAvailability:
NOT_AVAILABLE` for the Anthropic models — the account could not even accept the
model agreement, which is a billing/verification state, not an IAM one. Keeping
a provider that failed over to Groq on every call would have left the code and
the script reading as if AWS answered, so it is gone.

**This does not weaken the submission.** Strands Agents SDK, Cedar and SAM are
AWS open-source projects on the Build It list, OpenSearch is genuinely queried,
and **Textract is a live AWS service verified working through the real
pipeline**. That is four AWS technologies with evidence on camera.

Before recording, confirm the agent is actually answering:

```bash
set -a && . ./.env && set +a && .venv/bin/python scripts/verify_agent.py
```

It exits non-zero unless the configured provider itself answered, so a pass is
evidence rather than a guess. In the app, `"reasoning": "strands:groq"` on an
evaluate response says the same thing.

Separately, unrelated to the demo: the **root** access keys are still active on
this laptop. Delete them in the console (IAM → My security credentials) — the
app only needs the dedicated IAM user's Textract permission.
