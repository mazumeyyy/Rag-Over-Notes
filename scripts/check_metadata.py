"""
check_metadata.py

Read-only diagnostic: load documents, inspect metadata, and report
any gaps — without building the FAISS index.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `import ingest` works
# regardless of where the script is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingest import load_documents

REQUIRED_KEYS = ("semester", "subject", "chapter")


def main():
    documents = load_documents()

    # ── 1. First 3 documents' full metadata ───────────────────────
    print("=" * 60)
    print("METADATA FOR FIRST 3 DOCUMENTS")
    print("=" * 60)
    for i, doc in enumerate(documents[:3]):
        print(f"\n[Doc {i + 1}]  source: {doc.metadata.get('source', '?')}")
        for key, value in sorted(doc.metadata.items()):
            print(f"  {key}: {value!r}")

    # ── 2. Unique (semester, subject, chapter) combinations ───────
    combos = set()
    for doc in documents:
        combo = (
            doc.metadata.get("semester"),
            doc.metadata.get("subject"),
            doc.metadata.get("chapter"),
        )
        combos.add(combo)

    print("\n" + "=" * 60)
    print(f"UNIQUE (semester, subject, chapter) COMBINATIONS  [{len(combos)} total]")
    print("=" * 60)
    for sem, subj, chap in sorted(combos, key=lambda c: (c[0] or 0, c[1] or "", c[2] or "")):
        print(f"  semester={sem}  subject={subj!r}  chapter={chap!r}")

    # ── 3. Warnings for missing metadata ──────────────────────────
    warnings = []
    for i, doc in enumerate(documents):
        missing = [k for k in REQUIRED_KEYS if not doc.metadata.get(k)]
        if missing:
            src = doc.metadata.get("source", "<unknown>")
            warnings.append((i, src, missing))

    print("\n" + "=" * 60)
    if warnings:
        print(f"⚠  DOCUMENTS WITH MISSING METADATA  [{len(warnings)} issue(s)]")
        print("=" * 60)
        for idx, src, missing in warnings:
            print(f"  Doc {idx}: missing {', '.join(missing)}")
            print(f"           source: {src}")
    else:
        print("✓  All documents have semester, subject, and chapter metadata.")
        print("=" * 60)


if __name__ == "__main__":
    main()
