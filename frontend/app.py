import streamlit as st, requests, os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Ask David’s Portfolio", page_icon="💬", layout="wide")
st.title("Ask David’s Portfolio")

if "chat" not in st.session_state: st.session_state.chat = []

q = st.chat_input("Ask about experience, projects, stack…")
if q:
    st.session_state.chat.append(("user", q))
    r = requests.post(f"{API_URL}/ask", json={"question": q, "top_k": 4}).json()
    st.session_state.chat.append(("assistant", r))

for role, content in st.session_state.chat:
    if role == "user":
        st.chat_message("user").markdown(content)
    else:
        st.chat_message("assistant").markdown(content["answer"])
        with st.expander("Sources"):
            for s in content.get("sources", []):
                title = s.get("title","Source")
                url = s.get("url","#")
                st.write(f"- [{title}]({url})")
