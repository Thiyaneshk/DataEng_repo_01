import streamlit as st
from app.config import get_config
import duckdb

def main():
    st.title("🤖 Market Assistant (RAG Chat)")
    st.write("Interact with your market data using a Local LLM.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about your stocks..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            st.markdown("*(SCAFFOLD: Local LLM Integration placeholder)*")
            st.write("I am pre-wired to read context from `fct_equity_features_1d`.")
            st.info("Check `docs/RAG_ARCH.md` for integration steps.")

if __name__ == "__main__":
    main()
