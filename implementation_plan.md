# Phase-Wise Implementation Plan: Mutual Fund FAQ Assistant

Provide a structured, step-by-step roadmap for building the facts-only RAG chatbot for HDFC mutual fund schemes based on the provided problem statement and architecture documents.

## User Review Required

> [!IMPORTANT]
> Please review this implementation plan. Specifically, confirm if you have your Groq API key ready and if you have a preference for the UI framework (Streamlit vs Gradio). Once approved, we will begin execution.

## Proposed Changes

### Phase 1: Project Setup and Dependencies
- Initialize the Python virtual environment.
- Install the required dependencies: `langchain`, `beautifulsoup4`, `chromadb` (or FAISS), `groq`, and `sentence-transformers` (for BAAI/BGE).
- Set up the environment variables (`GROQ_API_KEY`).

### Phase 2: Data Ingestion (Web Scraping)

#### Phase 2a: Scraping
- Develop a Python scraping script targeting the 5 specific Groww mutual fund URLs.
- Use `requests` (or `Playwright` as fallback for JS-rendered content) to fetch raw HTML from each URL.
- Store the raw HTML responses locally for reproducibility and debugging.

#### Phase 2b: Cleaning / Parsing
- Implement HTML parsing logic using `beautifulsoup4` to extract only the core text content.
- Strip out irrelevant elements: navbars, footers, ads, sidebars, and promotional banners.
- Preserve financial symbols (₹, %, ₹Cr) and tabular data structure.
- Attach metadata (source URL, scheme name, scrape timestamp) to each cleaned text block.

#### Phase 2c: Chunking
- Process the cleaned data block-by-block (segmented by `--- Block X ---`).
- Apply `RecursiveCharacterTextSplitter` (chunk size 500, overlap 100) to each block individually.
- For tabular data blocks (e.g., Holdings), rely on newline (`\n`) separators so that rows are kept relatively intact during splitting.
- Attach `source_url` and `scheme_name` metadata to every resulting chunk.
- Save the resulting chunks (with their metadata) locally to prepare for the ChromaDB ingestion in Phase 3.

### Phase 3: Embedding and Vector Storage (BGE)
- Initialize the local BAAI/BGE embedding model (`BAAI/bge-small-en-v1.5`) via `langchain_huggingface.HuggingFaceEmbeddings` (or `HuggingFaceBgeEmbeddings`).
- Set up a persistent local ChromaDB instance (`chroma_db` directory) to store the vector embeddings.
- **Embedding Strategy for Chunks**: 
  - Load the 259 chunks from `data/chunks.json`.
  - Prepend the `scheme_name` to each chunk's text prior to vectorization (e.g., `"Scheme: HDFC Mid-Cap Fund...\n[Chunk Text]"`) to ensure dense vectors are strongly clustered by their mutual fund context.
  - For queries (Phase 4), use BGE's recommended query instruction prefix if necessary.
- Store the enriched embeddings alongside the original text chunks and their metadata (`source`, `scheme_name`) into a single ChromaDB collection (`hdfc_mutual_funds`).

### Phase 4: LLM Integration and RAG Chain (Groq)
- Integrate the Groq API client to utilize a fast LLM (`llama-3.3-70b-versatile` via `langchain_groq.ChatGroq`).
- **Rate Limit Management**: Account for Groq's limits (30 RPM, 12K TPM, 100K TPD):
  - Configure `ChatGroq` with `max_retries` (exponential backoff) to handle 429 errors gracefully.
  - Set `TOP_K = 6` to ensure enough diverse chunks are retrieved to answer multi-part questions (e.g. asking about two funds at once), which consumes ~720 tokens per request—safely keeping total context under the 12K TPM limit.
- **Retrieval Strategy**: 
  - Initialize the `Chroma` retriever utilizing the `HuggingFaceBgeEmbeddings` with the mandatory query instruction: `"Represent this sentence for searching relevant passages: "`.
  - Fetch the `Top-K = 6` chunks based on Cosine Similarity.
- Construct a robust system prompt enforcing the "facts-only" constraint, the 3-sentence limit, and the mandatory footer (`"Last updated from sources: <date>"`).
- Build the RAG pipeline combining the context chunks, the user's query, and the LLM.

### Phase 5: User Interface (Minimal)
- Build a lightweight web UI using Streamlit (or Gradio).
- Implement the welcome message and visible disclaimer: *"Facts-only. No investment advice."*
- Add the 3 example quick-start questions.
- Display the chat interface handling user inputs and rendering the formatted responses with the required footer.

### Phase 6: Scheduler Component (Automated Ingestion)
- Develop a GitHub Actions workflow (`.github/workflows/ingestion.yml`) to serve as the scheduler.
- Configure a `cron` trigger to run automatically every day at a specific time (e.g., midnight UTC).
- The workflow should check out the code, set up Python, install dependencies, and run the Data Ingestion pipeline scripts.
- Automatically commit and push the updated `data/` and `chroma_db/` directories back to the repository to ensure data freshness.

## Verification Plan

### Automated Tests
- N/A (We will rely primarily on manual functional testing of the RAG responses).

### Manual Verification
- Test factual queries (e.g., "What is the expense ratio for HDFC Mid-Cap Fund?") and verify accurate retrieval from the vector database.
- Ensure responses are limited to a maximum of 3 sentences and contain exactly one Groww URL citation.
- Ensure the footer *“Last updated from sources: <date>”* is present on all responses.
- Test advisory queries (e.g., "Which HDFC fund is best for me?") and verify that the system politely refuses and provides an educational link.
