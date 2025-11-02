import re
import streamlit as st

def is_hebrew(text: str) -> bool:
    return bool(re.search(r"[\u0590-\u05FF]", text))

def set_text_direction(text: str):
    if is_hebrew(text):
        st.markdown(
            """
            <style>
            .rtl { direction: rtl; text-align: right; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        return "rtl"
    else:
        st.markdown(
            """
            <style>
            .ltr { direction: ltr; text-align: left; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        return "ltr"
