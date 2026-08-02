"""
ingest.py

Purpose:
---------
This script ingests study materials from the `data/` directory,
splits them into manageable chunks, converts them into embeddings,
and stores them in a FAISS vector database for retrieval.

Supported formats:
- .txt
- .md
"""

# ── standard library imports ───────────────────────────────────────
import os
from pathlib import Path

# ── third-party imports ────────────────────────────────────────────
from dotenv import load_dotenv

# document loaders
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

# text splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter

# embeddings
from langchain_huggingface import HuggingFaceEmbeddings

# vector database
from langchain_community.vectorstores import FAISS

# ── environment setup ──────────────────────────────────────────────
load_dotenv()

# ── project paths ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"


# ──────────────────────────────────────────────────────────────────
# 📥 Load documents
# ──────────────────────────────────────────────────────────────────
def load_documents():
    """
    Load supported files (.txt, .md) from the data directory.
    """
    loaders = []

    # Loader for .txt files
    loaders.append(
        DirectoryLoader(
            str(DATA_DIR),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
        )
    )

    # Loader for .md files
    loaders.append(
        DirectoryLoader(
            str(DATA_DIR),
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader,
            show_progress=True,
        )
    )

    documents = []

    # Load documents safely
    for loader in loaders:
        try:
            documents.extend(loader.load())
        except Exception:
            # Skip if no matching files exist
            continue

    # Validation check
    if not documents:
        print("⚠ No documents found in 'data/' directory.")
        print("👉 Add .txt or .md files and run again.")
        raise SystemExit(1)

    print(f"✓ Loaded {len(documents)} document(s)")
    return documents


# ──────────────────────────────────────────────────────────────────
# ✂️ Chunk documents
# ──────────────────────────────────────────────────────────────────
def chunk_documents(documents):
    """
    Split documents into smaller overlapping chunks for better retrieval.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    print(f"✓ Generated {len(chunks)} chunk(s)")
    return chunks


# ──────────────────────────────────────────────────────────────────
# 🧠 Build vector store
# ──────────────────────────────────────────────────────────────────
def build_vectorstore(chunks):
    """
    Convert chunks into embeddings and store them in FAISS.
    """
    print("Generating embeddings...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    print("Creating FAISS index...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    VECTORSTORE_DIR.mkdir(exist_ok=True)
    vectorstore.save_local(str(VECTORSTORE_DIR))

    print(f"Vector store saved at: {VECTORSTORE_DIR}")
    return vectorstore


# ──────────────────────────────────────────────────────────────────
# 🚀 Main pipeline
# ──────────────────────────────────────────────────────────────────
def main():
    print("\nStarting ingestion pipeline...\n")

    documents = load_documents()
    chunks = chunk_documents(documents)
    build_vectorstore(chunks)

    print("\nIngestion complete.")
    print("You can now run: python query.py\n")


# ── entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    main()