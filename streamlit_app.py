import streamlit as st
from openai import OpenAI
import base64
import re
import requests
import io
import wave
import speech_recognition as sr

from streamlit_webrtc import webrtc_streamer, WebRtcMode


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
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 20px;
    }

    .call-title {
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-top: 10px;
    }

    div[data-testid="stButton"] button {
        border-radius: 14px;
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
# Session State
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_call" not in st.session_state:
    st.session_state.voice_call = False

if "audio_frames" not in st.session_state:
    st.session_state.audio_frames = []


# =========================================================
# تعليمات Yosef AI
# =========================================================

system_prompt = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

في المحادثة الصوتية:
- تحدث بطريقة طبيعية وقصيرة.
- لا تكتب مقدمات طويلة.
- تعامل مع المستخدم كأنها محادثة صوتية.
- لا تكرر كلام المستخدم إلا إذا كان ذلك ضروريًا.
- اجعل الرد مناسبًا للاستماع وليس للقراءة.

إذا تم إعطاؤك معلومات من البحث على الإنترنت:
- استخدم المعلومات المتاحة.
- لا تخترع معلومات.
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
    use_container_width=True
):

    st.session_state.messages = []
    st.session_state.voice_call = False
    st.session_state.audio_frames = []

    st.rerun()


# =========================================================
# عرض المحادثة
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================================================
# البحث التلقائي
# =========================================================

def needs_web_search(text):

    keywords = [

        "الطقس",
        "الجو",
        "درجة الحرارة",
        "مطر",
        "رياح",

        "أخبار",
        "خبر",
        "الأخبار",
        "آخر الأخبار",
        "اخر الاخبار",

        "سعر",
        "الأسعار",
        "بكام",
        "سعر الدولار",
        "سعر الذهب",

        "اليوم",
        "دلوقتي",
        "الآن",
        "حاليا",
        "حاليًا",

        "أحدث",
        "آخر",
        "الجديد",

        "موعد",
        "متى",
        "نتيجة",
        "نتائج",

        "مباراة",
        "مباريات",
        "ماتش",

        "today",
        "now",
        "latest",
        "news",
        "weather",
        "price",
        "current",
        "score",
        "match"
    ]

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in keywords
    )


# =========================================================
# البحث على الإنترنت
# =========================================================

def search_web(query):

    try:

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={
                "q": query
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=15
        )

        if response.status_code != 200:
            return []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL
        )

        matches = pattern.findall(
            response.text
        )

        results = []

        for href, title in matches[:5]:

            clean_title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            results.append(
                {
                    "title": clean_title,
                    "href": href
                }
            )

        return results

    except Exception:

        return []


# =========================================================
# سؤال Yosef AI
# =========================================================

def ask_yosef(text, voice_mode=False):

    if voice_mode:

        user_instruction = (
            "هذه رسالة صوتية من المستخدم. "
            "رد بطريقة طبيعية ومختصرة مناسبة للمحادثة الصوتية:\n\n"
            + text
        )

    else:

        user_instruction = text


    content = [
        {
            "type": "text",
            "text": user_instruction
        }
    ]


    # -------------------------------------------------------
    # البحث التلقائي
    # -------------------------------------------------------

    if needs_web_search(text):

        results = search_web(text)

        if results:

            search_text = (
                "\n\n"
                "معلومات حديثة من البحث على الإنترنت:\n\n"
            )
