"""
Phase 3: Embedding and Vector Storage (BGE)

Initializes the local BAAI/BGE embedding model, sets up ChromaDB, 
and ingests all chunks from Phase 2 into a persistent vector store.
"""
import os
import json
from typing import List, Dict
import warnings

# Suppress HuggingFace warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=FutureWarning)

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import BGE_MODEL_NAME, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

# Paths
CHUNKS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'chunks.json')
PERSIST_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', '..', CHROMA_PERSIST_DIR)


def get_embedding_model() -> HuggingFaceBgeEmbeddings:
    """Initialize and return the BGE embedding model."""
    print(f"🔄 Initializing embedding model: {BGE_MODEL_NAME}")
    
    # BGE parameters
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True} # set True to compute cosine similarity
    
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=BGE_MODEL_NAME,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
        # BGE requires specific instruction for queries, but for documents we just encode them directly.
        # Langchain handles this internally if configured, or we pass it via query_instruction.
        query_instruction="Represent this sentence for searching relevant passages: "
    )
    print("✅ Model initialized successfully")
    return embeddings


def load_chunks() -> List[Dict]:
    """Load chunks from the JSON file."""
    if not os.path.exists(CHUNKS_FILE):
        raise FileNotFoundError(f"Chunks file not found at {CHUNKS_FILE}")
        
    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    print(f"📄 Loaded {len(chunks)} chunks from {CHUNKS_FILE}")
    return chunks


def prepare_documents(chunks: List[Dict]) -> List[Document]:
    """
    Convert chunk dictionaries to LangChain Document objects.
    Implements the strategy: prepends scheme_name to the text to ensure 
    dense vectors are tightly clustered.
    """
    documents = []
    
    for chunk in chunks:
        scheme_name = chunk.get("metadata", {}).get("scheme_name", "")
        original_text = chunk.get("text", "")
        
        # Inject domain knowledge directly into the embedding text
        display_name = scheme_name
        if "Nifty 50" in display_name:
            display_name += " (Large Cap)"
            
        # Prepend scheme name for better dense retrieval clustering
        enriched_text = f"Scheme: {display_name}\n{original_text}"
        
        doc = Document(
            page_content=enriched_text,
            metadata=chunk.get("metadata", {})
        )
        documents.append(doc)
        
    return documents


def build_vector_store():
    """Build and populate the ChromaDB vector store."""
    print("=" * 60)
    print("🗄️ Starting Vector Store Population")
    print("=" * 60)
    
    # 1. Load Chunks
    chunks = load_chunks()
    
    # 2. Prepare Documents (Enrich with metadata)
    documents = prepare_documents(chunks)
    print(f"📝 Prepared {len(documents)} LangChain Document objects")
    
    # 3. Initialize Embedding Model
    embedding_model = get_embedding_model()
    
    # 4. Create/Update ChromaDB
    print(f"💾 Ingesting documents into ChromaDB (Collection: {CHROMA_COLLECTION_NAME})...")
    
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=PERSIST_DIRECTORY
    )
    
    print("\n" + "=" * 60)
    print(f"🎉 Vector Store successfully built at: {PERSIST_DIRECTORY}")
    print(f"   Total vectors stored: {vectorstore._collection.count()}")
    print("=" * 60)


if __name__ == "__main__":
    build_vector_store()
