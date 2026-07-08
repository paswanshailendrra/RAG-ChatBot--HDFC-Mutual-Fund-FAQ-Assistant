"""
Script to view the stored embeddings and their associated metadata/text in ChromaDB.
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


def view_embeddings():
    print("🔄 Initializing embedding model...")
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=BGE_MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    print(f"📂 Loading ChromaDB from {PERSIST_DIRECTORY}...")
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    # The underlying chromadb collection
    collection = vectorstore._collection
    count = collection.count()
    print(f"\n📊 Total vectors stored in '{CHROMA_COLLECTION_NAME}': {count}")
    
    if count == 0:
        print("No embeddings found.")
        return

    # Fetch a few samples (including embeddings)
    print("\n🔍 Fetching 2 sample chunks with their embeddings...")
    results = collection.get(
        limit=2,
        include=["embeddings", "documents", "metadatas"]
    )
    
    for i in range(len(results['ids'])):
        print("\n" + "-" * 60)
        print(f"🔹 Chunk ID: {results['ids'][i]}")
        print(f"🔹 Scheme Name: {results['metadatas'][i].get('scheme_name', 'N/A')}")
        print(f"🔹 Source URL: {results['metadatas'][i].get('source', 'N/A')}")
        print("-" * 60)
        
        # Print a snippet of the text
        text = results['documents'][i]
        text_snippet = text[:150] + ("..." if len(text) > 150 else "")
        print(f"📝 Text Snippet:\n{text_snippet}\n")
        
        # Print embedding information
        embedding = results['embeddings'][i]
        print(f"🔢 Vector Dimension: {len(embedding)}")
        
        # Print just the first 5 and last 5 values of the vector so it doesn't flood the terminal
        preview = [round(val, 5) for val in embedding[:5]] + ["..."] + [round(val, 5) for val in embedding[-5:]]
        print(f"🔢 Vector Preview: {preview}")


if __name__ == "__main__":
    view_embeddings()
