"""
Configuration and constants for the Mutual Fund FAQ Assistant.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ======================
# Groq Configuration
# ======================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Fallback for Streamlit Community Cloud secrets
if not GROQ_API_KEY:
    try:
        import streamlit as st
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

GROQ_MODEL = "llama-3.3-70b-versatile"  # Default Groq model

# ======================
# BGE Embedding Model
# ======================
BGE_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384

# ======================
# ChromaDB Configuration
# ======================
CHROMA_PERSIST_DIR = "chroma_db"
CHROMA_COLLECTION_NAME = "hdfc_mutual_funds"

# ======================
# Chunking Configuration
# ======================
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# ======================
# Retrieval Configuration
# ======================
TOP_K = 6

# ======================
# Groww URLs (Corpus)
# ======================
GROWW_URLS = [
    {
        "url": "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
        "scheme_name": "HDFC Silver ETF FOF Direct Growth",
    },
    {
        "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "scheme_name": "HDFC Mid-Cap Fund Direct Growth",
    },
    {
        "url": "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
        "scheme_name": "HDFC Defence Fund Direct Growth",
    },
    {
        "url": "https://groww.in/mutual-funds/hdfc-nifty-50-index-fund-direct-growth",
        "scheme_name": "HDFC Nifty 50 Index Fund Direct Growth",
    },
    {
        "url": "https://groww.in/mutual-funds/hdfc-dividend-yield-fund-direct-growth",
        "scheme_name": "HDFC Dividend Yield Fund Direct Growth",
    },
]

# ======================
# Disclaimer
# ======================
DISCLAIMER = "Facts-only. No investment advice."
