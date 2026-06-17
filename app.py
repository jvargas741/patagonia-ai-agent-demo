import json
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI

from rag import search_documents, format_context, load_index
from prompts import SYSTEM_PROMPT, build_user_prompt

load_dotenv()

BASE_DIR = Path(__file__).parent
PUBLIC_DIR = BASE_DIR / "public"

app = FastAPI(title="Patagonia AI Agent Demo")
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

class EvaluationRequest(BaseModel):
    title: str
    decision_type: str
    description: str

@app.get("/")
def index():
    return FileResponse(PUBLIC_DIR / "index.html")

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "indexed_chunks": len(load_index()),
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    }

@app.get("/api/sources")
def sources():
    index = load_index()
    docs = {}
    for item in index:
        docs[item["source"]] = docs.get(item["source"], 0) + 1
    return {
        "documents": [{"source": k, "chunks": v} for k, v in sorted(docs.items())]
    }

@app.post("/api/evaluate")
def evaluate(req: EvaluationRequest):
    if not os.getenv("OPENAI_API_KEY"):
        return JSONResponse(
            status_code=500,
            content={"error": "OPENAI_API_KEY no está configurada."}
        )

    query = f"{req.title}\n{req.decision_type}\n{req.description}"
    chunks = search_documents(query, top_k=6)
    context = format_context(chunks)

    prompt = build_user_prompt(
        decision_title=req.title,
        decision_type=req.decision_type,
        decision_description=req.description,
        retrieved_context=context
    )

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

    try:
  response = client.chat.completions.create(

    model=model,

    messages=[

        {"role": "system", "content": SYSTEM_PROMPT},

        {"role": "user", "content": prompt}

    ],

    temperature=0.2

)

output_text = response.choices[0].message.content.strip()

        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError:
            parsed = {
                "score_total": None,
                "nivel_riesgo": "No estructurado",
                "recomendacion_tipo": "solicitar_mas_informacion",
                "resumen_ejecutivo": output_text,
                "desglose": {},
                "banderas_alerta": ["La respuesta no vino en formato JSON válido."],
                "evidencia_consultada": [],
                "recomendacion_comite": "Revisar manualmente.",
                "condiciones_minimas": [],
                "preguntas_para_comite": [],
                "limitaciones": ["El modelo no devolvió JSON válido."]
            }

        return {
            "evaluation": parsed,
            "retrieved_chunks": [
                {
                    "source": c["source"],
                    "chunk_id": c["chunk_id"],
                    "score": c["score"],
                    "text": c["text"][:900]
                }
                for c in chunks
            ]
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "message": "Error al llamar a OpenAI. Revisa API key, créditos, modelo y conexión."
            }
        )
