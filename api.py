
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from chatbot import ask


# Project directories
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Tata Car Guide")


# Request format
class Query(BaseModel):
    question: str


# Serve the main HTML page
@app.get("/")
def home():
    index_file = STATIC_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="static/index.html was not found."
        )

    return FileResponse(index_file)


# Chat API
@app.post("/api/chat")
def chat(q: Query):
    question = q.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    try:
        # Your existing RAG function returns answer and sources
        answer, sources = ask(question)

        # Ensure the answer is JSON serializable
        if not isinstance(answer, str):
            answer = getattr(answer, "content", str(answer))

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception:
        app.logger.exception("Chat request failed")

        raise HTTPException(
            status_code=500,
            detail="Could not generate an answer. Check the server logs."
        )


# Serve CSS, JavaScript and other static assets
app.mount(
    "/",
    StaticFiles(directory=str(STATIC_DIR), html=True),
    name="static"
)
