
import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load .env for local development.
# On Vercel, configure GROQ_API_KEY in Environment Variables.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "chroma_db"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "openai/gpt-oss-20b"


@lru_cache(maxsize=1)
def get_resources():
    """Initialize and cache the RAG resources."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Configure it in "
            "Vercel Project Settings > Environment Variables."
        )

    if not DB_DIR.is_dir():
        raise FileNotFoundError(
            f"ChromaDB directory not found: {DB_DIR}. "
            "Ensure chroma_db is included in your deployment."
        )

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    db = Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embeddings
    )

    retriever = db.as_retriever(
        search_kwargs={"k": 10}
    )

    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
        api_key=api_key
    )

    prompt = ChatPromptTemplate.from_template(
        """
You are Tata Car Guide, an expert assistant on Tata Motors
SUVs sold in India.

Answer using only the information in the supplied excerpts.

The guide covers these 10 models:
Punch, Punch EV, Nexon, Nexon EV, Curvv, Curvv EV,
Harrier, Harrier EV, Safari, Sierra.

CONTEXT:
{context}

QUESTION:
{question}

INSTRUCTIONS:
1. Use only facts supported by the supplied context.
   Never invent prices, variants, colours, specifications or ratings.
2. "Punch" means the petrol/CNG Punch, not Punch EV,
   unless the user asks for the EV or both.
3. Answer with all relevant information available.
   If a detail is missing, say the guide does not mention it.
4. If the document says "higher variants", "select variants",
   "top variants" or "check brochure", retain that wording.
5. For overview questions, include available prices, variants,
   colours, engine or battery, range, safety rating and features.
6. For comparisons, use a Markdown table.
7. Prices are ex-showroom Delhi in Rs. lakh.
   When quoting a price, add:
   "On-road price will be higher."
8. Be concise and friendly. Use short bullets with bold labels.
9. Do not invent information when the excerpts are insufficient.

ANSWER:
"""
    )

    chain = prompt | llm | StrOutputParser()

    return retriever, chain


def ask(question: str):
    """Retrieve relevant documents and generate an answer."""

    if not isinstance(question, str):
        raise TypeError("question must be a string")

    question = question.strip()

    if not question:
        return (
            "Please enter a question about a Tata car, variant, or feature.",
            []
        )

    retriever, chain = get_resources()

    docs = retriever.invoke(question)

    if not docs:
        return (
            "I couldn't find that information in the documents.",
            []
        )

    context = "\n\n".join(
        doc.page_content for doc in docs
    )

    answer = chain.invoke({
        "context": context,
        "question": question
    })

    sources = set()

    for doc in docs:
        source_path = doc.metadata.get(
            "source", "Unknown source"
        )
        filename = Path(str(source_path)).name
        page = doc.metadata.get("page")

        if isinstance(page, int):
            sources.add(f"{filename} (p.{page + 1})")
        else:
            sources.add(filename)

    return answer, sorted(sources)
