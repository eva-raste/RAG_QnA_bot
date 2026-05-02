import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb   # ✅ PersistentClient — new API, no deprecated Settings needed

from utils.pdf_loader import load_pdf
from utils.chunker import chunk_text
from utils.embeddings import get_embeddings


def ingest(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return

    # ✅ PersistentClient is the correct API for ChromaDB >= 0.4.0
    os.makedirs("vectorstore/chroma", exist_ok=True)
    client = chromadb.PersistentClient(path="vectorstore/chroma")

    # ✅ Delete old collection to avoid duplicate chunk IDs on re-ingestion
    try:
        client.delete_collection(name="rag_collection")
        print("🗑️  Cleared old collection.")
    except Exception:
        pass  # Collection didn't exist yet, that's fine

    collection = client.get_or_create_collection(name="rag_collection")

    print("📄 Loading PDF...")
    text = load_pdf(pdf_path)

    if not text.strip():
        print("❌ No text extracted from PDF. It may be scanned/image-based.")
        return

    print(f"✅ Extracted {len(text)} characters from PDF.")

    print("✂️  Chunking text...")
    chunks = chunk_text(text)

    if not chunks:
        print("❌ No chunks created.")
        return

    print(f"✅ Created {len(chunks)} chunks.")

    print("🔢 Generating embeddings...")
    embeddings = get_embeddings(chunks)

    ids = [f"chunk_{i}" for i in range(len(chunks))]

    print("💾 Storing in ChromaDB...")
    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        ids=ids
    )

    print(f"✅ Ingestion complete! {len(chunks)} chunks stored in vectorstore/chroma")


if __name__ == "__main__":
    ingest("data/sample.pdf")