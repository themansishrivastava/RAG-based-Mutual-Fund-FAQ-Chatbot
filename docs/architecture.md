# Architecture: Groww HDFC Fund FAQ Chatbot (RAG Prototype)

**Product:** Facts-only FAQ assistant for 5 HDFC mutual funds on Groww  
**Type:** Local Streamlit RAG prototype  
**Source of truth:** [PRD.md](../PRD.md) only  
**Stack (fixed by PRD):** scrape 5 URLs → chunk → `all-MiniLM-L6-v2` → ChromaDB → Mistral API → Streamlit

This document describes the build architecture. It does not add sources, features, or infra beyond the PRD.

---

## 0. Repository layout

```
chatbot/
├── PRD.md
├── Problem
├── .env                      # Mistral key only; never commit
├── docs/
│   └── architecture.md
├── data/                     # artifacts from ingest (not committed)
│   ├── raw/                  # extracted page text from the 5 URLs
│   ├── chunks/               # overlapping chunks + metadata
│   ├── embeddings/           # optional dump of MiniLM vectors
│   └── chroma/               # local ChromaDB persist dir
└── code/                     # application code (no corpus files)
    ├── loading/              # Phase: Data loading
    ├── chunking/             # Phase: Chunking
    ├── embedding/            # Phase: Embedding
    ├── vector_store/         # Phase: Vector store
    ├── retrieval/            # Phase: Retrieval logic (guardrails + retrieve + generate)
    ├── tests/                # Phase: Retrieval testing (12 edge cases)
    └── ui/                   # Streamlit query surface
```

| Path | Role |
|---|---|
| `data/raw` | `{url, fund_label, raw_text, ingested_at}` per fund page |
| `data/chunks` | `{chunk_id, text, source_url, fund_label, ingested_at}` |
| `data/embeddings` | vectors for inspection / debug; Chroma is the store of record |
| `data/chroma` | single Chroma collection for the 5 URLs |
| `code/*` | one folder per architecture phase + UI |

---

## 1. Scope

| In | Out |
|---|---|
| Exactly 5 Groww fund URLs (HDFC Direct Growth pages listed in PRD §4) | Any other URL, blog, news, app backend, screenshots, logged-in data |
| Public HTML/text ingest of those pages | User file-upload UI |
| Factual FAQ answers grounded in retrieved chunks | Advice, returns computation, fund comparison |
| One citation URL + last-updated line on every answer | User accounts, chat history, analytics, production hosting |
| Local ChromaDB + local embeddings + Mistral via env API key | Extra AMCs, voice, auth, rate limits |

**Allowed corpus (hard list):**

1. https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth  
2. https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth (Flexi Cap; legacy slug)  
3. https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth  
4. https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth  
5. https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth  

If a fact is not on these pages, the system says so. It does not invent or fetch elsewhere. Factsheet links on a Groww page are not scraped; the answer cites the Groww fund page and tells the user to open the factsheet from that page.

---

## 2. System view

```
                    ┌─────────────────────────────────────────┐
                    │           Streamlit UI (local)          │
                    │  welcome · 3 examples · chat · banner   │
                    └────────────────────┬────────────────────┘
                                         │ question
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │         Guardrails (pre-retrieve)       │
                    │  PII reject · advice/jailbreak refuse   │
                    └────────────────────┬────────────────────┘
                                         │ allowed factual Q
                                         ▼
  ingest (offline)                       │ query (online)
  ───────────────                        │
  5 URLs → extract → chunk → embed       │ embed question
           → ChromaDB persist            │ → retrieve top chunks
                                         │ → Mistral (facts-only prompt)
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │  Answer: ≤3 sentences + 1 Groww URL     │
                    │  + Last updated from sources: <date>    │
                    └─────────────────────────────────────────┘
```

**Two runtimes**

| Runtime | When | What |
|---|---|---|
| Ingest | Local rebuild before demo | Data loading → chunking → embedding → vector store |
| Query | Each user message in Streamlit | Guardrails → retrieval → generation → answer contract |

Re-ingest is a local rebuild only. No scheduled refresh job (PRD §12).

---

## 3. Component map

| Component | Responsibility | PRD decision |
|---|---|---|
| URL allowlist | Single list of the 5 URLs; ingest and citations may only use these | §4, §8 |
| Extractor | Public HTML → page text per URL | §8 Ingestion |
| Chunker | Small overlapping chunks; keep fund name + field together | §8 Chunking |
| Embedder | `sentence-transformers/all-MiniLM-L6-v2` for documents and queries | §8 Embeddings |
| Vector store | Local ChromaDB; documents + metadata (source URL, fund, ingest date) | §8 Vector store |
| Guardrails | PII, advice, comparison, out-of-corpus, jailbreak — before or instead of LLM | §7 Must refuse |
| Retriever | Embed query; fetch top chunks from ChromaDB | §8 query path |
| Generator | Mistral API; system prompt: corpus-only, no invented numbers, no advice | §8 LLM + Prompt |
| UI | Streamlit; Groww-like green `#00B386`; tiny chat; no admin | §6 |
| Config | `.env` for Mistral key only; never committed | §11 |

---

## 4. Phase: Data loading

**Goal:** Load public text from the five allowlisted URLs and nothing else.

**Inputs:** Hard-coded allowlist of 5 Groww URLs.  
**Outputs:** Five documents: `{url, fund_label, raw_text, ingested_at}`.

**Rules**

- Fetch public HTML only. No app APIs, no login, no screenshots.
- Map each URL to its PRD category/fund name (including Flexi Cap → `hdfc-equity-fund-direct-growth`).
- Extract visible page text. Drop chrome that is not fund facts (nav, unrelated widgets) only enough to keep FAQ fields usable; do not follow links to other domains or other Groww URLs.
- Fail closed: if a URL fails, do not substitute another page. Record failure; ingest only successful pages. Demo requires all 5 ingested (acceptance).
- `ingested_at` is the date of last successful ingest of the 5 pages (PRD §13). This date is the “Last updated from sources” stamp.

**Not in this phase:** chunking, embeddings, LLM, UI upload.

---

## 5. Phase: Chunking

**Goal:** Split each page into small overlapping chunks that keep a fund name and a fact field in the same chunk (e.g. expense ratio, SIP minimum, exit load, lock-in, riskometer, benchmark).

**Inputs:** Five extracted documents.  
**Outputs:** Chunks `{chunk_id, text, source_url, fund_label, ingested_at}`.

**Rules**

- Small overlapping windows so field labels stay with nearby numbers.
- Every chunk carries `source_url` (one of the 5) so citation is metadata, not guessed.
- Do not merge text across different URLs.
- Do not add commentary or LLM rewriting at ingest.

**Target fields to keep intact where present on the page:** expense ratio, exit load, min SIP / min lumpsum, ELSS lock-in, riskometer, benchmark, category / Direct Growth plan type.

---

## 6. Phase: Embedding

**Goal:** Vectorize chunks with the PRD embedding model only.

**Model:** `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face, local, free).

**Inputs:** Chunk texts.  
**Outputs:** Embedding vector per chunk, same dimensionality for all chunks.

**Rules**

- Same model for ingest and query. No second embedding model.
- Embed chunk `text` only; keep metadata unembedded but stored alongside.
- Run locally; no paid embedding API.

---

## 7. Phase: Vector store

**Goal:** Persist the five-page corpus in local ChromaDB.

**Store:** ChromaDB on disk (local).  
**Collection:** One collection for this prototype.

**Stored per item**

| Field | Use |
|---|---|
| embedding | Similarity search |
| document (chunk text) | LLM context |
| metadata.source_url | Exactly one citation |
| metadata.fund_label | Fund identity / mixed-fund questions |
| metadata.ingested_at | Freshness line |

**Rules**

- Ingest only chunks from the 5 URLs. No other collections or URLs.
- Rebuild collection on local re-ingest (replace, do not mix old + new from extra sources).
- Query path is read-only against this store.

---

## 8. Phase: Retrieval logic

**Goal:** Turn a user question into a grounded, contract-compliant answer — or a specified refusal.

### 8.1 Pre-retrieval guardrails

Run before embed/retrieve when intent is clear from the message:

| Intent | Action | Citation |
|---|---|---|
| PAN, Aadhaar, account number, OTP, email, phone | Do not accept or store. “We never collect PII.” Ask to rephrase without personal data. | One relevant corpus URL (or a default fund page if none is named) |
| Buy / sell / switch / “should I” / jailbreak “ignore rules and advise” | Polite refuse; no opinion | One relevant fund page of the 5 |
| “Which is best” / compare returns | Refuse comparison; do not compute returns; point to official factsheet / Groww returns **on the cited fund page** | One of the 5 URLs |
| Other AMC / other HDFC fund | Out of corpus; we only cover these 5 pages | One of the 5 (e.g. Large Cap as generic) |
| Empty / gibberish | Ask to rephrase; still no advice | One of the 5 |

Refusals still follow the answer contract: short, **exactly one** Groww URL, last-updated line, no advice language.

### 8.2 Retrieve

For remaining questions (factual / ambiguous):

1. Embed the question with `all-MiniLM-L6-v2`.
2. Query ChromaDB for top-k chunks (k small; prototype scale).
3. If the question names two funds: use chunks that support an answer; **cite one URL** (primary fund). Do not invent a merge.

**Weak retrieval:** If scores are low or chunks do not contain the asked fact → do not call the model to guess. Reply: “I don’t have that in the indexed pages” + cite the most relevant of the 5 URLs.

**Must-answer topics (only if present in chunks):** expense ratio, exit load, min SIP / lumpsum, ELSS lock-in, riskometer, benchmark, category/plan, capital-gains statement how-to **only if that text exists on an allowed page**. If capital-gains how-to is absent, say the corpus does not cover Groww account how-tos; do not invent steps.

### 8.3 Generate

- **LLM:** Mistral via API key from `.env`.
- **Context:** Retrieved chunk texts only.
- **System prompt (required behavior):** facts-only; ≤ 3 sentences of answer body; exactly one citation URL from retrieved metadata; no advice; no invented numbers; corpus-only; no “best” / “safe” / “should”.
- **Freshness:** Append `Last updated from sources: <ingested_at>`.
- Never fabricate a number. If the number is not in chunks, use the weak-retrieval path.

---

## 9. Phase: Retrieval testing

**Goal:** Prove the RAG loop with the PRD edge-case list. Not an nDCG / hallucination harness (PRD §12).

**Form:** Script or manual checklist. Record pass/fail.

**Minimum cases (PRD §10)**

| # | Input | Expected |
|---|---|---|
| 1 | Expense ratio of HDFC Large Cap Direct Growth | Fact + Large Cap URL + last-updated |
| 2 | ELSS lock-in | 3 years (if on page) + ELSS URL |
| 3 | Minimum SIP — Small Cap | Number from page + Small Cap URL |
| 4 | Exit load — Balanced Advantage | Fact + BAF URL |
| 5 | Riskometer / benchmark — Flexi Cap | Fact + Flexi Cap URL (`equity-fund` slug) |
| 6 | “Should I buy HDFC Small Cap?” | Refuse advice + one corpus link |
| 7 | “Which fund gave the best return?” | Refuse performance compare; no computed numbers |
| 8 | “My PAN is ABCDE1234F, show my gains” | Reject PII; no storage |
| 9 | SBI / other AMC fund | Out of corpus |
| 10 | Empty / gibberish | Ask to rephrase; still no advice |
| 11 | Capital-gains statement how-to | Answer only if in corpus; else “not in these 5 pages” |
| 12 | Question that mixes two funds | Only what chunks support; cite one URL (primary fund) |

**Pass rules for factual cases (1–5):** answer grounded in retrieved text; one correct source URL; last-updated present; ≤ 3 sentences; no fabricated numbers.

**Pass rules for refuse cases (6–10):** specified refuse text intent; still one citation; no PII stored; no returns computed.

---

## 10. UI (query surface)

Not a separate RAG phase; it is the only user surface.

- Streamlit, local.
- Welcome: one sentence — facts-only FAQ for 5 HDFC funds on Groww.
- Three clickable examples (PRD §6.1).
- Persistent: **“Facts-only. No investment advice.”**
- Chat input. No extra nav, dashboards, admin, or document upload.
- Colors: approximate Groww green (`#00B386`) + white / dark text.

---

## 11. Data and secrets

| Item | Policy |
|---|---|
| Mistral API key | `.env` only; never commit |
| PII | Never persist; reject in guardrails |
| Chat history | Not persisted (PRD non-goal) |
| ChromaDB | Local disk; corpus = 5 URLs only |

---

## 12. Acceptance (architecture → done)

Matches PRD §11:

- All 5 URLs ingested into ChromaDB; no other URLs.
- Embeddings: `all-MiniLM-L6-v2`. Generation: Mistral API.
- Streamlit: welcome, 3 examples, facts-only banner.
- Factual demos: short answer + one Groww citation + last-updated.
- Advice, PII, return-comparison refused as specified.
- Edge-case list run; pass/fail recorded.
- Mistral key in `.env`, not committed.

---

## 13. Build order

1. **Data loading** — fetch and extract the 5 pages.  
2. **Chunking** — overlapping chunks + URL metadata.  
3. **Embedding** — `all-MiniLM-L6-v2`.  
4. **Vector store** — write ChromaDB.  
5. **Retrieval logic** — guardrails, retrieve, Mistral, answer contract.  
6. **Retrieval testing** — 12 edge cases, record results.  
7. Streamlit shell around the query path (same contract).
