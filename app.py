
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chatbot import ask

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tata Car Guide API",
    description="RAG chatbot for Tata Motors cars",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {"status": "ok"}


class Query(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question about Tata cars"
    )


@app.get("/", include_in_schema=False)
def home():
    if not INDEX_FILE.is_file():
        raise HTTPException(
            status_code=404,
            detail="static/index.html was not found."
        )

    return FileResponse(INDEX_FILE)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(query: Query):
    question = query.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    try:
        answer, sources = ask(question)

        return {
            "answer": answer,
            "sources": sources or []
        }

    except Exception:
        logger.exception("Chat request failed")

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not generate an answer. "
                "Check the Vercel function logs."
            )
        )


# Mount frontend assets after defining API routes.
if STATIC_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(
            directory=str(STATIC_DIR),
            html=True
        ),
        name="static"
    )
