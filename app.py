"""Streamlit UI for the Mem0 + LangChain interview prep assistant."""

import streamlit as st
from memory_agent import chat, get_all_memories

st.set_page_config(page_title="AI Interview Prep Coach", page_icon="🧠")
st.title("🧠 AI Interview Prep Coach")
st.caption("Powered by LangChain + Mem0 + Groq — remembers you across sessions.")

with st.sidebar:
    st.header("Session")
    user_id = st.text_input("User ID", value="alice")
    st.markdown("---")
    if st.button("Show stored memories"):
        st.write(get_all_memories(user_id))
    st.markdown("---")
    if st.button("Clear transcript"):
        st.session_state.pop("messages", None)
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Tell me about your prep, or answer my question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = chat(user_id=user_id, user_message=user_input)
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})