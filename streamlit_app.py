import streamlit as st
from openai import OpenAI
import base64
import io
import speech_recognition as sr
import streamlit.components.v1 as components
import json
from ddgs import DDGS


# =========================
# إعداد الصفحة
# =========================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖"
)

st.title("🤖 Yosef AI")
st.write("أهلاً بيك 👋")
st.write("أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!")


# =========================
# OpenRouter
# =========================

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


# =========================
# الذاكرة
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================
# تعليمات Yosef AI
# =========================

system_prompt = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

إذا تم تزويدك بنتائج بحث على الإنترنت:
- استخدم النتائج للإجابة.
- لا تخترع معلومات غير موجودة في النتائج.
- إذا كانت المعلومات غير كافية، وضح ذلك.
- لا تذكر للمستخدم تفاصيل تقنية عن طريقة البحث.
"""


# =========================
# عرض المحادثة السابقة
# =========================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# محادثة جديدة
# =========================

if st.button("🆕 محادثة جديدة"):

    st.session_state.messages = []

    st.rerun()


# =========================
# أدوات صغيرة
# =========================

col1, col2 = st.columns(2)

with col1:

    web_enabled = st.toggle(
        "🔎 بحث",
        value=True
    )

with col2:

    voice_enabled = st.toggle(
        "🔊 صوت الرد",
        value=False
    )


# =========================
# تحديد الأسئلة التي تحتاج بحث
# =========================

def needs_web_search(text):

    keywords = [

        "الطقس",
        "الجو",
        "درجة الحرارة",

        "أخبار",
        "خبر",
        "الأخبار",

        "سعر",
        "الأسعار",

        "اليوم",
        "دلوقتي",
        "الآن",
        "حاليا",
        "حاليًا",

        "أحدث",
        "آخر",

        "موعد",
        "متى",

        "نتيجة",
        "نتائج",

        "مباراة",
        "مباريات",

        "حدث",
        "أحداث",

        "today",
        "now",
        "latest",
        "news",
        "weather",
        "price",
        "prices",
        "current"
    ]

    text_lower = text.lower()

    return any(
        keyword
