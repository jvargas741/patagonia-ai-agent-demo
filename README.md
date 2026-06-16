# Patagonia AI Agent Demo — Asistente de Coherencia

Este proyecto es una **demo funcional**, no solo una maqueta visual.

Permite abrir una interfaz web, escribir una decisión estratégica y recibir una evaluación generada por IA con:

- Score de coherencia.
- Nivel de riesgo.
- Riesgos detectados.
- Evidencia documental.
- Recomendación para Comité.
- Condiciones mínimas.
- Preguntas para decisión ejecutiva.

## Qué es técnicamente

Es un agente RAG sencillo:

```text
Interfaz HTML
   ↓
Backend FastAPI
   ↓
Búsqueda documental / RAG
   ↓
OpenAI API
   ↓
Respuesta estructurada JSON
   ↓
Dashboard visual
```

## Qué debes entregar

La forma más profesional de entrega es:

```text
1. URL pública de la app desplegada.
2. ZIP del código fuente.
3. API key configurada en el servidor, no visible para el profesor.
4. Documentos base cargados.
```

## Instalación local

### 1. Instala Python 3.11+

### 2. Crea ambiente virtual

Mac:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instala dependencias

```bash
pip install -r requirements.txt
```

### 4. Configura API key

Copia `.env.example` como `.env`.

Mac:

```bash
cp .env.example .env
```

Windows:

```bash
copy .env.example .env
```

Edita `.env` y pega tu API key real:

```text
OPENAI_API_KEY=sk-...
```

### 5. Indexa documentos

```bash
python index_documents.py
```

### 6. Corre la app

```bash
uvicorn app:app --reload
```

Abre:

```text
http://127.0.0.1:8000
```

## Cómo desplegar en Render

1. Crea una cuenta en Render.
2. Crea un nuevo **Web Service**.
3. Conecta un repositorio de GitHub con este proyecto.
4. Build command:

```bash
pip install -r requirements.txt && python index_documents.py
```

5. Start command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

6. En Environment Variables agrega:

```text
OPENAI_API_KEY=tu_api_key_real
OPENAI_MODEL=gpt-5.4-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

7. Render te dará una URL pública. Esa es la URL que puedes entregar.

## Cómo agregar documentos reales

Copia documentos `.pdf`, `.txt` o `.docx` dentro de:

```text
documents/
```

Luego ejecuta otra vez:

```bash
python index_documents.py
```

## Documentos incluidos

El proyecto trae documentos demo sintéticos para que funcione desde el inicio:

- `01_mision_patagonia_demo.txt`
- `02_worn_wear_demo.txt`
- `03_supplier_code_demo.txt`
- `04_decision_framework_demo.txt`

Para una entrega más sólida, reemplázalos o compleméntalos con documentos reales de Patagonia.

## Caso de prueba sugerido

```text
Patagonia quiere lanzar una alianza con un retailer masivo en Europa. 
El socio tiene gran capacidad de distribución, pero no tiene certificación B Corp 
y ha recibido críticas por prácticas laborales en proveedores indirectos.
```

## Limitación importante

Este prototipo no toma decisiones finales. Es una herramienta de apoyo para análisis preliminar del Comité.
