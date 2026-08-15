import streamlit as st
from openai import OpenAI
import base64
import io
import requests
import re
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

if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False


# =========================================================
# تعليمات Yosef AI
# =========================================================

SYSTEM_PROMPT = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

اسمك Yosef AI.

إذا سأل المستخدم: من طورك؟ أو مين عملك؟
قل إن التطبيق تم تطويره بواسطة يوسف، صاحب ومطور Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

كن طبيعيًا وودودًا ومفيدًا.

مهم جدًا:
- لا تعرض خطوات التفكير الداخلية.
- لا تعرض التحليل الداخلي.
- لا تقل: Here's a thinking process.
- أعط الإجابة النهائية فقط.
- إذا كانت هناك معلومات من البحث، استخدمها بحذر.
- لا تخترع معلومات غير موجودة.
- إذا أرسل المستخدم صورة، حلل فقط ما يظهر فيها بوضوح.
- إذا أرسل المستخدم ملفًا، استخدم المحتوى المتاح منه فقط.
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
    st.session_state.voice_mode = False

    st.rerun()


# =========================================================
# البحث الذكي
# =========================================================

def needs_web_search(text):

    if not text:
        return False

    text_lower = text.lower()

    keywords = [
        "ابحث",
        "ابحثلي",
        "ابحث لي",
        "دورلي",
        "دور لي",
        "شوفلي",
        "شوف لي",
        "على النت",
        "على الإنترنت",
        "من الإنترنت",

        "الطقس",
        "الجو",
        "درجة الحرارة",

        "أخبار",
        "اخبار",
        "خبر",
        "الأخبار",
        "الاخبار",

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

        "اليوم",
        "دلوقتي",
        "دلوقت",
        "الآن",
        "حاليا",
        "حاليًا",
        "النهارده",
        "بكره",
        "غدا",

        "أحدث",
        "احدث",
        "آخر",
        "اخر",

        "today",
        "now",
        "latest",
        "recent",
        "news",
        "weather",
        "price",
        "prices",
        "score",
        "match"
    ]

    for keyword in keywords:

        if keyword in text_lower:
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

            clean_title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            if clean_title and href:

                results.append(
                    {
                        "title": clean_title,
                        "url": href
                    }
                )

        return results

    except Exception:

        return []


# =========================================================
# قراءة الملفات
# =========================================================

def read_uploaded_file(uploaded_file):

    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    file_bytes = uploaded_file.getvalue()

    try:

        if file_name.endswith(".txt"):

            return file_bytes.decode(
                "utf-8",
                errors="ignore"
            )


        if file_name.endswith(".pdf"):

            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(file_bytes)
            )

            pages = []

            for page in reader.pages:

                pages.append(
                    page.extract_text() or ""
                )

            return "\n".join(pages)


        if file_name.endswith(".docx"):

            from docx import Document

            document = Document(
                io.BytesIO(file_bytes)
            )

            paragraphs = []

            for paragraph in document.paragraphs:

                if paragraph.text:

                    paragraphs.append(
                        paragraph.text
                    )

            return "\n".join(paragraphs)

    except Exception:

        return ""

    return ""


# =========================================================
# تحويل الصوت إلى نص
# =========================================================

def audio_to_text(audio_file):

    recognizer = sr.Recognizer()

    audio_buffer = io.BytesIO(
        audio_file.getvalue()
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


    # -----------------------------------------------------
    # محتوى إضافي
    # -----------------------------------------------------

    if extra_content:

        content.extend(
            extra_content
        )


    # -----------------------------------------------------
    # البحث
    # -----------------------------------------------------

    if needs_web_search(text):

        results = search_web(text)

       
