import faiss
import numpy as np
import os
import pickle

from utils.pdf_loader import load_pdf
from utils.chunker import chunk_text
from utils.embeddings import get_embeddings

def ingest(pdf_path):
    text = load_pdf(pdf_path)
    chunks = chunk_text(text)

    embeddings = get_embeddings(chunks)
    dim = len(embeddings[0])

    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    os.makedirs("vectorstore", exist_ok=True)

    faiss.write_index(index, "vectorstore/faiss.index")

    with open("vectorstore/chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    print("Ingestion complete!")

if __name__ == "__main__":
    ingest("data/sample.pdf")