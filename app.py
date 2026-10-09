import streamlit as st
from chatbot import ask

st.set_page_config(page_title="Tata Car Chatbot", page_icon="🚗")
st.title("🚗 Tata Car Chatbot")
st.caption("Ask about Tata car types and variants")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if question := st.chat_input("Ask about a Tata car..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            answer, sources = ask(question)
        st.markdown(answer)
        st.caption("Sources: " + ", ".join(sources))

    st.session_state.messages.append({"role": "assistant", "content": answer})