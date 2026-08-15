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

system_prompt = (
    "أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.\n\n"
    "اسمك هو Yosef AI.\n\n"

    "إذا سألك المستخدم: مين مطورك؟ أو مين عملك؟ أو مين طورك؟ "
    "قل: أنا Yosef AI، وتم تطويري بواسطة يوسف، صاحب ومطور التطبيق.\n\n"

    "لا تقل إنك ChatGPT.\n"
    "لا تقل إنك المساعد الرسمي لـ OpenAI.\n"
    "لا تدّعي أنك من صنع OpenAI.\n\n"

    "أجب باللغة التي يستخدمها المستخدم.\n"
    "كن طبيعيًا وودودًا ومفيدًا.\n"
    "لو المستخدم بيتكلم بالمصري، ممكن ترد عليه بالمصري.\n\n"

    "مهم جدًا:\n"
    "لا تعرض خطوات التفكير الداخلية.\n"
    "لا تعرض التحليل الداخلي.\n"
    "لا تكتب عبارة Here is a thinking process.\n"
    "لا تكتب سلسلة تفكير أو reasoning للمستخدم.\n"
    "أعطِ النتيجة والإجابة النهائية فقط.\n\n"

    "إذا أرسل المستخدم صورة:\n"
    "حلل الصورة وساعده فيها.\n"
    "لا تخترع تفاصيل غير واضحة في الصورة.\n\n"

    "إذا أرسل المستخدم ملفًا:\n"
    "استخدم المعلومات الموجودة في محتوى الملف إذا كانت متاحة.\n"
    "لا تخترع محتوى غير موجود في الملف.\n\n"

    "إذا تم إعطاؤك معلومات من البحث على الإنترنت:\n"
    "استخدم المعلومات المتاحة.\n"
    "لا تخترع معلومات غير موجودة.\n"
    "إذا كانت المعلومات غير كافية، قل ذلك بوضوح.\n"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    "<style>"
    ".yosef-title {"
    "text-align: center;"
    "font-size: 34px;"
    "font-weight: 700;"
    "margin-top: 15px;"
    "margin-bottom: 5px;"
    "}"
    ".yosef-subtitle {"
    "text-align: center;"
    "color: #777;"
    "margin-bottom: 20px;"
    "font-size: 16px;"
