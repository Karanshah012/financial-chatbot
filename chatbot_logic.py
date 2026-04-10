# chatbot_logic.py
import os
import pandas as pd
from langchain_ollama.chat_models import ChatOllama
from langchain.vectorstores import FAISS
from admin_backend import ensure_vector_store_available, get_embeddings
from predictive_analysis import parse_financial_query

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


# ---------------- INIT ----------------
def init_chatbot():
    ensure_vector_store_available()
    embeddings = get_embeddings()

    vector_db = FAISS.load_local(
        "vector_store/faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    llm = ChatOllama(model=OLLAMA_MODEL)

    return {
        "llm": llm,
        "vector_db": vector_db
    }


# ---------------- USER DATA ----------------
def get_user_data(account_number):
    df = pd.read_csv("data/users.csv", dtype=str)
    match = df[df["account_number"] == str(account_number)]
    return match.iloc[0].to_dict() if not match.empty else None


# ---------------- MAIN CHAT ----------------
def chat_with_bot(user_message, chatbot, session):
    llm = chatbot["llm"]
    vector_db = chatbot["vector_db"]

    text = user_message.strip().lower()

    # =========================================================
    # 🔐 ACCOUNT VALIDATION
    # =========================================================
    if session.get("awaiting_account", False):
        user_data = get_user_data(text)

        if not user_data:
            return "❌ Invalid account number. Please enter a valid account number."

        session["account_number"] = text
        session["awaiting_account"] = False
        return "✅ Account verified successfully. You can now ask about your account."

    user_data = get_user_data(session.get("account_number")) if session.get("account_number") else None

    # =========================================================
    # 🧠 1. PREDICTION (HIGHEST PRIORITY)
    # =========================================================
    prediction_keywords = ["predict", "future", "next", "forecast", "estimate"]

    if any(word in text for word in prediction_keywords):
        prediction = parse_financial_query(text)

        if prediction:
            return prediction
        else:
            return "📊 Please provide more details like amount, duration, or rate for accurate prediction."

    # =========================================================
    # 📊 2. INVESTMENT ADVISOR
    # =========================================================
    if "invest" in text or "investment" in text:
        return (
            "📊 **Recommended Investment Options:**\n\n"
            "• Fixed Deposits – Safe and stable returns\n"
            "• Mutual Funds / SIP – Long-term wealth creation\n"
            "• PPF – Tax-saving with guaranteed returns\n"
            "• Stocks – High return (with risk)\n"
            "• Gold – Safe hedge against inflation\n\n"
            "👉 Suggestion: Diversify your portfolio based on your risk appetite and goals."
        )

    # =========================================================
    # 🔐 3. PERSONAL DATA (STRICT)
    # =========================================================
    if "balance" in text:
        if not user_data:
            session["awaiting_account"] = True
            return "🔐 Please enter your account number to check your balance."

        return f"💰 Your current account balance is ₹{user_data.get('balance', 'N/A')}."

    if "transaction" in text:
        # IMPORTANT FIX: avoid conflict with prediction queries
        if any(word in text for word in ["predict", "next", "future"]):
            pass
        else:
            if not user_data:
                session["awaiting_account"] = True
                return "🔐 Please enter your account number to view transactions."

            return f"📄 Your last transaction: {user_data.get('last_transaction', 'N/A')}."

    # =========================================================
    # 🧠 4. RAG (KNOWLEDGE BASE)
    # =========================================================
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    docs = retriever.get_relevant_documents(text)

    context = "\n\n".join([doc.page_content for doc in docs]) if docs else ""

    # =========================================================
    # 🤖 SMART FALLBACK
    # =========================================================
    financial_keywords = [
        "bank", "loan", "fd", "interest", "account",
        "investment", "money", "credit", "debit", "emi"
    ]

    is_financial = any(word in text for word in financial_keywords)

    if not context:
        if is_financial:
            return (
                "⚠️ I don't have complete information on that topic.\n\n"
                "📞 I can arrange a call with a banking advisor if you'd like.\n"
                "Type YES to proceed."
            )
        else:
            return (
                "🤖 I'm designed to assist with banking and financial queries.\n\n"
                "Please ask something related to banking, loans, investments, or your account."
            )

    # =========================================================
    # 🧠 5. FINAL AI RESPONSE
    # =========================================================
    prompt = f"""
You are a professional AI Banking Assistant.

Your job is to:
- Understand user intent clearly
- Provide accurate and professional answers
- Use the context if available
- If context is partial, enhance with financial knowledge

Context:
{context}

User Question:
{text}

Answer in a clear, structured, and professional way.
"""

    response = llm.invoke(prompt)

    return response.content if hasattr(response, "content") else str(response)
