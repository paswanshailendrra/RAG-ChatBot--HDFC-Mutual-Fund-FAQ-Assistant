# Comprehensive Project Script: HDFC Mutual Fund FAQ Assistant

## 1. Project Overview
The goal of this project was to build an automated, end-to-end Retrieval-Augmented Generation (RAG) chatbot capable of answering factual questions about HDFC Mutual Funds based on real-time data scraped from official sources and Groww. 

### Key Constraints & Requirements:
- Strictly factual responses (No hallucinations).
- Maximum 3 sentences per response.
- Must cite sources/context.
- Must decline questions unrelated to HDFC Mutual Funds.
- Must append a mandatory disclaimer to every answer.

---

## 2. Architecture & Technology Stack
- **Language:** Python 3.9+
- **LLM Provider:** Groq (`llama-3.3-70b-versatile`) for blazing fast, highly capable inference.
- **Embedding Model:** `BAAI/bge-small-en-v1.5` (via `sentence-transformers`) for high-quality, dense vector embeddings.
- **Vector Database:** ChromaDB (local, persistent storage).
- **Scraping Framework:** `requests` & `BeautifulSoup4` with rotating User-Agents.
- **Orchestration:** LangChain (Core & Community).
- **Frontend UI:** Streamlit.
- **CI/CD & Automation:** GitHub Actions (Automated cron-job ingestion).
- **Hosting:** Streamlit Community Cloud.

---

## 3. Step-by-Step Implementation Process

### Phase 1: Data Acquisition (Scraping)
**File:** `src/scraper/scraper.py`
- We built a custom web scraper to fetch HTML data from HDFC AMC and Groww mutual fund pages.
- **Challenge:** Web Application Firewalls (WAFs) blocked our automated requests.
- **Solution:** We implemented randomized `User-Agent` strings and exponential backoff to mimic human browser traffic, successfully bypassing the blocks.
- The scraper extracts the main text content, cleans it of HTML tags, and yields it as raw text.

### Phase 2: Vector Database & Embeddings
**File:** `src/rag/vector_store.py`
- We used `langchain_community.vectorstores.Chroma` to initialize a local database.
- Data chunks were created using `RecursiveCharacterTextSplitter` to ensure semantic completeness.
- **Challenge:** The embedding model couldn't differentiate "mid and large cap" queries properly because the "large cap" fund (Nifty 50) lacked explicit metadata in its text.
- **Solution:** We enriched the text chunks programmatically by injecting the keyword `(Large Cap)` into the Nifty 50 data before embedding it. This aligned the vector space and fixed complex multi-fund queries.

### Phase 3: The RAG Pipeline (LLM Orchestration)
**File:** `src/rag/chain.py`
- We set up `ChatGroq` with `temperature=0.0` to enforce strictly factual, non-creative responses.
- A highly engineered `ChatPromptTemplate` was created to enforce the 3-sentence limit, the mandatory disclaimer, and the refusal to answer out-of-domain questions.
- **Challenge:** Streamlit's dynamic reloader and Cloud package installer crashed repeatedly when attempting to use complex LangChain modules (like `MultiQueryRetriever`). 
- **Solution:** We adopted a robust, native retrieval strategy using the `base_retriever` with `TOP_K=6`. This successfully pulled in diverse context without requiring toxic, buggy dependencies.

### Phase 4: Frontend Development
**File:** `src/ui/app.py`
- We built a sleek, minimal chat interface using Streamlit (`st.chat_input`, `st.chat_message`).
- We utilized `@st.cache_resource` to load the heavy AI models only once per session, drastically speeding up response times.
- **Challenge:** Streamlit Cloud's Secret Management was highly buggy, failing to pass environment variables down to the LLM during initialization.
- **Solution:** We implemented a custom "⚙️ Configuration" sidebar. This allowed the user to paste their Groq API Key directly into the web browser, completely bypassing the cloud's broken secret management and guaranteeing instant initialization.

### Phase 5: CI/CD Pipeline (Automated Ingestion)
**File:** `.github/workflows/ingestion.yml`
- We needed the chatbot to always have the latest NAV and fund data without manual intervention.
- We wrote a GitHub Action script that triggers every day (`cron: '0 0 * * *'`) and on every `push`.
- **Workflow Steps:**
  1. Spins up an Ubuntu runner and installs Python.
  2. Restores HuggingFace model weights from cache to save download time.
  3. Runs `python src/rag/vector_store.py` to scrape fresh data and rebuild the ChromaDB locally.
  4. Uses `git diff` to check if the database actually changed.
  5. If new data is found, it automatically commits the new `chroma.sqlite3` file and pushes it to the `main` branch.

### Phase 6: Cloud Deployment Troubleshooting
Deploying to Streamlit Community Cloud required solving four massive technical hurdles:
1. **PyTorch OOM Freeze:** The default PyTorch library is 800MB. Loading it maxed out Streamlit's 1GB RAM limit, freezing the app for 10+ minutes. We fixed this by forcing `pip` to install the CPU-only version in `requirements.txt`, dropping the size to 150MB.
2. **SQLite Incompatibility:** Older Linux containers crashed ChromaDB. We tried the `pysqlite3-binary` hot-swap, but the specific wheel was missing for Streamlit's OS, causing fatal pip crashes. We removed it entirely and relied on native SQLite.
3. **Langchain Pip Corruption:** Streamlit's installer corrupted the `langchain` package installation when encountering complex sub-modules like `MultiQueryRetriever`. We bypassed this completely by falling back to the native `base_retriever` (with `TOP_K=6`) and completely removing the toxic `langchain.retrievers` package from our codebase.
4. **API Key Sleep State Wipe:** Streamlit puts idle apps to sleep. When woken, our temporary sidebar API key was wiped, requiring the user to re-enter it. We permanently fixed this by instructing the user to bake the key into Streamlit Cloud's "Secrets" dashboard (`st.secrets`) and updated the UI code to magically hide the sidebar when the key is detected, making the app publicly shareable without friction.

---

## 4. How to Run the Project Locally
1. Clone the repository: `git clone <repo_url>`
2. Create virtual environment: `python3 -m venv venv && source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set your API Key: Create a `.env` file and add `GROQ_API_KEY=gsk_your_key`
5. Run the vector store builder: `python src/rag/vector_store.py`
6. Start the UI: `streamlit run src/ui/app.py`

## 5. How to Deploy (Streamlit Cloud)
1. Go to `share.streamlit.io`.
2. Connect your GitHub repository.
3. Set the **Main file path** to `src/ui/app.py`.
4. Click Deploy. 
5. Wait for the initial build (takes ~3 minutes to download models).
6. Enter your Groq API key in the UI sidebar.
