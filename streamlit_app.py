import streamlit as st
from openai import OpenAI
import io
import speech_recognition as sr


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    "<style>"
    ".yosef-title {"
    "text-align: center;"
    "font-size: 34
