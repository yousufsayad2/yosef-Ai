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

st.markdown(
    """
    <style>
    .yosef-title {
        text-align: center;
        font-size: 38px;
        font-weight: 800;
        margin-top: 20px;
        margin-bottom: 5px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #888;
        font-size: 16px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="yosef-title">🤖 Yosef AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="yosef-subtitle">'
    'أهلاً بيك 👋<br>'
    'أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!'
    '</div>',
    unsafe_allow_html=True,
)

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True,
    key="new_chat",
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
        "score",
    ]

    low = (text or "").lower()

    return any(
        word in low
        for word in words
    )


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
                "User-Agent": "YosefAI/1.0",
            },
            timeout=10,
        )

        if response.status_code != 200:
            return ""

        data = response.json()
        parts = []

        abstract = data.get(
            "AbstractText",
            "",
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
                    "",
                )

                url = item.get(
                    "FirstURL",
                    "",
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
                errors="ignore",
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
    extra=None,
):

    content = [
        {
            "type": "text",
            "text": text or "",
        }
    ]

    if extra:
        content.extend(
            extra
        )

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


# =========================================================
# عرض المحادثة
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# خانة الشات الرئيسية
# + الصور
# + الملفات
# + الصوت
# =========================================================

prompt = st.chat_input(
    "اكتب رسالتك...",
    accept_file=True,
    accept_audio=True,
    file_type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
        "txt",
        "pdf",
        "docx",
    ],
)


# =========================================================
# استقبال الرسالة
# =========================================================

if prompt:

    try:

        text = prompt.text or ""

        uploaded_file = None

        if prompt.files:

            uploaded_file = prompt.files[0]


        # =================================================
        # تحويل الصوت إلى نص
        # =================================================

        if prompt.audio:

            try:

                text = audio_to_text(
                    prompt.audio
                )

            except sr.UnknownValueError:

                st.error(
                    "❌ مش قادر أفهم التسجيل. "
                    "جرب تتكلم أوضح."
                )

                st.stop()

            except sr.RequestError:

                st.error(
                    "❌ خدمة تحويل الصوت إلى نص "
                    "غير متاحة حاليًا."
                )

                st.stop()


        # =================================================
        # التأكد من وجود محتوى
        # =================================================

        if not text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو اضغط + لإضافة صورة أو ملف."
            )

            st.stop()


        # =================================================
        # عرض رسالة المستخدم
        # =================================================

        with st.chat_message(
            "user"
        ):

            if text:

                st.markdown(
                    text
                )

            if uploaded_file:

                file_type = (
                    uploaded_file.type or ""
                )

                if file_type.startswith(
                    "image/"
                ):

                    st.image(
                        uploaded_file
                    )

                else:

                    st.caption(
                        "📎 "
                        + uploaded_file.name
                    )


        # =================================================
        # تجهيز المحتوى الإضافي
        # =================================================

        extra_content = []


        # =================================================
        # الصورة
        # =================================================

        if uploaded_file:

            file_type = (
                uploaded_file.type or ""
            )

            if file_type.startswith(
                "image/"
            ):

                image_bytes = (
                    uploaded_file.getvalue()
                )

                image_base64 = (
                    base64.b64encode(
                        image_bytes
                    ).decode("utf-8")
                )

                extra_content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                "data:"
                                + file_type
                                + ";base64,"
                                + image_base64
                            )
                        },
                    }
                )


            # =================================================
            # PDF / DOCX / TXT
            # =================================================

            else:

                file_text = read_file(
                    uploaded_file
                )

                if file_text:

                    extra_content.append(
                        {
                            "type": "text",
                            "text": (
                                "محتوى الملف المرفق:\n\n"
                                + file_text[:20000]
                            ),
                        }
                    )

                else:

                    extra_content.append(
                        {
                            "type": "text",
                            "text": (
                                "المستخدم أرفق ملفًا اسمه: "
                                + uploaded_file.name
                            ),
                        }
                    )


        # =================================================
        # إرسال إلى Yosef AI
        # =================================================

        with st.spinner(
            "🤖 Yosef AI بيفكر..."
        ):

            answer = ask_yosef(
                text,
                extra_content,
            )


        # =================================================
        # لو حصل خطأ
        # =================================================

        if not answer:

            st.stop()


        # =================================================
        # عرض الرد
        # =================================================

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                answer
            )


        # =================================================
        # حفظ المحادثة
        # =================================================

        st.session_state.messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )


    except Exception as error:

        st.error(
            "❌ حصل خطأ: "
            + str(error)
        )
