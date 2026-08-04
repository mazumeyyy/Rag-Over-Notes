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
- .pdf
"""

# ── standard library imports ───────────────────────────────────────
import re
from collections import Counter
from pathlib import Path

# ── third-party imports ────────────────────────────────────────────
from dotenv import load_dotenv

# document loaders
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyMuPDFLoader,
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


# ── helpers ────────────────────────────────────────────────────────
def _extract_metadata_from_path(file_path: str) -> dict:
    """
    Derive semester, subject, and chapter from the file's location
    inside the data/ directory.

    Expected layouts:
      data/semester_N/<CourseCode>_<Subject>/Unit X-<Title>/file.ext
      data/semester_N/Elective_I/<CourseCode>_<Subject>/Unit X-<Title>/file.ext
    """
    path = Path(file_path)

    # Get the parts relative to data/
    try:
        rel = path.relative_to(DATA_DIR)
    except ValueError:
        return {}

    parts = rel.parts  # e.g. ("semester_3", "CSC211_Data_...", "Unit 1-...", "file.pdf")

    metadata: dict = {}

    # ── Semester ──────────────────────────────────────────────────
    if parts and parts[0].startswith("semester_"):
        try:
            metadata["semester"] = int(parts[0].split("_")[1])
        except (IndexError, ValueError):
            pass

    # ── Subject & Chapter ─────────────────────────────────────────
    # Determine the offset: if there's an "Elective_*" folder, subject
    # and unit are one level deeper.
    offset = 1  # default: subject folder is right under semester_N
    if len(parts) > 1 and parts[1].lower().startswith("elective"):
        offset = 2

    # Subject
    if len(parts) > offset:
        subject_folder = parts[offset]
        # Strip leading course code (e.g. "CSC115_") and convert underscores
        subject_name = re.sub(r"^[A-Z]{2,4}\d+_", "", subject_folder)
        metadata["subject"] = subject_name.replace("_", " ")

    # Chapter / Unit
    if len(parts) > offset + 1:
        unit_folder = parts[offset + 1]
        # e.g. "Unit 3-Input and Output" or "Unit 5-Dynamic Programming (8)"
        m = re.match(r"Unit\s+(\d+)\s*-\s*(.+)", unit_folder)
        if m:
            metadata["chapter"] = f"Unit {m.group(1)} - {m.group(2).strip()}"
        else:
            metadata["chapter"] = unit_folder

    return metadata


# ──────────────────────────────────────────────────────────────────
# 📥 Load documents
# ──────────────────────────────────────────────────────────────────
def load_documents():
    """
    Load supported files (.txt, .md, .pdf) from the data directory,
    attach semester / subject / chapter metadata derived from the
    folder structure, and print a per-subject summary.
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

    # Loader for .md files (using TextLoader instead of UnstructuredMarkdownLoader)
    loaders.append(
        DirectoryLoader(
            str(DATA_DIR),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
        )
    )

    # Loader for .pdf files
    loaders.append(
        DirectoryLoader(
            str(DATA_DIR),
            glob="**/*.pdf",
            loader_cls=PyMuPDFLoader,
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
        print("No documents found in 'data/' directory.")
        print("Add .txt, .md, or .pdf files and run again.")
        raise SystemExit(1)

    # ── Attach metadata from folder hierarchy ─────────────────────
    for doc in documents:
        source = doc.metadata.get("source", "")
        path_meta = _extract_metadata_from_path(source)
        doc.metadata.update(path_meta)

    # ── Print summary ─────────────────────────────────────────────
    subject_counts = Counter(
        doc.metadata.get("subject", "unknown") for doc in documents
    )
    print(f"\n Loaded {len(documents)} document(s) total")
    print("  Documents per subject:")
    for subject, count in sorted(subject_counts.items()):
        print(f"    • {subject}: {count}")
    print()

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