import os
import json
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document

load_dotenv()

DOCUMENTS_DIR = Path("documents")
VECTOR_STORE_DIR = Path("vector_store")
VECTOR_STORE_PATH = VECTOR_STORE_DIR / "index.json"

def read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)

def read_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def read_document(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return read_txt(path)
    if path.suffix.lower() == ".pdf":
        return read_pdf(path)
    if path.suffix.lower() == ".docx":
        return read_docx(path)
    return ""

def chunk_text(text: str, chunk_size: int = 1400, overlap: int = 250) -> List[str]:
    clean = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(clean):
        end = start + chunk_size
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY. Copia .env.example como .env y pega tu API key.")

    client = OpenAI(api_key=api_key)
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    VECTOR_STORE_DIR.mkdir(exist_ok=True)
    supported = {".txt", ".pdf", ".docx"}
    docs = [p for p in DOCUMENTS_DIR.iterdir() if p.suffix.lower() in supported]

    if not docs:
        raise RuntimeError("No hay documentos en /documents.")

    indexed = []

    for path in docs:
        print(f"Leyendo {path.name}")
        text = read_document(path)
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            print(f"  Indexando fragmento {i + 1}/{len(chunks)}")
            response = client.embeddings.create(model=embedding_model, input=chunk)
            indexed.append({
                "source": path.name,
                "chunk_id": i,
                "text": chunk,
                "embedding": response.data[0].embedding
            })

    with open(VECTOR_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(indexed, f, ensure_ascii=False)

    print(f"Listo. Fragmentos indexados: {len(indexed)}")

if __name__ == "__main__":
    main()
