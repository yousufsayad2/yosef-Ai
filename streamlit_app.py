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

SYSTEM_PROMPT = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.
اسمك Yosef AI.
إذا سأل المستخدم عن المطور، قل: تم تطوير Yosef AI بواسطة يوسف.
لا تقل إنك ChatGPT.
أجب بلغة المستخدم وبأسلوب طبيعي وودود.
لا تعرض خطوات التفكير الداخلية أو التحليل الداخلي.
أعط الإجابة النهائية فقط.
إذا أرسل المستخدم صورة، حلل ما يظهر بوضوح فقط.
إذا أرسل المستخدم ملفًا، استخدم المعلومات المتاحة منه فقط.
"""

st.markdown(
    """
    <style>
    .title {
        text-align: center;
        font-size: 34px;
        font-weight: 700;
    }

    .subtitle {
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
    '<div class="subtitle">'
    'أهلاً بيك 👋<br>'
    'أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!'
    '</div>',
    unsafe_allow_html=True
)

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):
    st.session_state.messages = []
    st.rerun()


def needs_web_search(text):
    if not text:
        return False

    keywords = [
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

    low = text.lower()

    for word in keywords:
        if word in low:
            return True

    return False


def search_web(query):
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
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

            clean_title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            if clean_title:
                results.append(
                    (
                        clean_title,
                        href
                    )
                )

        return results

    except Exception:
        return []


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

    audio_buffer = io.BytesIO(
        audio.getvalue()
    )

    with sr.AudioFile(
        audio_buffer
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
    extra=None
):

    content = [
        {
            "type": "text",
            "text": text or ""
        }
    ]

    if extra:
        content.extend(extra)

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

    api_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for message in st.session_state.messages[-20:]:

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

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=api_messages,
            max_tokens=800
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        if not answer:
            return "لم أتمكن من إنشاء رد."

        return answer

    except Exception as error:

        error_text = str(error)

        if (
            "429" in error_text
            or "free-models-per-day" in error_text
        ):

            st.warning(
                "⏳ الحد المجاني في OpenRouter انتهى حاليًا."
            )

            st.info(
                "جرّب مرة أخرى بعد تجدد الحد المجاني."
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


st.markdown("### 📎 صورة أو ملف")

uploaded_file = st.file_uploader(
    "اختار صورة أو ملف",
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

if uploaded_file:

    file_type = uploaded_file.type or ""

    if file_type.startswith("image/"):

        st.image(
            uploaded_file,
            caption=uploaded_file.name
        )

    else:

        st.info(
            "📎 " + uploaded_file.name
        )


st.markdown("### 🎙️ صوت")

voice_audio = st.audio_input(
    "سجل رسالتك من الميكروفون"
)

if voice_audio:

    try:

        with st.spinner(
            "🎧 جاري فهم صوتك..."
        ):

            spoken_text = audio_to_text(
                voice_audio
            )

        with st.spinner(
            "🤖 Yosef AI بيفكر..."
        ):

            answer = ask_yosef(
                spoken_text
            )

        if answer:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": spoken_text
                }
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.rerun()

    except sr.UnknownValueError:

        st.error(
            "❌ مش قادر أفهم التسجيل."
        )

    except sr.RequestError:

        st.error(
            "❌ خدمة التعرف على الصوت غير متاحة."
        )

    except Exception as error:

        st.error(
            "❌ حصل خطأ في الصوت: "
            + str(error)
        )


st.markdown("### 💬 اكتب رسالتك")

text = st.text_area(
    "الرسالة",
    placeholder="اكتب رسالتك هنا...",
    height=100,
    label_visibility="collapsed"
)

if st.button(
    "إرسال ➤",
   
