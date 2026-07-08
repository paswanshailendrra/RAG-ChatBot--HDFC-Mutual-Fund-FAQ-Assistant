from src.rag.chain import get_rag_chain, ask_question
import sys

def main():
    chain = get_rag_chain()
    query = "fund size of mid and large cap"
    print(f"\n💬 Querying: '{query}'")
    answer = ask_question(query, chain)
    print("🤖 Response:")
    print(answer)

if __name__ == "__main__":
    main()
