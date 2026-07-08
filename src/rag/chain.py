"""
Phase 4: LLM Integration and RAG Chain (Groq)

Implements the Retrieval-Augmented Generation pipeline using LangChain,
Groq (Llama-3), and the ChromaDB vector store.
"""
import os
import warnings
from datetime import datetime
from typing import Dict, Any

# Suppress HuggingFace warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=FutureWarning)

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers.multi_query import MultiQueryRetriever

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import (
    GROQ_API_KEY, GROQ_MODEL, BGE_MODEL_NAME, 
    CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, TOP_K, DISCLAIMER
)

PERSIST_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', '..', CHROMA_PERSIST_DIR)


# ==========================================
# 1. System Prompt Definition
# ==========================================
SYSTEM_PROMPT = """You are a highly strictly factual Mutual Fund FAQ Assistant for HDFC Asset Management Company.
Your sole purpose is to provide objective, factual information about specific mutual funds based EXCLUSIVELY on the provided context.

RULES AND CONSTRAINTS:
1. FACTS ONLY: Answer using ONLY the information found in the `<context>`. If the context does not contain the answer, say "I don't have enough information to answer that based on the provided sources."
2. NO ADVICE: You must strictly refuse to answer any advisory or predictive queries (e.g., "Should I invest?", "Is this a good fund?", "Will it go up?"). Respond with: "I am a facts-only assistant and cannot provide investment advice."
3. LENGTH LIMIT: Your response MUST NOT exceed 3 sentences. Be extremely concise.
4. CITATION: If you use the context, you must cite the source URL at the end of your text response.
5. FOOTER: The very last line of your entire response MUST be exactly: "Last updated from sources: {date}"
6. NO MARKDOWN TABLES: Present data in readable sentences, not markdown tables.
7. DOMAIN KNOWLEDGE: If the user asks about a "Large Cap" fund, they are referring to the "HDFC Nifty 50 Index Fund".

<context>
{context}
</context>
"""

# ==========================================
# 2. RAG Pipeline Initialization
# ==========================================

def get_rag_chain(api_key=None):
    """Initializes and returns the complete RAG chain."""
    
    # Fetch API Key dynamically
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("GROQ_API_KEY")
            except Exception:
                pass
            
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please check your .env file or Streamlit secrets.")

    # 1. Setup Retriever
    print("🔄 Initializing Embedding Model & Retriever...")
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
    
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    # 2. Setup LLM
    print(f"🧠 Initializing LLM ({GROQ_MODEL})...")
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=GROQ_MODEL,
        temperature=0.0,  # Zero temperature for strictly factual responses
        max_tokens=256,
        max_retries=3  # Exponential backoff for Groq rate limits
    )
    
    # Wrap with MultiQueryRetriever to solve the "mid and large cap" bias issue
    print("🔍 Setting up MultiQueryRetriever...")
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever, 
        llm=llm
    )

    # 3. Setup Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}")
    ])

    # 4. Format Context Function
    def format_docs(docs):
        """Format retrieved documents and collect their source URLs."""
        formatted_chunks = []
        sources = set()
        
        for i, doc in enumerate(docs, 1):
            formatted_chunks.append(f"[Document {i}]:\n{doc.page_content}")
            if doc.metadata.get("source"):
                sources.add(doc.metadata.get("source"))
                
        # Append source URLs to the context block so the LLM knows what to cite
        sources_text = "\n\nAvailable Source URLs:\n" + "\n".join(sources)
        return "\n\n".join(formatted_chunks) + sources_text

    # 5. Build Chain
    print("⛓️ Building RAG Chain...")
    
    # We inject the current date into the prompt dynamically during invocation
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough(), "date": lambda _: datetime.now().strftime("%Y-%m-%d")}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain


# ==========================================
# 3. Query Execution Function
# ==========================================
def ask_question(query: str, chain=None) -> str:
    """Execute a query against the RAG pipeline."""
    if chain is None:
        chain = get_rag_chain()
        
    print(f"\n💬 Querying: '{query}'")
    response = chain.invoke(query)
    return response


if __name__ == "__main__":
    # Test the pipeline
    test_queries = [
        "What is the expense ratio of HDFC Mid-Cap Fund?",
        "Should I invest in HDFC Defence Fund right now?"
    ]
    
    chain = get_rag_chain()
    
    for q in test_queries:
        print("\n" + "="*50)
        answer = ask_question(q, chain)
        print("🤖 Response:")
        print(answer)
        print("="*50)
