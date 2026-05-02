import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
from chromadb.config import Settings
import requests
from dotenv import load_dotenv

from utils.embeddings import get_embeddings

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ✅ Free model on OpenRouter — no billing needed
MODEL = "openrouter/free"


# -----------------------------
# Load ChromaDB (matches ingest)
# -----------------------------
def load_collection():
    # ✅ Use PersistentClient — new ChromaDB API
    client = chromadb.PersistentClient(path="vectorstore/chroma")
    collection = client.get_or_create_collection(name="rag_collection")
    return collection


# -----------------------------
# Retrieval from ChromaDB
# -----------------------------
def retrieve(query, n_results=4):
    collection = load_collection()

    # Check if collection has any data
    count = collection.count()
    if count == 0:
        print("❌ Vector DB is empty! Run ingest_chroma.py first.")
        return []

    print(f"✅ Found {count} chunks in DB. Retrieving top {n_results}...")

    query_embedding = get_embeddings([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, count)   # can't retrieve more than what exists
    )

    chunks = results["documents"][0]  # list of matched text chunks
    return chunks


# -----------------------------
# LLM via OpenRouter API
# -----------------------------
def generate_answer(context, question):
    if not OPENROUTER_API_KEY:
        return "❌ OPENROUTER_API_KEY not set in .env file!"

    prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context.
If the answer is not in the context, say "I don't have enough information to answer this."
Do NOT make up information.

Context:
{context}

Question: {question}

Answer:"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",   # required by OpenRouter
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.HTTPError as e:
        return f"❌ API Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


# -----------------------------
# Main ask function
# -----------------------------
def ask(query):
    print(f"\n🔍 Retrieving context for: '{query}'")
    chunks = retrieve(query)

    if not chunks:
        return "❌ Could not retrieve any context. Make sure you've run ingest_chroma.py first."

    context = "\n\n---\n\n".join(chunks)
    print(f"📄 Using {len(chunks)} chunks as context.")

    print("🤖 Generating answer...")
    return generate_answer(context, query)


# -----------------------------
# CLI Test
# -----------------------------
if __name__ == "__main__":
    print("🧠 RAG QnA Bot — type 'quit' to exit\n")
    while True:
        q = input("Ask: ").strip()
        if q.lower() in ("quit", "exit", "q"):
            break
        if not q:
            continue
        answer = ask(q)
        print(f"\nAnswer:\n{answer}\n")
        print("-" * 60)