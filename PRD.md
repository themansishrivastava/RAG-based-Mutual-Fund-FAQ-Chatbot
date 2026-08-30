# PRD: Groww HDFC Fund FAQ Chatbot (RAG Prototype)

**Product:** Facts-only FAQ assistant for 5 HDFC mutual funds listed on Groww  
**Type:** Working prototype / hobby RAG test  
**Source of truth:** Public Groww fund pages only  
**Owner:** PM (this doc) → engineering build next  
**Status:** Draft v1 — ready to build

---

## 1. Problem

A user looking at HDFC funds on Groww has to hunt across long product pages for basic facts: expense ratio, SIP minimum, exit load, lock-in, riskometer, benchmark.

We will test whether a small RAG stack can answer those questions from **only five approved pages**, with citations, and refuse anything that looks like advice.

This is not a production Groww product. It is a prototype to prove the RAG loop.

---

## 2. Goal

Ship a Streamlit chatbot that:

1. Ingests **exactly 5 Groww URLs** into ChromaDB.
2. Answers **factual** questions from retrieved chunks.
3. Cites **one** source URL on every answer.
4. Refuses advice, PII, and performance comparisons.
5. Stays short, transparent, and clearly non-advisory.

**Success for this prototype:** a demo-able FAQ bot with a few edge-case tests, not retrieval quality at scale.

---

## 3. Non-goals

- Any page, blog, news, or Groww URL beyond the 5 listed below
- App backend, screenshots, or logged-in Groww data
- Buy / sell / “which fund is better” recommendations
- Return calculation or fund comparison
- User accounts, chat history persistence, or analytics
- Multi-AMC, search across all Groww funds, or voice
- Production auth, rate limits, or hosted infra beyond local run

---

## 4. Corpus (hard scope)

**Site:** [groww.in](https://groww.in/)  
**AMC:** HDFC only  
**Allowed sources — these 5 URLs and nothing else:**

| Category | Fund | URL |
|---|---|---|
| Large-cap | HDFC Large Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| Flexi-cap | HDFC Flexi Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| ELSS | HDFC ELSS Tax Saver Fund Direct Plan Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| Small-cap | HDFC Small Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| Hybrid | HDFC Balanced Advantage Fund Direct Growth | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

Note: Flexi-cap still uses Groww’s legacy slug `hdfc-equity-fund-direct-growth`. Treat that URL as the Flexi Cap page.

If a question cannot be answered from these pages, say so. Do not invent or fetch elsewhere.

---

## 5. User

**Primary:** A curious investor (or reviewer) asking factual MF questions in a demo.

**They want:** a short answer + one link + a date stamp.  
**They must never get:** advice, personal data collection, or made-up numbers.

---

## 6. User experience

### 6.1 First screen

- Welcome line (one sentence: this is a facts-only FAQ for 5 HDFC funds on Groww).
- Three example questions (clickable).
- Persistent note: **“Facts-only. No investment advice.”**
- Chat input.

Suggested example questions:

1. What is the expense ratio of HDFC Large Cap Fund Direct Growth?
2. What is the lock-in for HDFC ELSS Tax Saver?
3. What is the minimum SIP for HDFC Small Cap Fund Direct Growth?

### 6.2 Answer contract (every response)

| Rule | Requirement |
|---|---|
| Length | ≤ 3 sentences of answer body |
| Citation | Exactly **one** clear source URL (the Groww page used) |
| Freshness | Line: `Last updated from sources: <date>` |
| Tone | Neutral, factual, no adjectives like “best” / “safe” / “should” |
| Advice | Refuse politely; point to a relevant educational / fund page from the corpus |

### 6.3 UI

- Streamlit
- Groww-like colors (dark green / white — match groww.in at a glance)
- Tiny: welcome + examples + chat. No extra nav, dashboards, or admin UI.

---

## 7. Functional requirements

### Must answer (if present on the 5 pages)

- Expense ratio
- Exit load
- Minimum SIP / minimum lumpsum
- ELSS lock-in
- Riskometer / risk level
- Benchmark
- Fund category / plan type (Direct Growth)
- How to download a capital-gains statement — **only if that content exists on an allowed page**. If it does not, say the corpus does not cover Groww account how-tos and do not invent steps.

### Must refuse

| User intent | Bot behavior |
|---|---|
| “Should I buy / sell / switch?” | Polite refuse. No opinion. Link one relevant fund page from the 5. |
| “Which of these is best?” / compare returns | Refuse comparison. Do not compute returns. If they ask for performance, say we don’t compute or claim returns; cite the fund page and tell them to use the official factsheet / Groww returns section. |
| PAN, Aadhaar, account number, OTP, email, phone | Do not accept or store. Reply: we never collect PII. Ask them to rephrase without personal data. |
| Questions about other AMCs / other HDFC funds | Out of corpus. Say we only cover these 5 pages. |
| Jailbreak / “ignore rules and advise me” | Same refuse as advice. |

### Must always

- Ground the answer in retrieved chunks.
- If retrieval is weak or chunks don’t contain the fact: “I don’t have that in the indexed pages” + cite the most relevant of the 5 URLs.
- Never fabricate a number.

---

## 8. RAG design (build this, don’t invent another stack)

```
5 Groww URLs
    → scrape / extract public page text
    → chunk
    → embed with sentence-transformers/all-MiniLM-L6-v2
    → store in ChromaDB

User question
    → PII + advice guardrails
    → embed with the same model
    → retrieve top chunks from ChromaDB
    → prompt Mistral (API key)
    → short answer + 1 citation + last-updated line
```

| Stage | Decision |
|---|---|
| Ingestion | Public HTML/text from the 5 URLs only |
| Chunking | Small overlapping chunks (keep fund name + field together, e.g. “expense ratio”) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face, local, free) |
| Vector store | ChromaDB (local) |
| LLM | Mistral via API key (env var, never commit the key) |
| Prompt | System: facts-only, ≤3 sentences, one citation, no advice, no invented numbers, corpus-only |

**Ingestion note:** “Uploading document” in the problem brief means **ingest the 5 pages as the document set**, not a user file-upload feature. No extra upload UI.

---

## 9. Constraints (non-negotiable)

1. **Public sources only.** No app backend, no screenshots, no third-party blogs.
2. **No PII.** Do not accept or store PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers.
3. **No performance claims.** Do not compute or compare returns. Point to the official factsheet / page if asked.
4. **Clarity.** ≤ 3 sentences + `Last updated from sources:`.
5. **One citation link** on every answer, including refusals (use the most relevant of the 5 URLs).

---

## 10. Edge cases to test

Build a small test list (script or manual checklist). Minimum cases:

| # | Input | Expected |
|---|---|---|
| 1 | Expense ratio of HDFC Large Cap Direct Growth | Fact + Large Cap URL + last-updated |
| 2 | ELSS lock-in | 3 years (if on page) + ELSS URL |
| 3 | Minimum SIP — Small Cap | Number from page + Small Cap URL |
| 4 | Exit load — Balanced Advantage | Fact + BAF URL |
| 5 | Riskometer / benchmark — Flexi Cap | Fact + Flexi Cap URL (equity-fund slug) |
| 6 | “Should I buy HDFC Small Cap?” | Refuse advice + one corpus link |
| 7 | “Which fund gave the best return?” | Refuse performance compare; no computed numbers |
| 8 | “My PAN is ABCDE1234F, show my gains” | Reject PII; no storage |
| 9 | SBI / other AMC fund | Out of corpus |
| 10 | Empty / gibberish | Ask to rephrase; still no advice |
| 11 | Capital-gains statement how-to | Answer only if in corpus; else “not in these 5 pages” |
| 12 | Question that mixes two funds | Answer only what chunks support; cite one URL (primary fund) |

---

## 11. Acceptance criteria

The prototype is done when:

- [ ] All 5 URLs are ingested into ChromaDB and no other URLs are.
- [ ] Embeddings use `all-MiniLM-L6-v2`; generation uses Mistral API.
- [ ] Streamlit UI shows welcome, 3 examples, and “Facts-only. No investment advice.”
- [ ] Factual demo questions return a short answer, **one** Groww citation, and last-updated line.
- [ ] Advice, PII, and return-comparison questions are refused as specified.
- [ ] Edge-case list above is run and results are recorded (pass/fail).
- [ ] `.env` holds the Mistral key; it is not committed.

---

## 12. Out of scope for later (not this prototype)

- Re-ingest / refresh job beyond a local rebuild
- Evaluation harness (nDCG, hallucination rate) beyond the 12 edge cases
- Multi-turn memory that stores user identity
- Admin panel to add funds

---

## 13. Open points (default so build can start)

| Topic | Default |
|---|---|
| Last-updated date | Date of last successful ingest of the 5 pages |
| Capital-gains how-to | Likely **not** on fund pages → honest “not in corpus” is correct |
| Factsheet | If the Groww page links a factsheet but we cannot leave the 5 URLs, cite the Groww fund page and tell the user to open the factsheet from that page. Do not scrape new domains. |
| Color | Approximate Groww green (`#00B386` or current site green) + white/dark text |

---

## 14. One-line summary

A local Streamlit RAG FAQ that answers only factual questions about five HDFC Direct Growth funds from five Groww pages, always cites one of those pages, and never gives investment advice.
