from pathlib import Path
import streamlit as st
from chatbot import ask

# ---------------- Page setup ----------------
st.set_page_config(
    page_title="Tata Car Guide",
    page_icon="🚗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
CSS_PATH = BASE_DIR / "static" / "style.css"

# Load the custom theme from static/style.css.
def load_css():
    if CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css()

MODELS = [
    "Punch", "Punch EV", "Nexon", "Nexon EV", "Curvv", "Curvv EV",
    "Harrier", "Harrier EV", "Safari", "Sierra",
]
STARTERS = [
    "Which Nexon variants have a sunroof?",
    "Compare the Harrier and the Safari",
    "What colours does the Curvv come in?",
]

# ---------------- Session state ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ---------------- Header ----------------
st.markdown(
    '<div class="tata-header">'
    '<div class="tata-header-top"><span class="tata-signal"></span>'
    '<div><div class="tata-title">Tata Car Guide</div>'
    '<div class="tata-subtitle">Answers from the Tata brochures</div></div>'
    '</div><div class="tata-tagline">Ask about variants, features, engines, batteries and colours.</div>'
    '</div>',
    unsafe_allow_html=True,
)

header_cols = st.columns([5, 1])
with header_cols[0]:
    st.markdown('<div class="section-label">EXPLORE A MODEL</div>', unsafe_allow_html=True)
with header_cols[1]:
    if st.button("New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()

# Model chips: each click sends a question to the same RAG function.
model_cols = st.columns(5)
for index, model in enumerate(MODELS):
    with model_cols[index % 5]:
        if st.button(model, key=f"model_{index}", use_container_width=True):
            st.session_state.pending_question = (
                f"Give me an overview of the Tata {model}: price range, variants, "
                "colours, engine or battery and range, safety rating and key features. "
                "If a detail is not present in the provided documents, say so."
            )
            st.rerun()

st.markdown('<div class="chat-divider"></div>', unsafe_allow_html=True)

# ---------------- Empty state / starter questions ----------------
if not st.session_state.messages:
    st.markdown(
        '<div class="welcome-card"><div class="welcome-eyebrow">TATA CAR ASSISTANT</div>'
        '<div class="welcome-title">Which Tata are you looking at?</div>'
        '<div class="welcome-copy">Ask about variants, features, engines or colours. '
        'Choose a model above or try one of these questions.</div></div>',
        unsafe_allow_html=True,
    )
    starter_cols = st.columns(1)
    for index, starter in enumerate(STARTERS):
        if st.button(f"↗  {starter}", key=f"starter_{index}", use_container_width=True):
            st.session_state.pending_question = starter
            st.rerun()

# ---------------- Chat history ----------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            st.markdown(
                "<div class='source-label'>SOURCES</div>",
                unsafe_allow_html=True,
            )
            st.caption(" · ".join(map(str, message["sources"])))

# ---------------- Question handling ----------------
question = st.chat_input("Ask about a Tata car, variant or feature…")
if question:
    st.session_state.pending_question = question

if st.session_state.pending_question:
    current_question = st.session_state.pending_question.strip()
    st.session_state.pending_question = None

    if current_question:
        st.session_state.messages.append({"role": "user", "content": current_question})
        with st.chat_message("user"):
            st.markdown(current_question)

        with st.chat_message("assistant"):
            with st.spinner("Searching the Tata car documents…"):
                try:
                    result = ask(current_question)
                    if not isinstance(result, tuple) or len(result) != 2:
                        raise ValueError(
                            "chatbot.ask(question) must return two values: (answer, sources)."
                        )
                    answer, sources = result
                    answer = str(answer or "I couldn't find that information in the documents.")
                    sources = sources or []
                    st.markdown(answer)
                    if sources:
                        st.markdown("<div class='source-label'>SOURCES</div>", unsafe_allow_html=True)
                        st.caption(" · ".join(map(str, sources)))
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })
                except Exception as exc:
                    st.error("The chatbot could not answer this question.")
                    st.caption(f"Error details: {exc}")
                    st.info(
                        "Check that chatbot.py is present, the Chroma database is available, "
                        "and the required API key is configured in Streamlit Secrets."
                    )
