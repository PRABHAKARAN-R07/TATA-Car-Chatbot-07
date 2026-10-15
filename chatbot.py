import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# --------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES AND GROQ API KEY
# --------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# If the key is not in the environment, try Streamlit Secrets.
if not GROQ_API_KEY:
    try:
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
    except Exception:
        GROQ_API_KEY = None

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Add it to your local .env "
        "file or Streamlit Cloud Secrets."
    )


# --------------------------------------------------
# 2. LOAD CHROMA VECTOR DATABASE
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "chroma_db"

if not DB_DIR.is_dir():
    raise FileNotFoundError(
        f"ChromaDB directory not found: {DB_DIR}. "
        "Ensure the database exists in your deployed project."
    )

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory=str(DB_DIR),
    embedding_function=embeddings
)

retriever = db.as_retriever(
    search_kwargs={"k": 10}
)


# --------------------------------------------------
# 3. INITIALIZE GROQ LLM
# --------------------------------------------------

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=GROQ_API_KEY
)


# --------------------------------------------------
# 4. CHATBOT PROMPT
# --------------------------------------------------

prompt = ChatPromptTemplate.from_template(
    """You are "Tata Car Guide", an expert assistant on Tata Motors
SUVs sold in India.

You answer from the CONTEXT below, taken from the
"Tata SUVs in India - Feature Guide (October 2026)".

The guide covers exactly 10 models:
Punch, Punch EV, Nexon, Nexon EV, Curvv, Curvv EV,
Harrier, Harrier EV, Safari, Sierra.

CONTEXT:
{context}

QUESTION:
{question}

HOW TO ANSWER

1. Use only facts that appear in the CONTEXT.
   Never invent prices, variants, colours, specifications or ratings.

2. The context mixes several models. Each line starts with a model name,
   for example "Tata Punch - ..." or "Tata Punch EV - ...".
   Use only the lines for the model the user asked about.
   "Punch" means the petrol/CNG Punch, not the Punch EV,
   unless the user says EV or asks for both.

3. Always give whatever the context supports, even if it is only
   part of the answer.
   Say "I couldn't find that in the documents." ONLY when the
   context has nothing relevant.
   If something is missing, answer the rest and add one line such as
   "The guide doesn't mention the mileage."

4. When an entry says "higher variants", "select variants",
   "top variants" or "check brochure", repeat that wording.
   Do not guess which variant has the feature.

5. For "tell me about" or overview questions, cover:
   price range, variants, colours, engine or battery and range,
   safety rating, and 4 to 6 key features, when available.

6. For comparisons, use a Markdown table with one column per model
   and one row per attribute.

7. Prices are ex-showroom (Delhi) in Rs. lakh.
   When you quote a price, add once:
   "On-road price will be higher."

8. If the user asks for a list of cars, list the 10 models above,
   grouped as petrol/diesel/CNG and electric, using only information
   supported by the CONTEXT.

9. Be concise and friendly. Use short bullets with bold labels.
   Do not mention "context" or page numbers.
   The app already shows the sources.

ANSWER:"""
)


# --------------------------------------------------
# 5. CREATE RAG CHAIN
# --------------------------------------------------

chain = prompt | llm | StrOutputParser()


# --------------------------------------------------
# 6. ASK FUNCTION
# --------------------------------------------------

def ask(question: str):
    if not isinstance(question, str):
        raise TypeError("question must be a string")

    question = question.strip()

    if not question:
        return (
            "Please enter a question about a Tata car, variant, or feature.",
            []
        )

    # Retrieve relevant documents from ChromaDB.
    docs = retriever.invoke(question)

    if not docs:
        return (
            "I couldn't find that information in the documents.",
            []
        )

    # Combine retrieved document content.
    context = "\n\n".join(
        doc.page_content for doc in docs
    )

    # Generate the answer using Groq.
    answer = chain.invoke(
        {
            "context": context,
            "question": question
        }
    )

    # Extract source filenames and page numbers.
    sources = set()

    for doc in docs:
        source_path = doc.metadata.get("source", "Unknown source")
        filename = Path(str(source_path)).name

        page = doc.metadata.get("page")

        if isinstance(page, int):
            page_number = page + 1
            sources.add(f"{filename} (p.{page_number})")
        else:
            sources.add(filename)

    return answer, sorted(sources)


# --------------------------------------------------
# 7. OPTIONAL TERMINAL TEST
# --------------------------------------------------

if __name__ == "__main__":
    print("Tata Car Chatbot (type 'exit' to quit)\n")

    while True:
        question = input("You: ").strip()

        if question.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            answer, sources = ask(question)

            print(f"\nBot: {answer}")
            print(f"Sources: {', '.join(sources)}\n")

        except Exception as error:
            print(f"\nError: {error}\n")
