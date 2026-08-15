import streamlit as st
from openai import OpenAI
import base64
import io
import requests
import re
import speech_recognition as sr

# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered",
)

# =========================================================
# OpenRouter
# =========================================================

api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("ضع OPENROUTER_API_KEY داخل Secrets في Streamlit.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

MODEL_NAME = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free",
)

# =========================================================
# الذاكرة
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================================================
# تعليمات Yosef AI
# =========================================================

SYSTEM_PROMPT = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

اسمك Yosef AI.
إذا سأل المستخدم عن مطور التطبيق، قل إن التطبيق تم تطويره بواسطة يوسف.
لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.
كن طبيعيًا وودودًا ومفيدًا.
لا تعرض خطوات التفكير الداخلية أو التحليل الداخلي.

إذا أرسل المستخدم صورة:
- حلل الأشياء الظاهرة بوضوح.
- إذا كان شيء غير واضح، قل إنه غير واضح.
- لا تخترع تفاصيل.

إذا أرسل المستخدم ملفًا:
- استخدم محتوى الملف المتاح لك.
- لا تخترع معلومات غير موجودة في الملف.

إذا تم تزويدك بنتائج بحث على الإنترنت:
- استخدم المعلومات الموجودة فيها.
- لا تخترع معلومات غير موجودة.
- إذا كانت النتائج غير كافية، وضح ذلك.
"""

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
        margin-top: 15px;
        margin
