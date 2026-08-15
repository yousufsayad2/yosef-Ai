import streamlit as st
from openai import OpenAI
import base64
import io
import requests
import speech_recognition as sr

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered",
)

api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("OPENROUTER_API_KEY غير موجود في Secrets.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

model = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free",
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
    "لا تخترع معلومات."
)

st.title("🤖 Yosef AI")
st.caption("أهلاً بيك 👋 أنا Yosef AI، مساعدك الذكي.")

if st.button("🆕 محادثة جديدة", use_container_width=True):
    st.session_state.messages = []
    st.rerun()


def needs_search(text):
    words = [
        "ابحث", "ابحثلي", "ابحث لي", "دورلي", "دور لي",
        "على النت", "الطقس", "الجو", "أخبار", "اخبار", "خبر",
        "سعر", "الدولار", "الذهب", "مباراة", "مباريات",
        "ماتش", "نتيجة", "موعد", "اليوم", "دلوقتي", "الآن",
        "أحدث", "آخر", "today", "now", "latest", "news",
        "weather", "price", "score"
    ]

    low = (text or "").lower()

    for word in words:
        if word in low:
            return True

    return False


def search_web(query):
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            },
            headers={
                "User-Agent": "YosefAI/1.0"
            },
            timeout=10,
        )

        if response.status_code != 200:
            return ""

        data = response.json()
        parts = []

        abstract = data.get(
            "AbstractText",
            ""
        )

        if abstract:
            parts.append(abstract)

        for item in data.get(
            "RelatedTopics",
            []
        )[:5]:

            if isinstance(item, dict):

                text = item.get(
                    "Text",
                    ""
                )

                url = item.get(
                    "FirstURL",
                    ""
                )

                if text:
                    parts.append(text)

                if url:
                    parts.append(url)

        return "\n\n".join(
            parts[:10]
        )

    except Exception:
        return ""


def read_file(file):
    if not file:
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

            parts = []

            for page in reader.pages:
                parts.append(
                    page.extract_text() or ""
                )

            return "\n".join(parts)

        if name.endswith(".docx"):
            from docx import Document

            document = Document(
                io.BytesIO(data)
            )

            parts = []

            for paragraph in document.paragraphs:

                if paragraph.text:
                    parts.append(
                        paragraph.text
                    )

            return "\n".join(parts)

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
        language="ar-EG",
    )


def ask_yosef(
    text,
    extra=None
):

    content = [
        {
            "type": "text",
            "text": text or "",
        }
    ]

    if extra:
        content.extend(extra)

    if needs_search(text):

        search_result = search_web(
            text
        )

        if search_result:

            content.append(
                {
                    "type": "text",
                    "text": (
                        "معلومات من البحث على الإنترنت:\n\n"
                        + search_result[:12000]
                    ),
                }
            )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    messages.extend(
        st.session_state.messages[-20:]
    )

    messages.append(
        {
            "role": "user",
            "content": content,
        }
    )

    try:

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=800,
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        return (
            answer
            or "لم أتمكن من إنشاء رد."
        )

    except Exception as error:

        error_text = str(error)

        if (
            "429" in error_text
            or "free-models-per-day" in error_text
            or "Rate limit exceeded" in error_text
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
        "docx",
    ],
)


extra = []


if uploaded:

    file_type = uploaded.type or ""

    if file_type.startswith("image/"):

        st.image(
            uploaded,
            caption=uploaded.name,
        )

        encoded = base64.b64encode(
            uploaded.getvalue()
        ).decode("utf-8")

        extra.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": (
                        "data:"
                        + file_type
                        + ";base64,"
                        + encoded
                    )
                },
            }
        )

    else:

        st.info(
            "📎 " + uploaded.name
        )

        file_text = read_file(
            uploaded
        )

        if file_text:

            extra.append(
                {
                    "type": "text",
                    "text": (
                        "محتوى الملف:\n"
                        + file_text[:20000]
                    ),
                }
            )


audio = st.audio_input(
    "🎙️ سجل صوتك",
)


if audio:

    try:

        spoken = audio_to_text(
            audio
        )

        with st.spinner(
            "🤖 Yosef AI بيفكر..."
        ):

            answer = ask_yosef(
                spoken
            )

        if answer:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": spoken,
                }
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            st.rerun()

    except sr.UnknownValueError:

        st.error(
            "❌ مش قادر أفهم التسجيل."
        )

    except sr.RequestError:

        st.error(
            "❌ خدمة تحويل الصوت غير متاحة."
        )

    except Exception as error:

        st.error(
            "❌ حصل خطأ في الصوت: "
            + str(error)
        )


prompt = st.chat_input(
    "اكتب رسالتك..."
)


if prompt:

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )

        if uploaded:

            file_type = uploaded.type or ""

            if file_type.startswith("image/"):

                st.image(
                    uploaded
                )

    with st.spinner(
        "🤖 Yosef AI بيفكر..."
    ):

        answer = ask_yosef(
            prompt,
            extra,
        )

    if answer:

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                answer
            )

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()
