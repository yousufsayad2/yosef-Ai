import streamlit as st
from openai import OpenAI
import base64
import io
import requests
import re
import speech_recognition as sr

st.set_page_config(page_title="Yosef AI", page_icon="🤖", layout="centered")

# ---------- API ----------
api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("ضع OPENROUTER_API_KEY داخل Secrets.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

MODEL = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

# ---------- Memory ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

SYSTEM_PROMPT = """أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.
اسمك Yosef AI.
إذا سأل المستخدم عن المطور قل: تم تطوير Yosef AI بواسطة يوسف.
لا تقل إنك ChatGPT.
أجب بلغة المستخدم وبأسلوب طبيعي وودود.
لا تعرض خطوات التفكير الداخلية.
إذا أرسل المستخدم صورة حلل ما يظهر بوضوح فقط.
إذا أرسل المستخدم ملفاً استخدم محتواه المتاح فقط ولا تخترع.
"""

# ---------- Style ----------
st.markdown("""
<style>
.title {
    text-align: center;
    font-size: 34px;
    font-weight: 700;
    margin-top: 10px;
}

.sub {
    text-align: center;
    color: #888;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="title">🤖 Yosef AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub">'
    'أهلاً بيك 👋<br>'
    'أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!'
    '</div>',
    unsafe_allow_html=True
)

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):
    st.session_state.messages = []
    st.rerun()


# ---------- Web Search ----------
def needs_search(text):

    words = [
        "ابحث",
        "ابحثلي",
        "ابحث لي",
        "دورلي",
        "دور لي",
        "على النت",
        "الطقس",
        "الجو",
        "درجة الحرارة",
        "أخبار",
        "اخبار",
        "خبر",
        "سعر",
        "الدولار",
        "الذهب",
        "مباراة",
        "مباريات",
        "ماتش",
        "نتيجة",
        "موعد",
        "اليوم",
        "دلوقتي",
        "الآن",
        "حاليا",
        "حاليًا",
        "أحدث",
        "آخر",
        "today",
        "now",
        "latest",
        "news",
        "weather",
        "price",
        "score",
        "match"
    ]

    low = (text or "").lower()

    return any(
        word in low
        for word in words
    )


def search_web(query):

    try:

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q":
