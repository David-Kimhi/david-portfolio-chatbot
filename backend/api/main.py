from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from chromadb import Client
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

app = FastAPI(title="PortfolioChat API")
embed = SentenceTransformer("all-MiniLM-L6-v2")
chroma = Client(Settings(anonymized_telemetry=False))
coll = chroma.get_or_create_collection("portfolio_docs")

class IngestItem(BaseModel):
    id: str
    text: str
    meta: Dict[str, str] = {}

class AskReq(BaseModel):
    question: str
    top_k: int = 4

@app.get("/health")
def health(): return {"ok": True}

@app.post("/ingest")
def ingest(items: List[IngestItem]):
    texts = [it.text for it in items]
    metas = [it.meta for it in items]
    ids   = [it.id for it in items]
    embs  = embed.encode(texts, normalize_embeddings=True).tolist()
    coll.add(documents=texts, embeddings=embs, metadatas=metas, ids=ids)
    return {"ok": True, "count": len(items)}

def _prompt(q:str, ctxs:List[str]) -> str:
    ctx = "\n\n".join(f"[{i+1}] {c}" for i,c in enumerate(ctxs))
    return f"You are David’s portfolio assistant. Use only the context.\n\nContext:\n{ctx}\n\nQ: {q}\nA:"

def llm_complete(prompt:str) -> str:
    # TODO: plug your LLM provider here (OpenAI/Anthropic/etc.)
    return "Stub: connect your LLM provider."

@app.post("/ask")
def ask(req: AskReq):
    qvec = embed.encode([req.question], normalize_embeddings=True).tolist()
    res  = coll.query(query_embeddings=qvec, n_results=req.top_k)
    ctxs = res["documents"][0] if res["documents"] else []
    ans  = llm_complete(_prompt(req.question, ctxs))
    return {"answer": ans, "sources": res.get("metadatas", [[]])[0]}
