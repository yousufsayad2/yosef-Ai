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
# دالة أخطاء الذكاء الاصطناعي
# =========================================================

def show_ai_error(error):

    error_text = str(error)

    if (
        "429" in error_text
        or "free-models-per-day" in error_text
        or "Rate limit exceeded" in error_text
    ):

        st.warning(
            "⏳ وصلنا للحد المجاني للطلبات اليوم.\n\n"
            "جرّب استخدام Yosef AI بعد تجدد الحد."
        )

    else:

        st.error(
            "❌ حصل خطأ أثناء تشغيل Yosef AI.\n\n"
            "جرّب مرة أخرى بعد قليل."
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
    key="new_chat_button"
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
# تحديد الأسئلة التي تحتاج بحث
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
        "نت
