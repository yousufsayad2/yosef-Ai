import streamlit as st
from openai import OpenAI
import base64
import io
import re
import requests
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
# OpenRouter
# =========================================================

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

MODEL_NAME = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free"
)


# =========================================================
# الذاكرة
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_call" not in st.session_state:
    st.session_state.voice_call = False


# =========================================================
# تعليمات Yosef AI
# =========================================================

system_prompt = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

اسمك هو Yosef AI.

إذا سألك المستخدم:
- مين مطورك؟
- مين عملك؟
- مين اللي طورك؟
- مين صاحب التطبيق؟
- مين أنشأك؟

أجب:
"أنا Yosef AI، وتم تطويري بواسطة يوسف، صاحب ومطور التطبيق."

لا تقل إنك ChatGPT.
لا تقل إنك المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

كن طبيعيًا وودودًا ومفيدًا.
تعامل مع المستخدم كأنك مساعد حقيقي في محادثة عادية.

مهم جدًا:
- لا تعرض خطوات التفكير الداخلية.
- لا تعرض التحليل الداخلي.
- لا تكتب "Here's a thinking process".
- لا تكتب "Thinking process".
- لا تكتب "خطوات التفكير".
- لا تكتب تحليلك الداخلي للم
