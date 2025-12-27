import streamlit as st


class SessionStateManager:
    IDX_RETRY = "idx_retry"
    CHAT = "chat"
    USER_QUERY = "user_query"
    AUTH_TOKEN = "auth_token"
    LANG = "lang"
    
    LINKEDIN_AUTH_STATE = "linkedin_auth_state"
    LINKEDIN_REDIRECT_URI = "linkedin_redirect_uri"
    LINKEDIN_ACCESS_TOKEN = "linkedin_access_token"


    def __init__(self):
        for name, value in self.__class__.__dict__.items():
            if not name.startswith("__") and not callable(value):
                if value not in st.session_state:
                    st.session_state[value] = None

    def get(self, key, default=None):
        return st.session_state.get(key, default)
    
    def set_one(self, key, value):
        if key not in st.session_state:
            raise KeyError(f"Key '{key}' not in session_state")
        
        st.session_state[key] = value

    def set_many(self, **kwargs):
        for k, v in kwargs.items():
            if k not in st.session_state:
                raise KeyError(f"Key '{k}' not in session_state")
            
            st.session_state[k] = v
    
    def set_default(self, key, default):
        if key not in st.session_state:
            raise KeyError(f"Key '{key}' not in session_state")
        
        if st.session_state[key] is None:
            st.session_state[key] = default