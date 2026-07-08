from src.rag.chain import get_rag_chain
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
import os

from src.config import BGE_MODEL_NAME, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

PERSIST_DIRECTORY = os.path.join(os.path.dirname(__file__), 'chroma_db')

def debug_query():
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=BGE_MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
        query_instruction="Represent this sentence for searching relevant passages: "
    )
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    
    query = "fund size of mid and large cap"
    results = vectorstore.similarity_search_with_score(query, k=10)
    
    for i, (doc, score) in enumerate(results):
        print(f"--- Rank {i+1} | Score: {score:.4f} ---")
        print(doc.page_content[:200] + "...")
        print()

if __name__ == "__main__":
    debug_query()
