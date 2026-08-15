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


# =========================================================
# OpenRouter
# =========================================================

api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("❌ OPENROUTER_API_KEY غير موجود في Secrets.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

MODEL = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free"
)


# =========================================================
# الذاكرة
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# تعليمات Yosef AI
# =========================================================

SYSTEM_PROMPT = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

اسمك Yosef AI.

إذا سأل المستخدم:
من طورك؟
من عملك؟
مين مطورك؟

قل:
تم تطوير Yosef AI بواسطة يوسف.

لا تقل إنك ChatGPT.

أجب باللغة التي يستخدمها المستخدم.

كن طبيعيًا وودودًا ومفيدًا.

لا تعرض خطوات التفكير الداخلية أو التحليل الداخلي.
أعط الإجابة النهائية فقط.

إذا أرسل المستخدم صورة:
حلل ما يظهر بوضوح فقط ولا تخترع تفاصيل.

إذا أرسل المستخدم ملفًا:
استخدم المعلومات المتاحة منه فقط.

إذا تم إعطاؤك معلومات من البحث:
استخدم المعلومات الموجودة ولا تخترع معلومات.
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
        margin-top: 20px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #777;
        font-size: 16px;
        margin-bottom: 20px;
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
    use_container_width=True
):

    st.session_state.messages = []

    st.rerun()


# =========================================================
# البحث الذكي
# =========================================================

def needs_web_search(text):

    if not text:
        return False

    words = [
        "ابحث",
        "ابحثلي",
        "ابحث لي",
        "دورلي",
        "دور لي",
        "على النت",
        "على الإنترنت",
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
        "score"
    ]

    text_lower = text.lower()

    for word in words:

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
            params={
                "q": query
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
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

            title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            if title and href:

                results.append(
                    (
                        title,
                        href
                    )
                )

        return results

    except Exception:

        return []


# =========================================================
# قراءة الملفات
# =========================================================

def read_file(uploaded):

    if uploaded is None:
        return ""

    name = uploaded.name.lower()

    data = uploaded.getvalue()

    try:

        if name.endswith(".txt"):

            return data.decode(
                "utf-8",
                errors="ignore"
            )


        if name.endswith(".pdf"):

            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(data)
            )

            text_parts = []

            for page in reader.pages:

                text_parts.append(
                    page.extract_text() or ""
                )

            return "\n".join(
                text_parts
            )


        if name.endswith(".docx"):

            from docx import Document

            document = Document(
                io.BytesIO(data)
            )

            text_parts = []

            for paragraph in document.paragraphs:

                if paragraph.text:

                    text_parts.append(
                        paragraph.text
                    )

            return "\n".join(
                text_parts
            )

    except Exception:

        return ""

    return ""


# =========================================================
# تحويل الصوت إلى نص
# =========================================================

def speech_to_text(audio):

    recognizer = sr.Recognizer()

    audio_buffer = io.BytesIO(
        audio.getvalue()
    )

    with sr.AudioFile(
        audio_buffer
    ) as source:

        audio_data = recognizer.record(
            source
        )

    return recognizer.recognize_google(
        audio_data,
        language="ar-EG"
    )


# =========================================================
# سؤال Yosef AI
# =========================================================

def ask_yosef(
    text,
    extra_content=None
):

    content = [
        {
            "type": "text",
            "text": text or ""
        }
    ]


    if extra_content:

        content.extend(
            extra_content
        )


    # البحث

    if needs_web_search(text):

        results = search_web(text)

        if results:

            search_text = (
                "معلومات من البحث على الإنترنت:\n\n"
            )

            for title, url in results:

                search_text += (
                    title
                    + "\n"
                    + url
                    + "\n\n"
                )

            content.append(
                {
                    "type": "text",
                    "text": search_text
                }
            )


    # تاريخ المحادثة

    api_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


    for message in
