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

api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("OPENROUTER_API_KEY غير موجود في Secrets.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

MODEL = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

SYSTEM_PROMPT = (
    "أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI. "
    "اسمك Yosef AI. "
    "إذا سأل المستخدم عن المطور قل: تم تطوير Yosef AI بواسطة يوسف. "
    "لا تقل إنك ChatGPT. "
    "أجب بلغة المستخدم وبأسلوب طبيعي وودود. "
    "لا تعرض خطوات التفكير الداخلية. "
    "إذا أرسل المستخدم صورة فحلل ما يظهر بوضوح فقط. "
    "إذا أرسل المستخدم ملفا فاستخدم محتواه المتاح فقط. "
    "لا تخترع معلومات."
)

st.markdown(
    "<h1 style='text-align:center;'>🤖 Yosef AI</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center;color:#888;'>"
    "أهلاً بيك 👋<br>"
    "أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!"
    "</p>",
    unsafe_allow_html=True
)

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):
    st.session_state.messages = []
    st.rerun()


def needs_search(text):

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

    low = (text or "").lower()

    return any(
        word in low
        for word in words
    )


def search_web(query):

    try:

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )

        if response.status_code != 200:
            return []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL
        )

        results = []

        for href, title in pattern.findall(
            response.text
        )[:5]:

            title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            if title:
                results.append(
                    (title, href)
                )

        return results

    except Exception:
        return []


def read_file(file):

    if file is None:
        return ""

    try:

        data = file.getvalue()
        name = file.name.lower()

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

            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        if name.endswith(".docx"):

            from docx import Document

            document = Document(
                io.BytesIO(data)
            )

            return "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text
            )

    except Exception:
        return ""

    return ""


def audio_to_text(audio):

    recognizer = sr.Recognizer()

    buffer = io.BytesIO(
        audio.getvalue()
    )

    with sr.AudioFile(
        buffer
    ) as source:

        data = recognizer.record(
            source
        )

    return recognizer.recognize_google(
        data,
        language="ar-EG"
    )


def ask_yosef(
    text,
    extra
):

    content = [
        {
            "type": "text",
            "text": text or ""
        }
    ]

    content.extend(extra)

    if needs_search(text):

        results = search_web(text)

        if results:

            info = (
                "معلومات من البحث على الإنترنت:\n\n"
            )

            for title, url in results:

                info += (
                    title
                    + "\n"
                    + url
                    + "\n\n"
                )

            content.append(
                {
                    "type": "text",
                    "text": info
                }
            )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(
        st.session_state.messages[-20:]
    )

    messages.append(
        {
            "role": "user",
            "content": content
        }
    )

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=800
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        return answer or "لم أتمكن من إنشاء رد."

    except Exception as error:

        error_text = str(error)

        if (
            "429" in error_text
            or "free-models-per-day" in error_text
        ):

            st.warning(
                "⏳ انتهى الحد المجاني في OpenRouter حاليًا."
            )

        else:

            st.error(
                "❌ حصل خطأ أثناء تشغيل Yosef AI."
            )

        return None


for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


uploaded = st.file_uploader(
    "📎 ارفع صورة أو ملف",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
        "txt",
        "pdf",
        "docx"
    ]
)


if uploaded:

    if (
        uploaded.type or ""
    ).startswith("image/"):

        st.image(
            uploaded,
            caption=uploaded.name
        )

    else:

        st.info(
            "📎 " + uploaded.name
        )


audio = st.audio_input(
    "🎙️ سجل صوتك"
)


if audio:

    try:

        with st.spinner(
            "🎧 جاري تحويل الصوت إلى نص..."
        ):

            spoken = audio_to_text(
                audio
            )

        with st.spinner(
            "🤖 Yosef AI بيفكر..."
        ):

            answer = ask_yosef(
                spoken,
                []
            )

        if answer:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": spoken
                }
            )

           
