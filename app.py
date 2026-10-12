from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chatbot import ask

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Tata Car Guide API")
logging.basicConfig(level=logging.INFO)


class Query(BaseModel):
    question: str


@app.get("/")
def home():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="static/index.html was not found.")
    return FileResponse(index_file)


@app.post("/chat")
def chat(q: Query):
    question = q.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty.")

    try:
        result = ask(question)

        # Your existing chatbot may return (answer, sources) or just an answer.
        if isinstance(result, tuple) and len(result) >= 2:
            answer, sources = result[0], result[1]
        else:
            answer, sources = result, []

        if not isinstance(answer, str):
            answer = getattr(answer, "content", str(answer))

        if sources is None:
            sources = []
        elif not isinstance(sources, (list, tuple)):
            sources = [str(sources)]

        # Convert source documents into JSON-safe values.
        safe_sources = []
        for source in sources:
            if isinstance(source, str):
                safe_sources.append(source)
            elif hasattr(source, "metadata"):
                metadata = source.metadata or {}
                safe_sources.append({
                    "source": str(metadata.get("source", metadata.get("file_path", "Tata brochure"))),
                    "page": metadata.get("page", "")
                })
            else:
                safe_sources.append(str(source))

        return {"answer": answer, "sources": safe_sources}

    except HTTPException:
        raise
    except Exception:
        logging.exception("Chat request failed")
        raise HTTPException(
            status_code=500,
            detail="Could not generate an answer. Check the server terminal for details."
        )


# Mount static assets last so the API route remains available.
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
