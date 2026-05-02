from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from query import ask

app = FastAPI(title="RAG QnA Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ask")
def ask_question(q: str):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    answer = ask(q)
    return {"question": q, "answer": answer}


@app.get("/health")
def health():
    return {"status": "ok"}