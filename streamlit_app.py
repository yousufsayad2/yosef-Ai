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

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"]
)

MODEL = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice" not in st.session_state:
    st.session_state.voice = False


SYSTEM = (
    "أنت Yosef AI. اسمك Yosef AI. "
    "تم تطوير Yosef AI بواسطة يوسف، صاحب ومطور التطبيق. "
    "إذا سأل المستخدم عن المطور، قل ذلك بوضوح. "
    "لا تقل إنك ChatGPT. "
    "أجب بلغة المستخدم وبأسلوب طبيعي وودود. "
    "لا تعرض خطوات التفكير الداخلية أو التحليل الداخلي. "
    "أعط الإجابة النهائية فقط. "
    "إذا أرسل المستخدم صورة فحللها ولا تخترع تفاصيل غير واضحة. "
    "إذا أرسل ملفًا فاستخدم المعلومات المتاحة منه فقط."
)


# =========================
# التصميم
# =========================

st.markdown(
    """
    <style>
    .title {
        text-align: center;
        font-size: 34px;
        font-weight: 700;
    }

    .sub {
        text-align: center;
        color: #777;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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


# =========================
# محادثة جديدة
# =========================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):

    st.session_state.messages = []
    st.session_state.voice = False

    st.rerun()


# =========================
# البحث الذكي
# =========================

def needs_search(text):

    words = [
        "ابحث",
        "ابحثلي",
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
        word
