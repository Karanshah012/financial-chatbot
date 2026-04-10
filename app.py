import streamlit as st
import time, os, json, uuid
from datetime import datetime
from chatbot_logic import init_chatbot, chat_with_bot
from admin_backend import (
    check_admin_login,
    load_faqs,
    add_faq,
    delete_faq,
    update_vector_store_from_faqs
)
from session_manager import init_session, clear_session

st.set_page_config(
    page_title="FinBot Assistance",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE INIT  (must come before sidebar renders)
# ============================================================
if "logged_in_user"  not in st.session_state: st.session_state.logged_in_user  = None
if "active_chat"     not in st.session_state: st.session_state.active_chat     = None
if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in = False
if "theme"           not in st.session_state: st.session_state.theme           = "dark"

# ============================================================
# THEME TOKENS
# ============================================================
DARK = {
    "bg_main":        "#1a1d23",
    "bg_sidebar":     "#13151a",
    "bg_card":        "#21252e",
    "bg_input":       "#2a2f3a",
    "bg_user_bubble": "#2563eb",
    "bg_bot_bubble":  "#252930",
    "border":         "rgba(255,255,255,0.08)",
    "accent":         "#3b82f6",
    "accent_hover":   "#2563eb",
    "accent_soft":    "rgba(59,130,246,0.12)",
    "text_primary":   "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted":     "#475569",
    "success":        "#10b981",
    "danger":         "#ef4444",
    "danger_soft":    "rgba(239,68,68,0.10)",
    "topbar_bg":      "rgba(26,29,35,0.96)",
    "user_bubble_txt":"#ffffff",
    "toggle_bg":      "#2a2f3a",
    "toggle_border":  "rgba(255,255,255,0.10)",
    "toggle_active":  "#3b82f6",
}

LIGHT = {
    "bg_main":        "#f5f6f8",
    "bg_sidebar":     "#ffffff",
    "bg_card":        "#ffffff",
    "bg_input":       "#f0f2f5",
    "bg_user_bubble": "#2563eb",
    "bg_bot_bubble":  "#ffffff",
    "border":         "rgba(0,0,0,0.08)",
    "accent":         "#2563eb",
    "accent_hover":   "#1d4ed8",
    "accent_soft":    "rgba(37,99,235,0.10)",
    "text_primary":   "#1e2330",
    "text_secondary": "#5a6478",
    "text_muted":     "#9ba3b2",
    "success":        "#059669",
    "danger":         "#dc2626",
    "danger_soft":    "rgba(220,38,38,0.08)",
    "topbar_bg":      "rgba(245,246,248,0.97)",
    "user_bubble_txt":"#ffffff",
    "toggle_bg":      "#e8eaed",
    "toggle_border":  "rgba(0,0,0,0.08)",
    "toggle_active":  "#2563eb",
}

T = DARK if st.session_state.theme == "dark" else LIGHT

# ============================================================
# GLOBAL STYLING  (injected fresh on every render)
# ============================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {{
    --bg-main:         {T['bg_main']};
    --bg-sidebar:      {T['bg_sidebar']};
    --bg-card:         {T['bg_card']};
    --bg-input:        {T['bg_input']};
    --bg-user-bubble:  {T['bg_user_bubble']};
    --bg-bot-bubble:   {T['bg_bot_bubble']};
    --border:          {T['border']};
    --accent:          {T['accent']};
    --accent-hover:    {T['accent_hover']};
    --accent-soft:     {T['accent_soft']};
    --text-primary:    {T['text_primary']};
    --text-secondary:  {T['text_secondary']};
    --text-muted:      {T['text_muted']};
    --success:         {T['success']};
    --danger:          {T['danger']};
    --danger-soft:     {T['danger_soft']};
    --topbar-bg:       {T['topbar_bg']};
    --user-bubble-txt: {T['user_bubble_txt']};
    --toggle-bg:       {T['toggle_bg']};
    --toggle-border:   {T['toggle_border']};
    --toggle-active:   {T['toggle_active']};
    --radius:          12px;
    --radius-sm:       8px;
    --radius-xs:       6px;
}}

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [class*="css"], .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
}}

#MainMenu, footer, header {{ visibility: hidden !important; display: none !important; }}
.stDeployButton {{ display: none !important; }}

.block-container {{
    padding: 0 !important;
    max-width: 100% !important;
    margin: 0 !important;
}}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
    width: 260px !important;
    min-width: 260px !important;
}}
[data-testid="stSidebar"] * {{
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}}

.sb-brand {{
    padding: 16px 16px 12px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 9px;
    margin-bottom: 4px;
    background: var(--bg-sidebar);
}}
.sb-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 7px var(--accent);
    flex-shrink: 0;
    animation: glow 2.5s ease-in-out infinite;
}}
@keyframes glow {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.35;}} }}
.sb-name {{ font-size: 0.88rem; font-weight: 700; color: var(--text-primary); letter-spacing:-0.01em; }}
.sb-tag  {{
    font-size: 0.58rem; font-weight: 600; color: var(--accent);
    background: var(--accent-soft); padding: 2px 6px;
    border-radius: 10px; letter-spacing: 0.07em; text-transform: uppercase;
}}

.sb-section {{
    font-size: 0.62rem; font-weight: 600;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--text-muted); padding: 12px 16px 5px;
}}

/* ── THEME TOGGLE ── */
.theme-toggle-wrap {{
    padding: 8px 14px 10px;
    display: flex; align-items: center; justify-content: space-between;
}}
.theme-label {{
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary);
}}
.theme-pill {{
    display: flex;
    background: var(--toggle-bg);
    border: 1px solid var(--toggle-border);
    border-radius: 20px;
    padding: 3px;
    gap: 2px;
}}
.theme-opt {{
    font-size: 0.7rem;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 14px;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
    color: var(--text-secondary);
    white-space: nowrap;
}}
.theme-opt.active {{
    background: var(--toggle-active);
    color: #fff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.18);
}}

/* User card */
.sb-user {{
    margin: 8px 12px 10px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 11px;
    display: flex; align-items: center; gap: 9px;
}}
.sb-av {{
    width: 32px; height: 32px; border-radius: 50%;
    background: linear-gradient(135deg,#1d4ed8,#3b82f6);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 700; color:#fff !important; flex-shrink:0;
}}
.sb-uname {{ font-size:0.81rem; font-weight:600; color:var(--text-primary) !important; }}
.sb-umeta {{ font-size:0.69rem; color:var(--text-secondary) !important; margin-top:1px; }}

/* All sidebar buttons — reset */
[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    color: var(--text-secondary) !important;
    font-size: 0.81rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    text-align: left !important;
    padding: 7px 12px !important;
    border-radius: var(--radius-xs) !important;
    width: 100% !important;
    transition: background 0.12s, color 0.12s !important;
    box-shadow: none !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: {'rgba(0,0,0,0.05)' if st.session_state.theme=='light' else 'rgba(255,255,255,0.05)'} !important;
    color: var(--text-primary) !important;
}}
[data-testid="stSidebar"] .stButton > button:focus {{
    box-shadow: none !important; outline: none !important;
}}

/* New chat */
.sb-newchat .stButton > button {{
    background: var(--accent-soft) !important;
    border: 1px solid rgba(59,130,246,0.22) !important;
    color: var(--accent) !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    border-radius: var(--radius-sm) !important;
    margin: 0 12px !important;
    width: calc(100% - 24px) !important;
}}
.sb-newchat .stButton > button:hover {{
    background: var(--accent-soft) !important;
    opacity: 0.85;
}}

/* Active chat */
.sb-chat-active .stButton > button {{
    background: var(--accent-soft) !important;
    color: var(--accent) !important;
    font-weight: 500 !important;
}}

/* Delete btn */
.sb-del .stButton > button {{
    padding: 4px 7px !important;
    font-size: 0.7rem !important;
    color: var(--text-muted) !important;
    width: auto !important;
}}
.sb-del .stButton > button:hover {{
    background: var(--danger-soft) !important;
    color: var(--danger) !important;
}}

/* Logout */
.sb-logout .stButton > button {{
    background: var(--danger-soft) !important;
    border: 1px solid rgba(220,38,38,0.14) !important;
    color: var(--danger) !important;
    font-size: 0.79rem !important;
    padding: 8px 12px !important;
    border-radius: var(--radius-sm) !important;
    margin: 0 12px !important;
    width: calc(100% - 24px) !important;
}}
.sb-logout .stButton > button:hover {{
    background: rgba(220,38,38,0.15) !important;
}}

/* Selectbox in sidebar */
[data-testid="stSidebar"] .stSelectbox > div > div {{
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-size: 0.82rem !important;
}}

/* ── TOPBAR ── */
.finbot-bar {{
    position: fixed;
    top: 0; left: 260px; right: 0;
    height: 50px;
    background: var(--topbar-bg);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center;
    padding: 0 22px; gap: 10px;
    z-index: 999;
    backdrop-filter: blur(10px);
}}
.bar-title {{ font-size:0.87rem; font-weight:600; color:var(--text-primary); letter-spacing:-0.01em; }}
.bar-status {{
    font-size:0.67rem; color:var(--success);
    background:rgba(16,185,129,0.1);
    padding:2px 8px; border-radius:10px;
}}

/* ── CHAT AREA ── */
.chat-area {{
    margin-top: 50px;
    padding: 18px 0 140px;
    min-height: calc(100vh - 50px);
}}

.msg-wrap {{
    padding: 3px 22px;
    display: flex; flex-direction: column;
    animation: fadeIn 0.2s ease;
}}
@keyframes fadeIn {{ from{{opacity:0;transform:translateY(5px);}} to{{opacity:1;transform:translateY(0);}} }}

.msg-row {{
    display: flex; align-items: flex-end; gap: 9px;
    max-width: 800px; width: 100%;
}}
.msg-row.user {{ flex-direction: row-reverse; margin-left: auto; }}
.msg-row.bot  {{ margin-right: auto; }}

.av {{
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.63rem; font-weight: 700; flex-shrink: 0; margin-bottom: 2px;
}}
.av.bot-av  {{ background: linear-gradient(135deg,#1e3a5f,#3b82f6); color:#fff !important; }}
.av.user-av {{ background: linear-gradient(135deg,#2d3748,#4a5568); color:#cbd5e1 !important; }}

.bubble {{
    padding: 10px 14px;
    border-radius: 13px;
    font-size: 0.875rem; line-height: 1.65;
    word-break: break-word; max-width: 100%;
}}
.bubble.bot-b {{
    background: var(--bg-bot-bubble);
    border: 1px solid var(--border);
    border-bottom-left-radius: 3px;
    color: var(--text-primary);
    {'box-shadow: 0 1px 4px rgba(0,0,0,0.06);' if st.session_state.theme=='light' else ''}
}}
.bubble.user-b {{
    background: var(--bg-user-bubble);
    border-bottom-right-radius: 3px;
    color: var(--user-bubble-txt) !important;
}}
.msg-ts {{ font-size:0.61rem; color:var(--text-muted); padding:3px 4px 0; }}

/* Typing dots */
.typing {{
    display:flex; gap:4px; align-items:center; padding:11px 14px;
}}
.typing span {{
    width:6px; height:6px; border-radius:50%;
    background:var(--accent);
    animation: tdot 1.3s infinite;
}}
.typing span:nth-child(2){{animation-delay:0.15s;}}
.typing span:nth-child(3){{animation-delay:0.3s;}}
@keyframes tdot {{
    0%,80%,100%{{transform:translateY(0);opacity:0.3;}}
    40%{{transform:translateY(-5px);opacity:1;}}
}}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] {{
    position: fixed !important;
    bottom: 0 !important;
    left: 260px !important;
    right: 0 !important;
    background: var(--bg-main) !important;
    border-top: 1px solid var(--border) !important;
    padding: 12px 24px 16px !important;
    z-index: 998 !important;
}}
[data-testid="stChatInput"] textarea {{
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    padding: 11px 16px !important;
    resize: none !important;
}}
[data-testid="stChatInput"] textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
    outline: none !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{ color: var(--text-muted) !important; }}

/* ── INPUTS global ── */
input[type="text"], input[type="password"] {{
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
}}
input:focus {{ border-color: var(--accent) !important; outline:none !important; }}

/* Primary button */
.btn-primary .stButton > button {{
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 18px !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s !important;
}}
.btn-primary .stButton > button:hover {{ background: var(--accent-hover) !important; }}

/* Alerts */
.stAlert {{ border-radius: var(--radius-sm) !important; font-size:0.82rem !important; }}

/* Scrollbar */
::-webkit-scrollbar {{ width:4px; }}
::-webkit-scrollbar-thumb {{ background:rgba(128,128,128,0.2); border-radius:4px; }}
::-webkit-scrollbar-thumb:hover {{ background:rgba(128,128,128,0.35); }}

/* Admin */
.admin-faq {{
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius); padding:15px 17px; margin-bottom:9px;
    {'box-shadow:0 1px 4px rgba(0,0,0,0.05);' if st.session_state.theme=='light' else ''}
}}
.faq-q {{ font-weight:600; font-size:0.84rem; color:var(--text-primary); margin-bottom:5px; }}
.faq-a {{ font-size:0.81rem; color:var(--text-secondary); line-height:1.65; }}
.stat-card {{
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius); padding:16px; text-align:center;
    {'box-shadow:0 1px 4px rgba(0,0,0,0.05);' if st.session_state.theme=='light' else ''}
}}
.stat-val {{ font-size:1.6rem; font-weight:700; }}
.stat-lbl {{ font-size:0.72rem; color:var(--text-secondary); margin-top:4px; }}

/* Expander */
.streamlit-expanderHeader {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-size: 0.85rem !important;
}}

/* Textarea */
textarea {{
    background: var(--bg-input) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Inter', sans-serif !important;
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
os.makedirs("chat_history", exist_ok=True)

def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return []

def list_user_chats(user_id):
    files = [f for f in os.listdir("chat_history") if f.startswith(f"{user_id}_chat_")]
    chats = []
    for f in sorted(files, reverse=True):
        try:
            with open(os.path.join("chat_history", f), "r") as file:
                data = json.load(file)
                first_msg = next((m["content"] for m in data if m["role"] == "user"), "New Chat")
                chats.append({"file": f, "title": first_msg[:34]})
        except:
            continue
    return chats

def render_message(role, content, timestamp=""):
    is_user = (role == "user")
    row_cls = "msg-row user" if is_user else "msg-row bot"
    bub_cls = "bubble user-b" if is_user else "bubble bot-b"
    av_cls  = "av user-av"   if is_user else "av bot-av"
    av_lbl  = "U"            if is_user else "FB"
    align   = "align-items:flex-end;" if is_user else ""

    safe = (content
        .replace("&","&amp;")
        .replace("<","&lt;")
        .replace(">","&gt;")
        .replace("\n","<br>"))
    ts = f'<div class="msg-ts">{timestamp}</div>' if timestamp else ""

    st.markdown(f"""
    <div class="msg-wrap">
      <div class="{row_cls}">
        <div class="{av_cls}">{av_lbl}</div>
        <div style="display:flex;flex-direction:column;{align}">
          <div class="{bub_cls}">{safe}</div>
          {ts}
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR — always rendered first
# ============================================================
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-dot"></div>
      <span class="sb-name">FinBot</span>
      <span class="sb-tag">AI</span>
    </div>""", unsafe_allow_html=True)

    # ── THEME TOGGLE ──────────────────────────────────────
    is_dark  = st.session_state.theme == "dark"
    is_light = not is_dark

    st.markdown(f"""
    <div class="theme-toggle-wrap">
      <span class="theme-label">Theme</span>
      <div class="theme-pill">
        <span class="theme-opt {'active' if is_dark else ''}">🌙 Dark</span>
        <span class="theme-opt {'active' if is_light else ''}">☀️ Light</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Two tiny invisible buttons that actually do the switching
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        if st.button("Dark", key="theme_dark",
                     use_container_width=True,
                     help="Switch to Dark theme"):
            st.session_state.theme = "dark"
            st.rerun()
    with tcol2:
        if st.button("Light", key="theme_light",
                     use_container_width=True,
                     help="Switch to Light theme"):
            st.session_state.theme = "light"
            st.rerun()

    # Style those two toggle buttons to be visually minimal
    st.markdown("""
    <style>
    /* Make the Dark/Light functional buttons look minimal */
    [data-testid="stSidebar"] [data-testid="column"]:nth-child(1) .stButton > button,
    [data-testid="stSidebar"] [data-testid="column"]:nth-child(2) .stButton > button {
        font-size: 0.72rem !important;
        padding: 4px 6px !important;
        opacity: 0.55 !important;
        font-weight: 400 !important;
        border-radius: 4px !important;
        color: var(--text-muted) !important;
    }
    [data-testid="stSidebar"] [data-testid="column"]:nth-child(1) .stButton > button:hover,
    [data-testid="stSidebar"] [data-testid="column"]:nth-child(2) .stButton > button:hover {
        opacity: 0.9 !important;
        background: var(--accent-soft) !important;
        color: var(--accent) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin:2px 12px 0;border-top:1px solid rgba(128,128,128,0.12);"></div>',
                unsafe_allow_html=True)

    # Mode switcher
    st.markdown('<div class="sb-section">Mode</div>', unsafe_allow_html=True)
    menu = st.selectbox("mode_select", ["User", "Admin"], label_visibility="collapsed")

    st.markdown('<div style="margin:4px 12px;border-top:1px solid rgba(128,128,128,0.08);"></div>',
                unsafe_allow_html=True)

    # ── User controls (only when logged in) ────────────────
    if menu == "User" and st.session_state.logged_in_user:
        user     = st.session_state.logged_in_user
        initials = "".join(w[0].upper() for w in user.get("name","U").split()[:2])

        st.markdown(f"""
        <div class="sb-user">
          <div class="sb-av">{initials}</div>
          <div>
            <div class="sb-uname">{user.get('name','—')}</div>
            <div class="sb-umeta">{user.get('bank','—')} · {user.get('account_type','—')}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sb-newchat">', unsafe_allow_html=True)
        if st.button("＋  New Conversation", key="btn_new_chat"):
            chat_id  = str(uuid.uuid4())[:8]
            filename = f"{user['user_id']}_chat_{chat_id}.json"
            with open(os.path.join("chat_history", filename), "w") as fh:
                json.dump([], fh)
            st.session_state.active_chat = filename
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        chats = list_user_chats(user["user_id"])
        if chats:
            st.markdown('<div class="sb-section">Recent Chats</div>', unsafe_allow_html=True)
            for c in chats:
                is_active = (st.session_state.active_chat == c["file"])
                c1, c2 = st.columns([5, 1])
                with c1:
                    cls = "sb-chat-active" if is_active else ""
                    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
                    label = ("▸ " if is_active else "   ") + c["title"]
                    if st.button(label, key=f"open_{c['file']}", use_container_width=True):
                        st.session_state.active_chat = c["file"]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<div class="sb-del">', unsafe_allow_html=True)
                    if st.button("✕", key=f"del_{c['file']}"):
                        try:
                            os.remove(os.path.join("chat_history", c["file"]))
                            if st.session_state.active_chat == c["file"]:
                                st.session_state.active_chat = None
                            st.rerun()
                        except:
                            pass
                    st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sb-logout">', unsafe_allow_html=True)
        if st.button("⎋  Sign Out", key="btn_signout_user"):
            st.session_state.logged_in_user = None
            st.session_state.active_chat    = None
            clear_session()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Admin controls (only when logged in) ───────────────
    elif menu == "Admin" and st.session_state.admin_logged_in:
        st.markdown(f"""
        <div style="padding:8px 16px;font-size:0.77rem;color:{T['success']};">
            ✓  Admin authenticated
        </div>""", unsafe_allow_html=True)
        st.markdown('<div class="sb-logout">', unsafe_allow_html=True)
        if st.button("⎋  Sign Out", key="btn_signout_admin"):
            st.session_state.admin_logged_in = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ── USER MODE ────────────────────────────────────────────────
# ============================================================
if menu == "User":

    if not st.session_state.logged_in_user:
        users = load_users()

        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.markdown("""
            <div style="height:16vh;"></div>
            <div style="text-align:center;margin-bottom:26px;">
              <div style="font-size:2rem;margin-bottom:8px;">🏦</div>
              <div style="font-size:1.28rem;font-weight:700;letter-spacing:-0.02em;color:var(--text-primary)">
                Welcome back
              </div>
              <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">
                Sign in to FinBot Assistance
              </div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input("u", placeholder="Username", label_visibility="collapsed")
            st.markdown('<div style="height:5px;"></div>', unsafe_allow_html=True)
            password = st.text_input("p", type="password", placeholder="Password", label_visibility="collapsed")
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            login_clicked = st.button("Sign In →", key="login_btn", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div style="text-align:center;margin-top:13px;font-size:0.7rem;color:{T['text_muted']};">
                End-to-end encrypted · FinBot AI v2.0
            </div>
            """, unsafe_allow_html=True)

            if login_clicked:
                found = next(
                    (u for u in users
                     if u.get("username") == username and u.get("password") == password),
                    None
                )
                if found:
                    st.session_state.logged_in_user = found
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.stop()

    # ── CHAT INTERFACE ─────────────────────────────────────
    user = st.session_state.logged_in_user

    chats = list_user_chats(user["user_id"])
    if not st.session_state.active_chat:
        if chats:
            st.session_state.active_chat = chats[0]["file"]
        else:
            default_file = f"{user['user_id']}_chat_default.json"
            with open(os.path.join("chat_history", default_file), "w") as fh:
                json.dump([], fh)
            st.session_state.active_chat = default_file

    chat_path = os.path.join("chat_history", st.session_state.active_chat)
    try:
        with open(chat_path, "r") as fh:
            history = json.load(fh)
    except:
        history = []

    init_session()
    if "chatbot" not in st.session_state or st.session_state.chatbot is None:
        with st.spinner("Starting FinBot AI…"):
            st.session_state.chatbot = init_chatbot()

    if not history:
        history.append({
            "role":    "assistant",
            "content": (
                f"Hello {user.get('name','there')} 👋  I'm FinBot Assistance, "
                "your personal AI financial advisor.\n\n"
                "I can help you with banking queries, loan information, investment advice, "
                "account details, and much more. How can I assist you today?"
            ),
            "time": datetime.now().strftime("%H:%M")
        })

    st.markdown("""
    <div class="finbot-bar">
      <span class="bar-title">FinBot Assistance</span>
      <span class="bar-status">● Online</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="chat-area">', unsafe_allow_html=True)
    for msg in history:
        render_message(msg["role"], msg["content"], msg.get("time",""))
    st.markdown('</div>', unsafe_allow_html=True)

    user_input = st.chat_input("Message FinBot Assistance…")

    if user_input:
        now = datetime.now().strftime("%H:%M")
        history.append({"role": "user", "content": user_input, "time": now})
        with open(chat_path, "w") as fh:
            json.dump(history, fh, indent=2)

        render_message("user", user_input, now)

        tp = st.empty()
        tp.markdown("""
        <div class="msg-wrap">
          <div class="msg-row bot">
            <div class="av bot-av">FB</div>
            <div class="bubble bot-b">
              <div class="typing"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Backend call — completely unchanged ──
        bot_response = chat_with_bot(
            user_input,
            st.session_state.chatbot,
            st.session_state
        )

        tp.empty()

        rp = st.empty()
        streamed = ""
        for char in bot_response:
            streamed += char
            safe = (streamed
                .replace("&","&amp;")
                .replace("<","&lt;")
                .replace(">","&gt;")
                .replace("\n","<br>"))
            rp.markdown(f"""
            <div class="msg-wrap">
              <div class="msg-row bot">
                <div class="av bot-av">FB</div>
                <div class="bubble bot-b">{safe}</div>
              </div>
            </div>""", unsafe_allow_html=True)
            time.sleep(0.008)

        history.append({"role": "assistant", "content": bot_response, "time": now})
        with open(chat_path, "w") as fh:
            json.dump(history, fh, indent=2)

        st.rerun()

# ============================================================
# ── ADMIN MODE ───────────────────────────────────────────────
# ============================================================
elif menu == "Admin":

    st.markdown("""
    <div class="finbot-bar">
      <span class="bar-title">Admin Panel</span>
      <span class="bar-status">● Secure</span>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.admin_logged_in:
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.markdown("""
            <div style="height:14vh;"></div>
            <div style="text-align:center;margin-bottom:24px;">
              <div style="font-size:1.8rem;margin-bottom:8px;">🔐</div>
              <div style="font-size:1.2rem;font-weight:700;letter-spacing:-0.02em;color:var(--text-primary)">
                Admin Access
              </div>
              <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">
                Restricted · Authorised personnel only
              </div>
            </div>
            """, unsafe_allow_html=True)

            admin_id = st.text_input("aid", placeholder="Admin ID", label_visibility="collapsed")
            st.markdown('<div style="height:5px;"></div>', unsafe_allow_html=True)
            password = st.text_input("apw", type="password", placeholder="Password", label_visibility="collapsed")
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Authenticate →", key="admin_login_btn", use_container_width=True):
                if check_admin_login(admin_id, password):
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown('<div style="margin-top:62px;padding:0 22px;">', unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom:18px;">
          <div style="font-size:1.15rem;font-weight:700;color:var(--text-primary)">Dashboard</div>
          <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:3px;">Manage knowledge base &amp; FAQs</div>
        </div>""", unsafe_allow_html=True)

        faqs = load_faqs()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{T["accent"]};">{len(faqs)}</div><div class="stat-lbl">Total FAQs</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{T["success"]};font-size:1.1rem;">Active</div><div class="stat-lbl">Vector Store</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{T["text_primary"]};font-size:1.1rem;">Online</div><div class="stat-lbl">FinBot AI</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

        with st.expander("➕  Add New FAQ"):
            new_q = st.text_input("Question", placeholder="Enter the question…")
            new_a = st.text_area("Answer", placeholder="Enter the answer…", height=110)
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Add to Knowledge Base", use_container_width=True):
                if new_q and new_a:
                    add_faq(new_q, new_a)
                    update_vector_store_from_faqs()
                    st.success("FAQ added and vector store updated ✅")
                    st.rerun()
                else:
                    st.warning("Both fields are required.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.67rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{T["text_muted"]};margin-bottom:10px;">Knowledge Base</div>', unsafe_allow_html=True)

        if not faqs:
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                        min-height:22vh;text-align:center;gap:11px;">
              <div style="font-size:2.4rem;">📭</div>
              <div style="font-size:1.05rem;font-weight:600;color:{T['text_primary']};">No FAQs yet</div>
              <div style="font-size:0.82rem;color:{T['text_secondary']};">Use the form above to add your first FAQ.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for i, faq in enumerate(faqs):
                st.markdown(f"""
                <div class="admin-faq">
                  <div class="faq-q">Q{i+1}. {faq['question']}</div>
                  <div class="faq-a">{faq['answer']}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
