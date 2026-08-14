import streamlit as st
from openai import OpenAI
import base64
import io
import speech_recognition as sr
import streamlit.components.v1 as components
import json
from ddgs import DDGS

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖"
)

st.title("🤖 Yosef AI")
st.write("أهلاً بيك 👋")
st.write("أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!")

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

system_prompt = """أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.
عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.
لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.
أجب باللغة التي يستخدمها المستخدم.

إذا تم تزويدك بنتائج بحث على الإنترنت، استخدمها للإجابة عن السؤال.
لا تخترع معلومات غير موجودة في نتائج البحث.
إذا كانت المعلومات حديثة، وضّح أنها مبنية على نتائج البحث.
"""

# =========================
# البحث على الإنترنت
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
        keyword in text_lower
        for keyword in keywords
    )


def search_web(query):
    try:
        with DDGS(timeout=10) as ddgs:

            results = list(
                ddgs.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=5
                )
            )

        return results

    except Exception as e:
        return []


# =========================
# عرض المحادثة
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
# الإعدادات
# =========================

voice_enabled = st.checkbox(
    "🔊 تشغيل رد Yosef AI بصوت",
    value=False
)

web_enabled = st.checkbox(
    "🌐 البحث على الإنترنت عند الحاجة",
    value=True
)


# =========================
# الإدخال
# =========================

prompt = st.chat_input(
    "اكتب رسالتك أو سجل صوتك...",
    accept_file=True,
    accept_audio=True,
    file_type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
        "txt",
        "pdf",
        "docx"
    ]
)


if prompt:

    try:

        prompt_text = prompt.text or ""

        uploaded_file = (
            prompt.files[0]
            if prompt.files
            else None
        )


        # =========================
        # تحويل الصوت إلى نص
        # =========================

        if prompt.audio:

            with st.spinner(
                "🎙️ جاري تحويل صوتك إلى نص..."
            ):

                audio_bytes = prompt.audio.getvalue()

                recognizer = sr.Recognizer()

                audio_file = io.BytesIO(
                    audio_bytes
                )

                with sr.AudioFile(audio_file) as source:

                    audio_data = recognizer.record(
                        source
                    )

                try:

                    prompt_text = (
                        recognizer.recognize_google(
                            audio_data,
                            language="ar-EG"
                        )
                    )

                except sr.UnknownValueError:

                    st.error(
                        "❌ مش قادر أفهم الكلام في التسجيل. "
                        "جرّب تتكلم أوضح."
                    )

                   
