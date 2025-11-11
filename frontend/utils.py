import re
import streamlit as st



HEB_RANGE = re.compile(r"[\u0590-\u05FF]")  # Hebrew Unicode block
ENG_RANGE = re.compile(r"[A-Za-z]")


def is_hebrew(text: str) -> bool:
    return bool(re.search(r"[\u0590-\u05FF]", text))

def detect_language(text: str) -> str:
    """
    Detect language of a text (very light heuristic).
    Returns 'he' for Hebrew, 'en' for English, or 'unknown'.
    """
    if not text or not text.strip():
        return "unknown"

    heb = len(HEB_RANGE.findall(text))
    eng = len(ENG_RANGE.findall(text))

    if heb > eng:
        return "he"
    elif eng > heb:
        return "en"
    else:
        return "unknown"

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
