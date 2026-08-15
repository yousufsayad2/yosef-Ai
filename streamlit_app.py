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
أنت Yosef AI.

اسمك Yosef AI.

لا تقل إنك ChatGPT.

أجب باللغة التي يستخدمها المستخدم.

كن طبيعيًا وودودًا ومفيدًا.

في المحادثة الصوتية:
- تحدث بطريقة طبيعية.
- اجعل الرد واضحًا ومختصرًا.
- لا تستخدم مقدمات طويلة.
- تعامل مع المستخدم كأنه يتحدث مع مساعد صوتي.

إذا أرسل المستخدم صورة:
- حلل الصورة.
- لا تخترع تفاصيل غير واضحة.

إذا أرسل المستخدم ملفًا:
- استخدم المعلومات المتاحة منه.
- لا تخترع محتوى الملف.

إذا أعطيتك معلومات من البحث:
- استخدم المعلومات الموجودة.
- لا تخترع معلومات غير موجودة.
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
        margin-bottom: 5px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 20px;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# العنوان
# =========================================================

st.markdown(
    '<div class="yosef-title">🤖 Yosef AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="yosef-subtitle">'
    'أهلاً بيك 👋<br>'
    'أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# محادثة جديدة
# =========================================================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True,
    key="new_chat"
):
    st.session_state.messages = []
    st.session_state.voice_call = False
    st.rerun()


# =========================================================
# عرض المحادثة
# =========================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================================================
# البحث الذكي
# =========================================================

def needs_web_search(text):

    if not text:
        return False

    text_lower = text.lower()

    explicit_words = [
        "ابحث",
        "ابحثلي",
        "ابحث لي",
        "دورلي",
        "دور لي",
        "شوفلي",
        "شوف لي",
        "على النت",
        "من النت",
        "على الإنترنت",
        "من الإنترنت",
        "search",
        "google",
        "look up"
    ]

    for word in explicit_words:
        if word in text_lower:
            return True

    current_words = [
        "اليوم",
        "دلوقتي",
        "دلوقت",
        "الآن",
        "حاليا",
        "حاليًا",
        "النهارده",
        "بكره",
        "غدا",
        "آخر",
        "اخر",
        "أحدث",
        "احدث",
        "الجديد",
        "current",
        "today",
        "now",
        "latest",
        "recent"
    ]

    for word in current_words:
        if word in text_lower:
            return True

    live_topics = [
        "أخبار",
        "اخبار",
        "خبر",
        "الأخبار",
        "الاخبار",
        "الطقس",
        "الجو",
        "درجة الحرارة",
        "مطر",
        "رياح",
        "سعر",
        "أسعار",
        "اسعار",
        "بكام",
        "الدولار",
        "اليورو",
        "الذهب",
        "البورصة",
        "مباراة",
        "مباريات",
        "ماتش",
        "نتيجة",
        "نتائج",
        "موعد",
        "news",
        "weather",
        "price",
        "prices",
        "score",
        "match"
    ]

    for word in live_topics:
        if word in text_lower:
            return True

    return False


# =========================================================
# البحث على الإنترنت
# =========================================================

def search_web(query):

    try:

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )

        if response.status_code != 200:
            return []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL
        )

        matches = pattern.findall(response.text)

        results = []

        for href, title in matches[:5]:

            clean_title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            if clean_title and href:
                results.append(
                    {
                        "title": clean_title,
                        "href": href
                    }
                )

       
