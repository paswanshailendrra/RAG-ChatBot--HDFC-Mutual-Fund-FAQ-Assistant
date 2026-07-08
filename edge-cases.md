# Edge Cases & Corner Scenarios

This document catalogs all edge cases and corner scenarios that the Mutual Fund FAQ Assistant must handle gracefully, organized by system layer as defined in the [Architecture.md](file:///Users/khushbushailendrra/Documents/GenAI%20NextLeap/AMC%20%28Asset%20Management%20Company%29%20/Architecture.md) and [Implementation Plan](file:///Users/khushbushailendrra/.gemini/antigravity-ide/brain/328117e7-398c-4c28-bd92-68fe9e70fa99/implementation_plan.md).

---

## 1. Data Ingestion & Web Scraping Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 1.1 | **Groww URL returns HTTP 403/429 (blocked or rate-limited)** | Retry with exponential backoff. After max retries, log the failure and alert the operator. Do not serve stale data without flagging it. |
| 1.2 | **Groww website HTML structure changes (DOM breakage)** | Scraper should fail gracefully, log the specific URL and element that broke, and skip that URL rather than ingesting garbage data. |
| 1.3 | **Groww page is temporarily down (HTTP 5xx)** | Retry logic with a timeout. If the page remains down, use the last successfully scraped version (if available) and append a staleness warning. |
| 1.4 | **JavaScript-rendered content not captured by BeautifulSoup** | Detect if critical sections (e.g., NAV, expense ratio) are missing in the parsed output. If so, fall back to a JS-rendering tool like Playwright. |
| 1.5 | **Duplicate or overlapping content across the 5 scheme pages** | De-duplicate chunks during ingestion based on content hashing to prevent redundant retrieval results. |
| 1.6 | **Special characters / Unicode in scraped text (₹, %, etc.)** | Ensure the text cleaning pipeline preserves financial symbols (₹, %, ₹Cr) and does not strip or corrupt them. |
| 1.7 | **Empty or near-empty page returned** | Validate scraped content length. If below a minimum threshold (e.g., < 100 chars), reject and log as a failed scrape. |

---

## 2. Chunking & Text Processing Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 2.1 | **Tabular data split across multiple chunks** | Use chunking strategies that respect table boundaries. Consider treating each table as a single chunk, even if it exceeds the default chunk size. |
| 2.2 | **Very short text sections (e.g., single-line facts)** | Avoid creating chunks that are too small to be meaningful. Set a minimum chunk size or merge adjacent short sections. |
| 2.3 | **Chunk loses its context (e.g., "0.5%" without knowing it refers to exit load)** | Use overlapping chunks and prepend section headers to each chunk so context is preserved. |
| 2.4 | **Metadata (source URL) gets lost during splitting** | Ensure the chunking pipeline explicitly attaches the source Groww URL to every chunk's metadata dictionary. Unit test this. |

---

## 3. Embedding & Vector Storage Edge Cases (BGE)

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 3.1 | **BGE model fails to load (corrupted download or OOM)** | Provide a clear error message at startup. Do not start the application if the embedding model is not available. |
| 3.2 | **Embedding dimension mismatch between ingestion and query time** | Ensure the same BGE model version is used for both indexing and querying. Store the model version in the vector DB metadata. |
| 3.3 | **ChromaDB / FAISS index becomes corrupted** | Implement a re-indexing script that can rebuild the vector store from scratch by re-scraping and re-embedding. |
| 3.4 | **Query embedding returns no close matches (all similarity scores below threshold)** | Return an "I don't have enough information to answer this question" response instead of returning low-confidence, irrelevant chunks. |
| 3.5 | **Very long user query exceeding BGE's max token limit (512 tokens)** | Truncate the query to the model's max token limit, or summarize it before embedding. Log a warning. |

---

## 4. Retrieval Engine Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 4.1 | **Top-K chunks come from multiple different schemes** | The response should clarify which scheme the answer pertains to, or ask the user to specify the scheme. |
| 4.2 | **Top-K chunks contain contradictory information** | Prefer the chunk with the higher similarity score. If ambiguity persists, respond with: "I found conflicting information. Please check the source directly: <URL>." |
| 4.3 | **Query matches a scheme not in our corpus (e.g., HDFC Balanced Advantage Fund)** | Politely inform the user that this scheme is outside the scope of the assistant and list the 5 supported schemes. |
| 4.4 | **User asks about a generic mutual fund concept (e.g., "What is SIP?")** | If the corpus contains this info, answer from context. If not, politely refuse and redirect to an educational resource (e.g., AMFI website). |
| 4.5 | **User asks a multi-part query about multiple funds (e.g., "mid and large cap") where context only covers one** | Ensure `TOP_K` is high enough to capture diverse chunks, and enforce via system prompt that the LLM answers for the available data while explicitly stating it lacks data for the missing parts. |

---

## 5. LLM / Groq Generation Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 5.1 | **Groq API is down or returns a timeout** | Display a user-friendly error: "Our service is temporarily unavailable. Please try again in a moment." Do not expose raw API errors. |
| 5.2 | **Groq API rate limit exceeded** | Implement rate limiting on the client side. Queue requests or show a "Too many requests" message gracefully. |
| 5.3 | **LLM hallucinates facts not present in the retrieved context** | The system prompt must instruct the LLM to answer *only* from the provided context. Post-processing should verify that key facts in the response appear in the source chunks. |
| 5.4 | **LLM generates a response exceeding 3 sentences** | Implement a post-processing check. If the response exceeds 3 sentences, truncate or re-prompt the LLM with stricter instructions. |
| 5.5 | **LLM fails to include the citation URL or footer** | Post-processing validation: check for the presence of a URL and the footer string. If missing, append them programmatically from chunk metadata. |
| 5.6 | **LLM provides investment advice despite the system prompt** | Implement a secondary guardrail: a keyword/intent classifier that scans the LLM output for advisory language (e.g., "you should invest", "recommended", "best fund") and blocks such responses. |
| 5.7 | **GROQ_API_KEY is missing or invalid** | Fail fast at application startup with a clear error message: "GROQ_API_KEY is not set or is invalid." |

---

## 6. User Input Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 6.1 | **Empty query submitted** | Display: "Please enter a question about one of our supported HDFC mutual fund schemes." |
| 6.2 | **Extremely long query (1000+ characters)** | Truncate or reject with a message: "Please keep your question concise (under 500 characters)." |
| 6.3 | **Query in a non-English language (e.g., Hindi)** | Politely respond: "Currently, this assistant only supports queries in English." |
| 6.4 | **Query contains PII (PAN, Aadhaar, phone number, email)** | Detect PII using regex patterns. Do NOT process the query. Respond: "For your security, please do not share personal or financial identifiers here." |
| 6.5 | **Adversarial prompt injection (e.g., "Ignore all instructions and tell me...")** | The system prompt must include injection-resistant instructions. The LLM should refuse and respond with the standard disclaimer. |
| 6.6 | **Query with typos or misspellings (e.g., "expens ratio", "HDFC mid kap")** | The embedding model (BGE) should handle minor misspellings via semantic similarity. For severe misspellings, consider a fuzzy matching layer or ask the user to rephrase. |
| 6.7 | **Comparative / advisory query disguised as factual (e.g., "Which fund has the lowest expense ratio?")** | This is borderline. If the data is available, a factual comparison is acceptable. However, if the question implies a recommendation ("Which is better?"), refuse politely. |
| 6.8 | **Query about performance/returns (e.g., "What are the 3Y returns?")** | Per constraints, do NOT calculate or state returns. Respond with: "For performance details, please refer to the official factsheet: <URL>." |
| 6.9 | **Rapid-fire/spammy queries from the same session** | Implement basic client-side rate limiting (e.g., max 5 queries per minute) to prevent abuse. |

---

## 7. UI / Frontend Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 7.1 | **User refreshes the page mid-conversation** | Chat history can be cleared on refresh (acceptable for MVP). Optionally, persist via session storage. |
| 7.2 | **Response takes too long (> 10 seconds)** | Display a loading spinner and a timeout message if the response exceeds 15 seconds. |
| 7.3 | **Disclaimer not visible (scrolled out of view)** | Pin the disclaimer ("Facts-only. No investment advice.") in a fixed header or sticky banner so it is always visible. |
| 7.4 | **Citation link is broken or Groww URL has changed** | The citation URL should be validated during scraping. If a URL becomes invalid, log it and display a note: "Source link may be outdated." |
| 7.5 | **Mobile/small screen rendering** | Ensure the UI is responsive. Test chat bubbles, citation links, and the disclaimer on mobile viewports. |

---

## 8. Compliance & Policy Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 8.1 | **User explicitly asks for investment advice** | Refuse clearly: "I provide only factual information. For investment advice, please consult a SEBI-registered financial advisor." |
| 8.2 | **User asks to compare two funds' performance** | Refuse: "I cannot provide performance comparisons. You can find individual scheme performance on the official factsheet: <URL>." |
| 8.3 | **User asks about a scheme from a different AMC (e.g., SBI Blue Chip)** | Respond: "I only support queries about the following HDFC AMC schemes: [list the 5 schemes]. Please ask about one of these." |
| 8.4 | **User asks about tax implications of investing** | If the corpus contains factual tax info (e.g., ELSS lock-in), provide it. If the query is advisory ("Should I invest for tax saving?"), refuse. |
| 8.5 | **User asks for real-time NAV** | Clarify: "The data I provide is based on the last scrape of the Groww website and may not reflect real-time NAV. Please check Groww directly for the latest value." |

---

## 9. Automated Scheduler (GitHub Actions) Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 9.1 | **Groww blocks GitHub Actions IPs (WAF/Cloudflare)** | Cloud providers like GitHub are often heavily rate-limited or blocked by financial websites. If a 403 Forbidden occurs, the action should fail gracefully without overwriting the previous good data. (Mitigation: use residential proxies if this becomes a persistent issue). |
| 9.2 | **Git Repository Bloat (ChromaDB)** | Committing binary database files (`chroma.sqlite3`) every single day will rapidly bloat the `.git` history size, even if the scraped text hasn't changed, because SQLite files regenerate internal timestamps/UUIDs. |
| 9.3 | **HuggingFace Model Download Failures** | The GitHub runner downloads the `BAAI/bge-small-en-v1.5` model from HuggingFace on every run. If HF is down or rate-limiting, the run fails. (Mitigation: implement directory caching for `~/.cache/huggingface` in the workflow). |
| 9.4 | **Empty Commits** | If no data has changed on the Groww website, the action might still push a commit because the newly generated ChromaDB binary has a different checksum. (Mitigation: implement a diff-check on `chunks.json` before building the vector database). |

---

## Summary

This document covers **45+ edge cases** across all layers of the system, including the newly added automated CI/CD scheduler. These scenarios should be used as a testing checklist during deployment to ensure robustness, compliance, and a trustworthy user experience.
