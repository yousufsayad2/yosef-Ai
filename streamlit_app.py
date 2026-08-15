import streamlit as st
from openai import OpenAI
import base64
import io
import requests
import re
import speech_recognition as sr

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)

api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("ضع OPENROUTER_API_KEY في Secrets.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

MODEL = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

SYSTEM_PROMPT = (
    "أنت Yosef AI. اسمك Yosef AI. "
    "إذا سأل المستخدم عن المطور قل: تم تطوير Yosef AI بواسطة يوسف. "
    "لا تقل إنك ChatGPT. أجب بلغة المستخدم وبأسلوب طبيعي. "
    "لا تعرض خطوات التفكير الداخلية. لا تخترع معلومات."
)

st.title("🤖 Yosef AI")
st.caption("أهلاً بيك 👋 أنا Yosef AI، مساعدك الذكي.")

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):
    st.session_state.messages = []
    st.rerun()


def needs_search(text):
    words = [
        "ابحث",
        "ابحثلي",
        "دورلي",
        "على النت",
        "الطقس",
        "الجو",
        "أخبار",
        "اخبار",
        "سعر",
        "الدولار",
        "الذهب",
        "مباراة",
        "مباريات",
        "نتيجة",
        "موعد",
        "اليوم",
        "دلوقتي",
        "الآن",
        "أحدث",
        "آخر",
        "today",
        "now",
        "latest",
        "news",
        "weather",
        "price",
        "score"
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
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )

        if response.status_code != 200:
            return []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.I | re.S
        )

        results = []

        for href, title in pattern.findall(
            response.text
