# admin_backend.py

import json
import sqlite3
from pathlib import Path
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import os

# ------------------ Paths ------------------
FAQ_PATH = Path("data/faqs.json")
VECTOR_DIR = Path("vector_store/faiss_index")
ADMIN_DB = Path("admin.db")

# ------------------ Embeddings ------------------
def get_embeddings():
    """Return HuggingFace embedding model."""
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    return HuggingFaceEmbeddings(model_name=model_name)

# ------------------ FAQ Helpers ------------------
def load_faqs():
    """Load FAQs from faqs.json"""
    if not FAQ_PATH.exists():
        FAQ_PATH.parent.mkdir(parents=True, exist_ok=True)
        FAQ_PATH.write_text("[]", encoding="utf-8")
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_faqs(faqs):
    """Save FAQs to faqs.json"""
    FAQ_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FAQ_PATH, "w", encoding="utf-8") as f:
        json.dump(faqs, f, indent=2, ensure_ascii=False)

def add_faq(question, answer):
    """Add a new FAQ and update vector store."""
    faqs = load_faqs()
    faqs.append({"question": question, "answer": answer})
    save_faqs(faqs)
    update_vector_store_from_faqs()  # 🔄 Auto-update FAISS

def delete_faq(index):
    """Delete a FAQ by index and update vector store."""
    faqs = load_faqs()
    if 0 <= index < len(faqs):
        faqs.pop(index)
        save_faqs(faqs)
        update_vector_store_from_faqs()  # 🔄 Auto-update FAISS
        return True
    return False

# ------------------ Vector Store ------------------
def update_vector_store_from_faqs():
    """
    Rebuild FAISS index from faqs.json.
    Ensures latest FAQ data is searchable.
    """
    faqs = load_faqs()
    if not faqs:
        texts = ["No FAQs available."]
    else:
        texts = [f["question"] + " " + f["answer"] for f in faqs]

    embeddings = get_embeddings()
    vector_db = FAISS.from_texts(texts, embeddings)

    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    vector_db.save_local(str(VECTOR_DIR))

def ensure_vector_store_available():
    """
    Ensure FAISS index exists; create if missing.
    """
    embeddings = get_embeddings()
    if not VECTOR_DIR.exists() or not any(VECTOR_DIR.iterdir()):
        update_vector_store_from_faqs()

    return FAISS.load_local(
        str(VECTOR_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

# ------------------ Admin Database ------------------
def connect_db():
    """Connect to SQLite admin DB."""
    ADMIN_DB.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(ADMIN_DB))

def initialize_admin_db():
    """Create admin table if not exists."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    # Default admin account
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO admins (admin_id, password) VALUES (?, ?)", ("admin", "12345"))
        conn.commit()
    conn.close()

def check_admin_login(admin_id, password):
    """Validate admin credentials."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admins WHERE admin_id=? AND password=?", (admin_id, password))
    found = cur.fetchone()
    conn.close()
    return bool(found)

# ------------------ Initialize on Import ------------------
initialize_admin_db()
ensure_vector_store_available()
