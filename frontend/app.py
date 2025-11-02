import streamlit as st, requests, os
from utils import set_text_direction
from translator import CONSTANTS
import icons
import json
from presets import PRESET_QUESTIONS


API_URL = os.environ.get("API_URL","http://localhost:8000")
AUTH_URL = f"{API_URL}/auth/login"

if "lang" not in st.session_state:
    st.session_state.lang = "en"  

# sidebar language selector
with st.sidebar:
    selected = st.selectbox(
        CONSTANTS['language'][st.session_state.lang],
        ["English", "עברית"],
        index=["en", "he"].index(st.session_state.lang)  # keep current
    )
    lang = "en" if selected == "English" else "he"

# update session state if changed
if lang != st.session_state.lang:
    st.session_state.lang = lang

language = st.session_state.get('lang', 'en')


page_title = CONSTANTS['app_title'][language]
st.set_page_config(page_title=page_title, page_icon="💬", layout="wide")

if language == 'he':
    st.markdown("""
    <style>
    /* global rtl for hebrew */
    html, body, [class*="css"]  {
        direction: rtl;
        text-align: right;
    }

    /* =========================
       1) EXPANDER HEADER (arrow)
       ========================= */
    /* the button that is the expander header */
    div[data-testid="stExpander"] > details > summary {
        flex-direction: row-reverse !important;   /* put arrow on the LEFT */
        justify-content: space-between !important;
    }

    /* some streamlit versions wrap it differently: */
    div[data-testid="stExpander"] button {
        flex-direction: row-reverse !important;
        justify-content: space-between !important;
    }

    /* also flip the icon itself if needed */
    div[data-testid="stExpander"] svg {
        transform: scaleX(-1);
    }

    /* make the content rtl too */
    div[data-testid="stExpander"] * {
        direction: rtl !important;
        text-align: right !important;
    }

    /* =========================
       2) CHAT INPUT BAR
       ========================= */
    /* the outer chat-input container is flex LTR – flip it */
    div[data-testid="stChatInput"] {
        direction: rtl !important;
    }
    /* inner flex row: icon + textarea -> reverse */
    div[data-testid="stChatInput"] > div {
        display: flex;
        flex-direction: row-reverse !important;
        align-items: center;
        gap: 0.5rem;
    }
    /* make the textarea rtl */
    div[data-testid="stChatInput"] textarea {
        direction: rtl !important;
        text-align: right !important;
    }

    /* sometimes the send button/icon is another div – flip it too */
    div[data-testid="stChatInput"] button,
    div[data-testid="stChatInput"] svg {
        direction: rtl !important;
    }

    /* =========================
       3) CHAT MESSAGES
       ========================= */
    div[data-testid="stChatMessageContent"] {
        direction: rtl !important;
        text-align: right !important;
    }
    </style>
    """, unsafe_allow_html=True)


if "chat" not in st.session_state:
    # list of dicts: {"role": "user"|"assistant", "content": "...", "sources": [...]}
    st.session_state.chat = []

API_URL = os.environ.get("API_URL", "http://localhost:8000")

with st.sidebar:
    st.divider()
    st.subheader(CONSTANTS['admin_settings'][language])

    if "auth_token" not in st.session_state:
        st.info(CONSTANTS['login_prompt'][language], icon=icons.INFO)
        email = st.text_input(CONSTANTS['email'][language])
        password = st.text_input(CONSTANTS['password'][language], type="password")
        if st.button(CONSTANTS['login'][language]):
            r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
            if r.ok:
                st.session_state["auth_token"] = r.json()["access_token"]
                st.success(CONSTANTS['logged_in'][language], icon=icons.SUCCESS)
                st.rerun()
            else:
                st.error(CONSTANTS['login_failed'][language], icon=icons.BLOCK)
    else:
        success_msg = CONSTANTS['authenticated'][language]
        st.success(success_msg)
        title = st.text_input(CONSTANTS['doc_title'][language], value=CONSTANTS['untitled'][language])
        url   = st.text_input(CONSTANTS['source_url'][language], value="")
        txt   = st.text_area(CONSTANTS['paste_text'][language], height=150)
        if st.button(CONSTANTS['ingest'][language]):
            if not txt.strip():
                st.warning(CONSTANTS['no_text'][language])
            else:
                items = [{"id": title, "text": txt, "meta": {"title": title, "url": url}}]
                r = requests.post(
                    f"{API_URL}/ingest",
                    headers={"Authorization": f"Bearer {st.session_state['auth_token']}"},
                    json=items,
                )
                if r.ok:
                    st.success(CONSTANTS['ingested'][language])
                else:
                    st.error(f"{CONSTANTS['ingest_failed'][language]}: {r.status_code}")

        st.divider()
        if st.button(CONSTANTS['logout'][language]):
            del st.session_state["auth_token"]
            st.rerun()


@st.fragment
def render_history():
    for msg in st.session_state.chat:
        if msg["role"] == "user":
            st.chat_message("user", avatar="./frontend/assets/user.png").markdown(msg["content"])
        else:
           with st.chat_message("assistant", avatar="./frontend/assets/assistant.jpg"):
                inner = st.empty()
                direction_class = set_text_direction(msg["content"])
                inner.markdown(f"<div class='{direction_class}'>{msg['content']}</div>", unsafe_allow_html=True)

                if msg.get("sources"):
                    with st.expander(CONSTANTS["sources"][language]):
                        for s in msg["sources"]:
                            if s.get("url"):
                                st.write(f"- [{s.get('title','Source')}]({s['url']})")
                            else:
                                st.write(f"- {s.get('title','Source')}")


st.title(CONSTANTS['ask_title'][language])

st.markdown(f"#### 💬 {CONSTANTS['preset_questions_title'][language]}")

for q in PRESET_QUESTIONS[language]:
    if st.button(f"👉 {q}", use_container_width=True):
        st.session_state["user_query"] = q
        st.rerun()

render_history()


def stream_answer_from_backend(question: str):
    headers = {}
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['auth_token']}"
    with requests.post(
        f"{API_URL}/ask/stream",
        json={"question": question, "top_k": 4},
        headers=headers,
        stream=True,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            yield json.loads(line.decode("utf-8"))


@st.fragment
def stream_live_assistant(question: str):
    with st.chat_message("assistant", avatar="./frontend/assets/assistant.jpg"):
        box = st.empty()
        full = ""
        sources = []

        for event in stream_answer_from_backend(question):
            if event["type"] == "chunk":
                full += event["data"]
                box.markdown(full)
            elif event["type"] == "sources":
                sources = event["data"]

        # IMPORTANT: don't render expander here
        return {"answer": full, "sources": sources}



if "chat" not in st.session_state:
    st.session_state.chat = []

q = st.chat_input(CONSTANTS['chat_placeholder'][language]) or st.session_state.get("user_query")

if q:
    # 1) add user to history immediately
    st.session_state.chat.append({"role": "user", "content": q})

    # 2) stream assistant (this does NOT re-render the whole page)
    result = stream_live_assistant(q)

    # 3) now that we have final text → add to history
    st.session_state.chat.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
        }
    )

    # 4) clear preset trigger if used
    st.session_state.pop("user_query", None)

    # 5) one small rerun so the assistant message moves
    st.rerun()



