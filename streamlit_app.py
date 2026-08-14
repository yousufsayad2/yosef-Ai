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
        margin-top: 20px;
        margin-bottom: 5px;
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
- تكلم بطريقة طبيعية.
- اجعل الرد مختصرًا وواضحًا.
- تعامل مع الكلام كأنه محادثة عادية.
- لا تستخدم مقدمات طويلة.

إذا تم إعطاؤك معلومات من البحث على الإنترنت:
- استخدم المعلومات المتاحة.
- لا تخترع معلومات.
- إذا كانت المعلومات غير كافية، وضح ذلك.
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
    use_container_width=True,
    key="new_chat"
):

    st.session_state.messages = []
    st.session_state.voice_call = False
    st.session_state.audio_frames = []

    st.rerun()


# =========================================================
# زر المحادثة الصوتية
# =========================================================

if not st.session_state.voice_call:

    if st.button(
        "📞 محادثة صوتية",
        use_container_width=True,
        key="start_voice_call"
    ):

        st.session_state.voice_call = True
        st.session_state.audio_frames = []

        st.rerun()

else:

    if st.button(
        "🔴 إنهاء المحادثة الصوتية",
        use_container_width=True,
        key="stop_voice_call"
    ):

        st.session_state.voice_call = False
        st.session_state.audio_frames = []

        st.rerun()


# =========================================================
# دالة البحث
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
        "score
