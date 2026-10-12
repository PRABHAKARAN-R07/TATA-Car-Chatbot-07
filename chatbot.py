from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

DB_DIR = "chroma_db"

# Vector DB + retriever
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
retriever = db.as_retriever(search_kwargs={"k": 10})

# LLM
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

# Prompt
prompt = ChatPromptTemplate.from_template(
    """You are "Tata Car Guide", an expert assistant on Tata Motors SUVs sold in India.
You answer from the CONTEXT below, taken from the "Tata SUVs in India - Feature Guide (October 2026)".
The guide covers exactly 10 models: Punch, Punch EV, Nexon, Nexon EV, Curvv, Curvv EV, Harrier, Harrier EV, Safari, Sierra.

CONTEXT:
{context}

QUESTION:
{question}

HOW TO ANSWER
1. Use only facts that appear in the CONTEXT. Never invent prices, variants, colours, specs or ratings.
2. The context mixes several models. Each line starts with a model name, for example "Tata Punch - ..." or "Tata Punch EV - ...". Use only the lines for the model the user asked about. "Punch" means the petrol/CNG Punch, not the Punch EV, unless the user says EV or asks for both.
3. Always give whatever the context supports, even if it is only part of the answer. Say "I couldn't find that in the documents." ONLY when the context has nothing relevant. If something is missing, answer the rest and add one line such as "The guide doesn't mention the mileage."
4. When an entry says "higher variants", "select variants", "top variants" or "check brochure", repeat that wording. Do not guess which variant has the feature.
5. For "tell me about" or overview questions, cover: price range, variants, colours, engine or battery and range, safety rating, and 4 to 6 key features.
6. For comparisons, use a markdown table with one column per model and one row per attribute.
7. Prices are ex-showroom (Delhi) in Rs. lakh. When you quote a price, add once: "On-road price will be higher."
8. If the user asks for a list of cars, list the 10 models above, grouped as petrol/diesel/CNG and electric.
9. Be concise and friendly. Use short bullets with bold labels. Do not mention "context" or page numbers; the app already shows the sources.

ANSWER:"""
)

chain = prompt | llm | StrOutputParser()


def ask(question: str):
    if not isinstance(question, str):
        raise TypeError("question must be a string")

    question = question.strip()
    if not question:
        return "Please enter a question about a Tata car, variant, or feature.", []

    docs = retriever.invoke(question)
    if not docs:
        return "I couldn't find that information in the documents.", []

    context = "\n\n".join(d.page_content for d in docs)
    answer = chain.invoke({"context": context, "question": question})
    sources = sorted({
        f"{d.metadata.get('source', '?').split('/')[-1].split(chr(92))[-1]} "
        f"(p.{d.metadata.get('page', 0) + 1})"
        for d in docs
    })
    return answer, sources


if __name__ == "__main__":
    print("Tata Car Chatbot (type 'exit' to quit)\n")
    while True:
        q = input("You: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        if not q:
            continue
        answer, sources = ask(q)
        print(f"\nBot: {answer}")
        print(f"Sources: {', '.join(sources)}\n")