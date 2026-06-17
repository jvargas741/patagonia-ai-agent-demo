import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

from prompts import SYSTEM_PROMPT, build_user_prompt
from rag import format_context, load_index, search_documents

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
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    }


@app.get("/api/sources")
def sources():
    index = load_index()

    documents = {}
    for item in index:
        source = item["source"]
        documents[source] = documents.get(source, 0) + 1

    return {
        "documents": [
            {"source": source, "chunks": chunks}
            for source, chunks in sorted(documents.items())
        ]
    }


@app.post("/api/evaluate")
def evaluate(req: EvaluationRequest):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return JSONResponse(
            status_code=500,
            content={
                "error": "OPENAI_API_KEY no está configurada en Render."
            },
        )

    query = f"{req.title}\n{req.decision_type}\n{req.description}"

    try:
        chunks = search_documents(query, top_k=6)
        context = format_context(chunks)

        user_prompt = build_user_prompt(
            decision_title=req.title,
            decision_type=req.decision_type,
            decision_description=req.description,
            retrieved_context=context,
        )

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
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
                "banderas_alerta": [
                    "El modelo respondió, pero no devolvió JSON válido."
                ],
                "evidencia_consultada": [],
                "recomendacion_comite": "Revisar manualmente la respuesta generada.",
                "condiciones_minimas": [],
                "preguntas_para_comite": [],
                "limitaciones": [
                    "La respuesta no pudo ser convertida a JSON estructurado."
                ],
            }

        return {
            "evaluation": parsed,
            "retrieved_chunks": [
                {
                    "source": chunk["source"],
                    "chunk_id": chunk["chunk_id"],
                    "score": chunk["score"],
                    "text": chunk["text"][:900],
                }
                for chunk in chunks
            ],
        }

    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(error),
                "message": "Error al evaluar la decisión. Revisa modelo, API key, créditos o logs de Render.",
            },
        )
