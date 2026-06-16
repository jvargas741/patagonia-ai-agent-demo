import json
import math
import os
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI

VECTOR_STORE_PATH = Path("vector_store/index.json")

def get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_index() -> List[Dict[str, Any]]:
    if not VECTOR_STORE_PATH.exists():
        return []
    with open(VECTOR_STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def get_embedding(text: str) -> List[float]:
    client = get_client()
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding

def search_documents(query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    index = load_index()
    if not index:
        return []

    query_embedding = get_embedding(query)

    scored = []
    for item in index:
        scored.append({
            "score": cosine_similarity(query_embedding, item["embedding"]),
            "source": item["source"],
            "chunk_id": item["chunk_id"],
            "text": item["text"]
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

def format_context(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "No hay documentos indexados o no se encontró contexto documental relevante."

    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(
            f"[Fuente {i}: {chunk['source']} | fragmento {chunk['chunk_id']} | similitud {chunk['score']:.3f}]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(blocks)
