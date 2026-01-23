# chatbot_logic.py
import os
import pandas as pd
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_ollama.chat_models import ChatOllama
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from admin_backend import ensure_vector_store_available, get_embeddings
from predictive_analysis import parse_financial_query


# Ollama model (Llama 3 recommended)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def init_chatbot():
    """Initialize the Ollama LLM + FAISS retriever + memory."""
    ensure_vector_store_available()
    embeddings = get_embeddings()

    # Load vector DB
    vector_db = FAISS.load_local(
        "vector_store/faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    llm = ChatOllama(model=OLLAMA_MODEL)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    return {
        "llm": llm,
        "retriever": vector_db.as_retriever(),
        "memory": memory
    }


# --------------------- USER DATA FETCH ---------------------
def get_user_data(account_number):
    """Fetch user info from CSV file."""
    df = pd.read_csv("data/users.csv", dtype=str)
    match = df[df["account_number"] == str(account_number)]
    return match.iloc[0].to_dict() if not match.empty else None


# --------------------- MAIN CHAT LOGIC ---------------------
def chat_with_bot(user_message, chatbot, session):
    llm = chatbot["llm"]
    retriever = chatbot["retriever"]

    text = user_message.strip()

    # 1️⃣ If awaiting account number
    if session.get("awaiting_account", False):
        acct = text.strip()
        session["account_number"] = acct
        session["awaiting_account"] = False
        return "✅ Got your account number. Now you can ask about balance, transactions, or predictions."

    # 2️⃣ Retrieve user data if exists
    user_data = get_user_data(session.get("account_number")) if session.get("account_number") else None

    # 3️⃣ AI decides INTENT dynamically
    intent_prompt = PromptTemplate(
        input_variables=["message"],
        template=(
            "You are an AI financial intent classifier.\n"
            "Given the user's message, decide the most likely intent from this list:\n"
            "[balance_check, transaction_query, fd_prediction, investment_prediction, spending_prediction, general_bank_query, unknown]\n"
            "Return only one word from the list.\n\nUser message: {message}"
        )
    )
    intent_chain = LLMChain(llm=llm, prompt=intent_prompt)
    intent = intent_chain.run(message=text).strip().lower()

    # 4️⃣ Handle based on intent
    if intent in ["fd_prediction", "investment_prediction", "spending_prediction"]:
        ai_response = parse_financial_query(text)
        if ai_response:
            return ai_response

    if intent == "balance_check":
        if not user_data:
            session["awaiting_account"] = True
            return "🔐 Please enter your account number to continue."
        return f"💰 Your current balance is ₹{user_data.get('balance', 'N/A')}."

    if intent == "transaction_query":
        if not user_data:
            session["awaiting_account"] = True
            return "🔐 Please enter your account number to continue."
        return f"📄 Your last transaction: {user_data.get('last_transaction', 'N/A')}."

    # 5️⃣ If intent is general or unknown → use AI reasoning with context
    context_docs = retriever.get_relevant_documents(text)
    context = "\n\n".join(d.page_content for d in context_docs[:3]) if context_docs else "No context found."

    reasoning_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are an intelligent financial assistant with advanced reasoning.\n"
            "Use the following context and your own financial knowledge to answer clearly and logically.\n\n"
            "Context:\n{context}\n\n"
            "Question:\n{question}\n\n"
            "Give step-by-step reasoning if needed (like calculations or comparisons)."
        )
    )
    reasoning_chain = LLMChain(llm=llm, prompt=reasoning_prompt)
    answer = reasoning_chain.run(context=context, question=text)

    return answer
