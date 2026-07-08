"""
Test retrieval from ChromaDB to ensure embeddings are working correctly.
"""
import os
import warnings

# Suppress HuggingFace warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=FutureWarning)

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import BGE_MODEL_NAME, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

PERSIST_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', '..', CHROMA_PERSIST_DIR)

def test_retrieval():
    print("🔄 Initializing embedding model...")
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=BGE_MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
        query_instruction="Represent this sentence for searching relevant passages: "
    )

    print(f"📂 Loading ChromaDB...")
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    query = "What is the expense ratio of HDFC Mid-Cap Fund?"
    print(f"\n🔍 Querying Vector Database:\n   '{query}'\n")
    
    # Perform similarity search
    results = vectorstore.similarity_search_with_score(query, k=1)
    
    if not results:
        print("❌ No results found!")
        return

    doc, score = results[0]
    print("✅ Best Matching Result (Score: {:.4f}):".format(score))
    print("-" * 60)
    print(f"🔹 Scheme Name: {doc.metadata.get('scheme_name')}")
    print(f"🔹 Source URL: {doc.metadata.get('source')}")
    print("-" * 60)
    print(f"{doc.page_content}")
    print("-" * 60)


if __name__ == "__main__":
    test_retrieval()
