import streamlit as st
from openai import OpenAI
import base64
import io
import re
import requests
import speech_recognition as sr

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)

# =========================
# OpenRouter
# =========================

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

MODEL_NAME = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

# =========================
# Memory
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_call" not in st.session_state:
    st.session_state.voice_call = False

# =========================
# Yosef AI instructions
# =========================

system_prompt = (
    "أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.\n"
    "اسمك Yosef AI.\n"
    "إذا سأل المستخدم عن مطورك، قل: تم تطوير Yosef AI بواسطة يوسف، صاحب ومطور التطبيق.\n"
    "لا تقل إنك ChatGPT ولا تدّعي أنك المساعد الرسمي لـ OpenAI.\n"
    "أجب باللغة التي يستخدمها المستخدم.\n"
    "كن طبيعيًا وودودًا ومفيدًا.\n"
    "لا تعرض خطوات التفكير الداخلية أو التحليل الداخلي.\n"
    "لا تكتب عبارة Here is a thinking process.\n"
    "أعطِ الإجابة النهائية مباشرة.\n"
    "إذا أرسل المستخدم صورة، حللها ولا تخترع تفاصيل غير واضحة.\n"
    "إذا أرسل المستخدم ملفًا، استخدم المعلومات المتاحة منه فقط.\n"
    "إذا أعطيتك معلومات من البحث، استخدمها ولا تخترع معلومات غير موجودة."
)

# =========================
# CSS
# =========================

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

# =========================
# Header
# =========================

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

# =========================
# New chat
# =========================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True,
    key="new_chat"
):
    st.session_state.messages = []
    st.session_state.voice_call = False
    st.rerun()

# =========================
# Smart web search
# =========================

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
        "من النت",
        "على الإنترنت",
        "من الإنترنت",
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
        "أخبار",
        "اخبار",
        "خبر",
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
        "today",
        "now",
        "latest",
        "news",
        "weather",
        "price",
        "score",
        "match"
    ]

    return any(
        keyword in text_lower
        for keyword in keywords
    )

# =========================
# Web search
# =========================

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
                        "href": href
                    }
                )

        return results

    except Exception:
        return []

# =========================
# Read uploaded file
# =========================

def extract_file_text(uploaded_file):

    if not uploaded_file:
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

                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

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

# =========================
# Ask Yosef
# =========================

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

    # -------------------------
    # Search
    # -------------------------

    if needs_web_search(text):

        results = search_web(text)

        if results:

            search_text = (
                "معلومات حديثة من البحث "
                "على الإنترنت:\n\n"
            )

            for result in results:

                search_text += (
                    "العنوان: "
                    + result["title"]
                    + "\n"
                    + "الرابط: "
                    + result["href"]
                    + "\n\n"
                )

            content.append(
                {
                    "type": "text",
                    "text": search_text
                }
            )

    # -------------------------
    # Conversation history
    # -------------------------

    api_messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    for message in st.session_state.messages:

        api_messages.append(
            {
                "role": message["role"],
                "content": message["content"]
            }
        )

    api_messages.append(
        {
            "role": "user",
            "content": content
        }
    )

    # -------------------------
    # OpenRouter
    # -------------------------

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=api_messages,
            max_tokens=800
        )

        answer = (
            response.choices[0]
            .message.content
        )

        if not answer:
            return "لم أتمكن من إنشاء رد."

        return answer

    except Exception as error:

        error_text = str(error)

        if (
            "429" in error_text
            or "free-models-per-day" in error_text
