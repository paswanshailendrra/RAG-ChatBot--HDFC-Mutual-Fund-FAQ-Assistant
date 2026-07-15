# 📈 HDFC Mutual Fund FAQ Assistant (RAG Chatbot)

An intelligent, fully-automated Retrieval-Augmented Generation (RAG) chatbot designed to answer factual questions about HDFC Mutual Funds. It scrapes real-time NAV and fund data from Groww, builds a local vector database, and uses the ultra-fast Groq API (LLaMA-3.3-70b) to provide precise, 3-sentence answers with citations.

---

## 🌟 Key Features
- **Real-Time Automated Data Ingestion:** A GitHub Actions cron job runs daily to automatically bypass Cloudflare WAF, scrape fresh NAV data, rebuild the vector database, and push the updates back to the repository.
- **Strictly Factual & Compliant:** Enforced through rigorous system prompting to decline out-of-domain questions, never offer investment advice, and adhere to a strict 3-sentence maximum.
- **Enriched Vector Embeddings:** Dynamically injects domain knowledge (e.g., tagging the Nifty 50 fund as "Large Cap" in the raw text before embedding) to solve complex semantic multi-query edge cases.
- **Seamless Cloud Deployment:** Configured to run blazingly fast on Streamlit Community Cloud with a custom CPU-only PyTorch implementation to prevent out-of-memory errors.

---

## 🏗️ Architecture & Design

This project is built using a modern, scalable AI stack:

1. **Scraping Engine (`cloudscraper` + `BeautifulSoup4`)**
   - Automatically visits Groww mutual fund pages.
   - Bypasses Cloudflare CDN caching and WAF bot-protection using TLS fingerprinting and cache-busting timestamps to guarantee fresh data extraction.
2. **Text Processing & Chunking (`LangChain`)**
   - Cleans the raw HTML and splits the data into semantically meaningful overlapping chunks.
   - Attaches strict metadata (source URLs, fund names, timestamps) to every chunk.
3. **Embeddings & Vector Store (`BAAI/bge-small-en-v1.5` + `ChromaDB`)**
   - Chunks are embedded locally using the high-performance BGE model.
   - Stored in a lightweight, persistent SQLite-backed ChromaDB.
4. **LLM Orchestration (`Groq` + `LLaMA-3.3-70b-versatile`)**
   - Uses `langchain-core` to retrieve the Top-K most relevant chunks using cosine similarity.
   - Formats a highly engineered prompt and streams the response back via Streamlit.
5. **Frontend (`Streamlit`)**
   - A clean, minimal chat interface.
   - Models are cached securely in memory to ensure sub-second response times on subsequent queries.

---

## 🛠️ Major Troubleshooting & Mitigations

Building this system required overcoming several massive cloud deployment hurdles:

- **PyTorch OOM Freeze on Streamlit Cloud:** The default PyTorch dependency (800MB) completely exhausted Streamlit's 1GB RAM limit, causing the app to freeze endlessly during deployment. 
  - *Fix:* Forced `pip` to install the CPU-only version of torch (`torch==2.0.1+cpu`) via `requirements.txt`, slashing the footprint to 150MB.
- **LangChain Dynamic Import Corruption:** Streamlit's hot-reloader aggressively corrupted the installation of complex LangChain modules like `MultiQueryRetriever`, throwing persistent `ModuleNotFound` errors in production.
  - *Fix:* We surgically removed toxic sub-dependencies from the codebase and fell back to the native `base_retriever` combined with enriched chunk metadata (injecting domain knowledge directly into the vector space).
- **GitHub Actions Scheduler Staleness:** Cloudflare recognized the GitHub Actions runner as a bot and served it a permanently cached, stale HTML file without updating the NAV.
  - *Fix:* Integrated `cloudscraper` and appended dynamic cache-busting query parameters to force the edge servers to fetch the absolute latest page data every single morning.

---

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/paswanshailendrra/RAG-ChatBot--HDFC-Mutual-Fund-FAQ-Assistant.git
cd RAG-ChatBot--HDFC-Mutual-Fund-FAQ-Assistant
```

### 2. Set up the Environment
Create a virtual environment and install the required dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure API Keys
Copy the example environment file and insert your free Groq API key:
```bash
cp .env.example .env
# Edit .env and add GROQ_API_KEY=gsk_your_key_here
```

### 4. Build the Vector Database (Optional)
The repository already contains the latest `chroma_db`, but you can rebuild it manually to scrape the newest data immediately:
```bash
python src/scraper/scraper.py
python src/scraper/chunker.py
python src/embeddings/vector_store.py
```

### 5. Launch the Chatbot
```bash
streamlit run src/ui/app.py
```

Enjoy exploring your factual, lightning-fast Mutual Fund AI Assistant!
