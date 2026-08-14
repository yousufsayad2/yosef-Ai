import streamlit as st
from openai import OpenAI
import base64
import re
import requests
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
    """
    <style>

    .yosef-title {
        text-align: center;
        font-size: 34px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 8px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 25px;
        font-size: 16px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# OpenRouter
# =========================================================

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
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

عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

كن طبيعيًا وودودًا ومفيدًا.

في المحادثة الصوتية:
- تحدث بطريقة طبيعية.
- اجعل الرد واضحًا ومختصرًا.
- تعامل مع المستخدم كأنه يتحدث مع مساعد صوتي.
- لا تبدأ كل رد بمقدمات طويلة.

إذا تم إعطاؤك معلومات من البحث على الإنترنت:
- استخدم المعلومات المتاحة.
- لا تخترع معلومات غير موجودة.
- إذا كانت المعلومات غير كافية، وضح ذلك.
- لا تذكر تفاصيل البحث الداخلية للمستخدم إلا إذا طلبها.
"""


# =========================================================
# العنوان
# =========================================================

st.markdown(
    '<div class="yosef-title">🤖 Yosef AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<
