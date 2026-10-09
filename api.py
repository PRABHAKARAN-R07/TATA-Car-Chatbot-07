from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chatbot import ask  # reuses your retriever + Groq chain

app = FastAPI(title="Tata Car Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    question: str


@app.post("/chat")
def chat(q: Query):
    question = q.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty.")
    try:
        answer, sources = ask(question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"answer": answer, "sources": sources}


# Must stay LAST: serves static/index.html, style.css, script.js
app.mount("/", StaticFiles(directory="static", html=True), name="static")