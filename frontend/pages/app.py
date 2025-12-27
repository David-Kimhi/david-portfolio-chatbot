import streamlit as st, requests, os
from frontend.constants.translator import get_text_value as gtv
import frontend.constants.icons as icons
import json
from frontend.constants.presets import PRESET_QUESTIONS
from frontend.utils import detect_language
from frontend.st_helpers.session_state import SessionStateManager


S = SessionStateManager()


API_URL = os.environ.get("API_URL","http://localhost:8000")
AUTH_URL = f"{API_URL}/auth/login"


S.set_default(S.LANG, 'en')

# sidebar language selector
with st.sidebar:
    selected = st.selectbox(
        gtv('language'),
        ["English", "עברית"],
        index=["en", "he"].index(S.get(S.LANG))  # keep current
    )
    lang = "en" if selected == "English" else "he"

# update session state if changed
if lang != S.get(S.LANG):
    S.set_one(S.LANG, lang)

language = lang

page_title = gtv('app_title')
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




S.set_default(S.CHAT, [])

with st.sidebar:
    st.divider()
    st.subheader(gtv('admin_settings'))

    auth_token = S.get(S.AUTH_TOKEN)
    if not auth_token:
        st.info(gtv('login_prompt'), icon=icons.INFO)
        with st.popover(gtv('login_title')):
            email = st.text_input(gtv('email'))
            password = st.text_input(gtv('password'), type="password")
            if st.button(gtv('login')):
                r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
                if r.ok:
                    S.set_one(S.AUTH_TOKEN, r.json()["access_token"])
                    st.success(gtv('logged_in'), icon=icons.SUCCESS)
                    st.rerun()
                else:
                    st.error(gtv('login_failed'), icon=icons.BLOCK)
    else:
        success_msg = gtv('authenticated')
        st.success(success_msg)
        title = st.text_input(gtv('doc_title'), value=gtv('untitled'))
        url   = st.text_input(gtv('source_url'), value="")
        txt   = st.text_area(gtv('paste_text'), height=150)
        if st.button(gtv('ingest')):
            if not txt.strip():
                st.warning(gtv('no_text'))
            else:
                items = [{"id": title, "text": txt, "meta": {"title": title, "url": url}}]
                r = requests.post(
                    f"{API_URL}/ingest",
                    headers={"Authorization": f"Bearer {S.get(S.AUTH_TOKEN)}"},
                    json=items,
                )
                if r.ok:
                    st.success(gtv('ingested'))
                else:
                    st.error(f"{gtv('ingest_failed')}: {r.status_code}")

        st.divider()
        if st.button(gtv('logout')):
            S.set_one(S.AUTH_TOKEN, None)
            st.rerun()


def stream_translate_from_backend(text: str, target_lang: str):
    """
    Call /trunslate/stream and yield events, just like /ask/stream.
    Each event is a dict with "type": "chunk" | "sources".
    """
    headers = {}
    if S.get(S.AUTH_TOKEN) is not None:
        headers["Authorization"] = f"Bearer {S.get(S.AUTH_TOKEN)}"

    try:
        with requests.post(
            f"{API_URL}/trunslate/stream",
            json={"text": text, "target_lang": target_lang},
            headers=headers,
            stream=True,
            timeout=(5, 60)
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                yield json.loads(line.decode("utf-8"))
                
    except requests.exceptions.Timeout:
        yield {"type": "error", "data": "⏰ Translation request timed out. Try again."}
    except requests.exceptions.RequestException as e:
        yield {"type": "error", "data": f"Translation failed: {e}"}



@st.fragment
def render_history():
    for idx, msg in enumerate(S.get(S.CHAT, [])):
        if msg["role"] == "user":
            st.chat_message("user", avatar="./frontend/assets/user.png").markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="./frontend/assets/assistant.jpg"):
                inner = st.empty()
                inner.markdown(msg['content'])

                # Sources expander (same as before)
                if msg.get("sources"):
                    with st.expander(gtv("sources")):
                        for s in msg["sources"]:
                            if s.get("url"):
                                st.write(f"- [{s.get('title','Source')}]({s['url']})")
                            else:
                                st.write(f"- {s.get('title','Source')}")

                # 🔁 Translate button
                msg_language = detect_language(msg["content"])
                disabled_rule = msg_language == language
                translate_label = gtv("translate_button")

                if not disabled_rule:
                    if st.button(translate_label, key=f"translate_{idx}", use_container_width=False, disabled=disabled_rule):
                        full = ""
                        box = inner
                        error_message = None

                        for event in stream_translate_from_backend(msg["content"], language):
                            etype = event.get("type")
                            if etype == "chunk":
                                full += event.get("data", "")
                                box.markdown(full)
                            elif etype == "error":
                                error_message = event["data"]
                                break  # stop reading more lines

                        if error_message:
                            box.markdown(f"**{error_message}**")
                            # add a quick retry button
                            if st.button("🔁 Try again", key=f"retry_{idx}", use_container_width=False):
                                st.rerun()
                        else:
                            chat = S.get(S.CHAT)
                            chat[idx]["content"] = full
                            st.rerun()


st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        border-radius: 12px;
        height: 40px;
        font-weight: 600;
        white-space: normal;
    }
    </style>
""", unsafe_allow_html=True)

st.title(gtv('ask_title'))
st.markdown(f"##### 💬 {gtv('preset_questions_title')}")

questions = PRESET_QUESTIONS[language]

n_cols = 2
cols = st.columns(n_cols)

for i, q in enumerate(questions):
    with cols[i % n_cols]:
        if st.button(q, use_container_width=True):
            S.set_one(S.USER_QUERY, q)
            st.rerun()


def stream_answer_from_backend(question: str):
    headers = {}

    auth_token = S.get(S.AUTH_TOKEN)
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    with requests.post(
        f"{API_URL}/ask/stream",
        json={"question": question, "top_k": 4},
        headers=headers,
        stream=True,
        timeout=(5, 60)
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

        error_message = None
        for event in stream_answer_from_backend(question):
            if event["type"] == "chunk":
                full += event["data"]
                box.markdown(full)
            elif event["type"] == "sources":
                sources = event["data"]
            elif event["type"] == "error":
                error_message = event["data"]
                break  # stop reading more lines
        
        if error_message:
            box.markdown(f"**{error_message}**")
            # add a quick retry button
            idx_retry = S.get(S.IDX_RETRY, 0)
            S.set_one(S.IDX_RETRY, idx_retry + 1)

            if idx_retry <= 3:
                if st.button("🔁 Try again", key=f"retry_{idx_retry}", use_container_width=False):
                    st.rerun()

        return {"answer": full, "sources": sources}



q = st.chat_input(gtv('chat_placeholder')) or S.get(S.USER_QUERY, None)

if q:
    # 1) clear preset trigger if used
    S.set_one(S.USER_QUERY, None)
    
    # 2) add user to history immediately
    s_chat = S.get(S.CHAT) or []
    s_chat.append({"role": "user", "content": q})
    S.set_one(S.CHAT, s_chat)

    render_history()

    # 3) stream assistant (this does NOT re-render the whole page)
    result = stream_live_assistant(q)

    # 4) add to history
    s_chat.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
        }
    )

    # 5) one small rerun so the assistant message moves
    st.rerun()
else:
    render_history()


