# app.py
import streamlit as st
import time, os, json, uuid
from chatbot_logic import init_chatbot, chat_with_bot
from admin_backend import (
    check_admin_login,
    load_faqs,
    add_faq,
    delete_faq,
    update_vector_store_from_faqs
)
from session_manager import init_session, add_message, clear_session

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(page_title="Bank Chatbot", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------
# Helper Functions
# ------------------------------------------------
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except Exception:
        return []

def list_user_chats(user_id):
    files = [f for f in os.listdir("chat_history") if f.startswith(f"{user_id}_chat_")]
    chats = []
    for f in sorted(files, reverse=True):
        try:
            with open(os.path.join("chat_history", f), "r") as file:
                data = json.load(file)
                first_user_msg = next((m["content"] for m in data if m["role"] == "user"), "New Chat")
                chats.append({"file": f, "title": first_user_msg[:40]})
        except Exception:
            continue
    return chats

# ------------------------------------------------
# SVG ICONS (no image files needed)
# ------------------------------------------------
LOGO_SVG = """
<svg width="40" height="40" viewBox="0 0 512 512" fill="none">
<circle cx="256" cy="256" r="256" fill="#0b57d0"/>
<path d="M130 180h252v30H130v-30zm0 80h252v30H130v-30zm0 80h252v30H130v-30z" fill="white"/>
</svg>
"""

USER_AVATAR_SVG = """
<svg width="40" height="40" viewBox="0 0 512 512" fill="none">
<circle cx="256" cy="256" r="256" fill="#3b82f6"/>
<circle cx="256" cy="200" r="80" fill="white"/>
<path d="M96 416c0-88 320-88 320 0v32H96v-32z" fill="white"/>
</svg>
"""

BOT_AVATAR_SVG = """
<svg width="40" height="40" viewBox="0 0 512 512" fill="none">
<circle cx="256" cy="256" r="256" fill="#facc15"/>
<rect x="176" y="160" width="160" height="192" rx="20" fill="#0b57d0"/>
<circle cx="216" cy="256" r="16" fill="white"/>
<circle cx="296" cy="256" r="16" fill="white"/>
</svg>
"""

# ------------------------------------------------
# Prepare folders
# ------------------------------------------------
os.makedirs("chat_history", exist_ok=True)

# ------------------------------------------------
# Sidebar Role Selection
# ------------------------------------------------
menu = st.sidebar.selectbox("Select Role", ["User", "Admin"])

# ------------------------------------------------
# USER MODE
# ------------------------------------------------
if menu == "User":
    # ---------- CSS Styling ----------
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #eef2ff, #e0e7ff); }

        .header {
            display:flex; align-items:center; gap:12px;
            padding:12px 18px; border-radius:10px;
            background: linear-gradient(90deg,#0b57d0,#2563eb);
            color: white; margin-bottom: 12px;
        }

        .chat-area { padding: 12px; }
        .msg-row { display:flex; align-items:flex-end; gap:10px; max-width: 90%; }
        .msg-row.bot { justify-content:flex-start; }
        .msg-row.user { justify-content:flex-end; align-self:flex-end; }

        .avatar {
            width:38px; height:38px; border-radius:50%;
            background: rgba(255,255,255,0.8);
            display:flex; align-items:center; justify-content:center;
            box-shadow:0 2px 6px rgba(0,0,0,0.1);
        }

        .bubble {
            padding:12px 16px; border-radius:14px; line-height:1.5; font-size:0.95rem;
            box-shadow:0 4px 12px rgba(0,0,0,0.08); max-width:70%;
        }
        .bubble.bot {
            background:#fff; color:#111827; border-top-left-radius:6px;
        }
        .bubble.user {
            background:linear-gradient(90deg,#2563eb,#0b57d0);
            color:white; border-top-right-radius:6px;
        }

        .typing { color:#6b7280; font-style:italic; margin:8px 0; }

        .chat-item {
            padding:8px 10px; border-radius:6px;
            background:rgba(255,255,255,0.15); color:white; margin-bottom:5px;
            cursor:pointer;
        }
        .chat-item:hover { background:rgba(255,255,255,0.25); transition:0.2s; }

        </style>
    """, unsafe_allow_html=True)

    # ---------- Load users ----------
    users = load_users()
    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None
    if "active_chat" not in st.session_state:
        st.session_state.active_chat = None

    # ---------- LOGIN PAGE ----------
    if not st.session_state.logged_in_user:
        st.markdown("<div style='text-align:center;margin-top:70px;'>", unsafe_allow_html=True)
        st.markdown(LOGO_SVG, unsafe_allow_html=True)
        st.markdown("<h1 style='color:#0b57d0;margin-bottom:6px;'>Bank Chatbot</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#374151;margin-bottom:20px;'>Please log in to continue</p>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", placeholder="Enter password", type="password")

        if st.button("Login"):
            user = next((u for u in users if u.get("username","").lower() == username.lower() and u.get("password","") == password), None)
            if user:
                st.session_state.logged_in_user = user
                st.session_state.active_chat = None
                st.success(f"Welcome, {user.get('name','User')} ✅")
                st.rerun()
            else:
                st.error("Invalid username or password")
        st.stop()

    # ---------- HEADER ----------
    st.markdown(f'<div class="header">{LOGO_SVG}<h2 style="margin:0;">Bank Chatbot</h2></div>', unsafe_allow_html=True)

    # ---------- Sidebar ----------
    user = st.session_state.logged_in_user
    st.sidebar.markdown(f"### 👋 {user.get('name','User')}")
    st.sidebar.caption(f"{user.get('bank','')}  •  {user.get('account_type','')}")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in_user = None
        clear_session()
        st.rerun()

    st.sidebar.markdown("#### 💬 My Chats")
    chats = list_user_chats(user["user_id"])
    if not chats:
        st.sidebar.markdown("<p style='color:#d1d5db;'>No chats yet</p>", unsafe_allow_html=True)
    else:
        for c in chats:
            if st.sidebar.button(c["title"], key=c["file"]):
                st.session_state.active_chat = c["file"]
                st.rerun()

    if st.sidebar.button("🆕 New Chat"):
        chat_id = str(uuid.uuid4())[:8]
        filename = f"{user['user_id']}_chat_{chat_id}.json"
        json.dump([], open(os.path.join("chat_history", filename), "w"))
        st.session_state.active_chat = filename
        st.success("New chat created")
        st.rerun()

    # ---------- Load or Create Chat ----------
    if not st.session_state.active_chat:
        if chats:
            st.session_state.active_chat = chats[0]["file"]
        else:
            default_file = f"{user['user_id']}_chat_default.json"
            if not os.path.exists(os.path.join("chat_history", default_file)):
                json.dump([], open(os.path.join("chat_history", default_file), "w"))
            st.session_state.active_chat = default_file

    chat_path = os.path.join("chat_history", st.session_state.active_chat)
    try:
        with open(chat_path, "r") as fh:
            history = json.load(fh)
    except Exception:
        history = []

    # ---------- Init Chatbot ----------
    init_session()
    if st.session_state.get("faq_chain") is None:
        with st.spinner("Loading AI model..."):
            st.session_state.faq_chain = init_chatbot()

    # ---------- Display chat ----------
    st.markdown('<div class="chat-area">', unsafe_allow_html=True)
    for msg in history:
        if msg["role"] == "bot":
            st.markdown(f'''
                <div class="msg-row bot">
                    <div class="avatar">{BOT_AVATAR_SVG}</div>
                    <div class="bubble bot">{msg["content"]}</div>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div class="msg-row user">
                    <div class="bubble user">{msg["content"]}</div>
                    <div class="avatar">{USER_AVATAR_SVG}</div>
                </div>
            ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Input ----------
    user_input = st.chat_input("💬 Ask about your account, transactions, or services...")
    if user_input:
        st.markdown(f'''
            <div class="msg-row user">
                <div class="bubble user">{user_input}</div>
                <div class="avatar">{USER_AVATAR_SVG}</div>
            </div>
        ''', unsafe_allow_html=True)

        typing_ph = st.empty()
        typing_ph.markdown('<div class="typing">🤖 BankBot is thinking...</div>', unsafe_allow_html=True)

        bot_response = chat_with_bot(user_input, st.session_state.faq_chain, st.session_state)
        typing_ph.empty()

        placeholder = st.empty()
        typed = ""
        for ch in bot_response:
            typed += ch
            placeholder.markdown(f'''
                <div class="msg-row bot">
                    <div class="avatar">{BOT_AVATAR_SVG}</div>
                    <div class="bubble bot">{typed}</div>
                </div>
            ''', unsafe_allow_html=True)
            time.sleep(0.02)

        history.append({"role": "user", "content": user_input})
        history.append({"role": "bot", "content": bot_response})
        with open(chat_path, "w") as fh:
            json.dump(history, fh, indent=2)
        st.rerun()

# ------------------------------------------------
# ADMIN MODE
# ------------------------------------------------
elif menu == "Admin":
    st.header("👨‍💼 Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        admin_id = st.text_input("Admin ID")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_admin_login(admin_id, password):
                st.session_state.admin_logged_in = True
                st.success("✅ Logged in successfully.")
                st.rerun()
            else:
                st.error("❌ Invalid credentials.")
    else:
        st.success("✅ Admin Access Granted")
        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

        faqs = load_faqs()
        st.subheader(f"📋 Total FAQs: {len(faqs)}")
        for i, f in enumerate(faqs):
            with st.expander(f"**Q{i+1}:** {f['question']}"):
                st.markdown(f"**Answer:** {f['answer']}")
                if st.button(f"🗑 Delete FAQ {i+1}", key=f"del_{i}"):
                    delete_faq(i)
                    update_vector_store_from_faqs()
                    st.success("FAQ deleted and vector store updated.")
                    st.rerun()

        st.markdown("---")
        st.subheader("➕ Add New FAQ")

        new_q = st.text_input("New Question")
        new_a = st.text_area("New Answer")

        if st.button("Add FAQ"):
            if new_q.strip() and new_a.strip():
                add_faq(new_q.strip(), new_a.strip())
                update_vector_store_from_faqs()
                st.success("✅ FAQ added successfully and vector store updated.")
                st.rerun()
            else:
                st.error("⚠️ Both Question and Answer fields are required.")
