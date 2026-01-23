# session_manager.py
import streamlit as st

def init_session():
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "account_number" not in st.session_state:
        st.session_state["account_number"] = None
    if "awaiting_account" not in st.session_state:
        st.session_state["awaiting_account"] = False
    # faq_chain loaded lazily by app.py into session_state["faq_chain"]

def add_message(role, content):
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    st.session_state["chat_history"].append({"role": role, "content": content})

def clear_session():
    keys = ["chat_history", "account_number", "awaiting_account", "faq_chain"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
