"""
query.py — Interactive Q&A over your notes using RAG.
Loads the FAISS vector store, retrieves relevant chunks,
and sends them + your question to Groq (Llama 3.3).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

load_dotenv()

# ── paths ──────────────────────────────────────────────────────────
VECTORSTORE_DIR = Path(__file__).parent / "vectorstore"

# ── prompt template ────────────────────────────────────────────────
RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""\
Use the following context from the user's personal notes to answer the question.
If the answer is not in the context, say "I don't have that in my notes."

Context:
{context}

Question: {question}

Answer:""",
)

# ── build chain ────────────────────────────────────────────────────
def get_chain():
    """Load vectorstore and wire up the RAG chain."""
    if not VECTORSTORE_DIR.exists():
        print("⚠  No vector store found. Run  python ingest.py  first.")
        raise SystemExit(1)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": RAG_PROMPT},
        return_source_documents=True,
    )
    return chain


# ── interactive loop ───────────────────────────────────────────────
if __name__ == "__main__":
    chain = get_chain()
    print("🔍 RAG Vault — ask anything about your notes  (type 'quit' to exit)\n")

    while True:
        question = input("You: ").strip()
        if not question or question.lower() in ("quit", "exit", "q"):
            print("👋 Bye!")
            break

        result = chain.invoke({"query": question})
        print(f"\nAnswer: {result['result']}\n")

        # Show source snippets
        sources = result.get("source_documents", [])
        if sources:
            print("── sources ──")
            for i, doc in enumerate(sources, 1):
                src = doc.metadata.get("source", "unknown")
                snippet = doc.page_content[:120].replace("\n", " ")
                print(f"  [{i}] {src}  →  {snippet}…")
            print()
