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

إذا تم تزويدك بمعلومات من البحث على الإنترنت:
- استخدمها للإجابة.
- لا تخترع معلومات غير موجودة فيها.
- إذا لم تكن المعلومات كافية، وضح ذلك للمستخدم.
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
# هل السؤال يحتاج بحث؟
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

    for keyword in keywords:
        if keyword in text_lower:
            return True

    return False

# =========================
# البحث على الإنترنت
# =========================

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

    except Exception:
        return []

# =========================
# خانة الكتابة
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

# =========================
# عند إرسال رسالة
# =========================

if prompt:

    try:

        # =========================
        # النص
        # =========================

        prompt_text = prompt.text or ""

        # =========================
        # الملف
        # =========================

        uploaded_file = (
            prompt.files[0]
            if prompt.files
            else None
        )

        # =========================
        # الصوت إلى نص
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

                    prompt_text = recognizer.recognize_google(
                        audio_data,
                        language="ar-EG"
                    )

                except sr.UnknownValueError:

                    st.error(
                        "❌ مش قادر أفهم الكلام في التسجيل. "
                        "جرّب تتكلم أوضح."
                    )

                    st.stop()

                except sr.RequestError as e:

                    st.error(
                        "❌ خدمة تحويل الصوت إلى نص "
                        f"غير متاحة حاليًا: {e}"
                    )

                    st.stop()

        # =========================
        # التأكد من وجود رسالة
        # =========================

        if not prompt_text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو سجل صوت أو ارفع ملف."
            )

            st.stop()

        # =========================
        # عرض رسالة المستخدم
        # =========================

        with st.chat_message("user"):

            if prompt_text:
                st.markdown(prompt_text)

            if prompt.audio:
                st.caption(
                    "🎙️ تم تحويل الرسالة الصوتية إلى نص."
                )

            if uploaded_file:

                file_type = uploaded_file.type or ""

                if file_type.startswith("image/"):
                    st.image(uploaded_file)
                else:
                    st.caption(
                        f"📎 {uploaded_file.name}"
                    )

        # =========================
        # تجهيز المحتوى
        # =========================

        content = [
            {
                "type": "text",
                "text": prompt_text
            }
        ]

        # =========================
        # إضافة
