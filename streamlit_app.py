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

# =========================================================
# OpenRouter
# =========================================================

api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("OPENROUTER_API_KEY غير موجود في Secrets.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# موديل ثابت وسريع ويدعم الصور
MODEL = "meta-llama/llama-4-scout:free"


# =========================================================
# الذاكرة
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# تعليمات Yosef AI
# =========================================================

SYSTEM_PROMPT = (
    "أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI. "
    "اسمك Yosef AI. "
    "إذا سأل المستخدم: مين مطورك؟ أو مين عملك؟ "
    "أجب: أنا Yosef AI، وتم تطويري بواسطة يوسف. "
    "لا تقل إنك ChatGPT. "
    "أجب باللغة التي يستخدمها المستخدم. "
    "كن طبيعيًا وودودًا ومختصرًا. "
    "ممنوع عرض التفكير الداخلي أو خطوات التحليل. "
    "لا تكتب عبارات مثل: أفكر، سأحلل، تحليل المستخدم، "
    "Here's a thinking process، First, I need to check، "
    "أو أي شرح لعملية التفكير الداخلية. "
    "أرسل الإجابة النهائية فقط. "
    "إذا كان السؤال بسيطًا، اجعل الرد قصيرًا."
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .yosef-title {
        text-align: center;
        font-size: 38px;
        font-weight: 800;
        margin-top: 18px;
        margin-bottom: 5px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #888;
        font-size: 16px;
        margin-bottom: 22px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# العنوان
# =========================================================

st.markdown(
    '<div class="yosef-title">🤖 Yosef AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="yosef-subtitle">'
    "أهلاً بيك 👋<br>"
    "أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!"
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# محادثة جديدة
# =========================================================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True,
    key="new_chat",
):

    st.session_state.messages = []

    st.rerun()


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
# البحث على الإنترنت
# =========================================================

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
        "دلوقت",
        "الآن",
        "حاليًا",
        "حاليا",
        "أحدث",
        "آخر",
        "اخر",
        "today",
        "now",
        "latest",
        "news",
        "weather",
        "price",
        "score",
    ]

    low = (
        text or ""
    ).lower()

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
                "User-Agent": "YosefAI/1.0",
            },
            timeout=8,
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
            parts.append(
                abstract
            )

        topics = data.get(
            "RelatedTopics",
            [],
        )

        for item in topics[:5]:

            if isinstance(
                item,
                dict,
            ):

                item_text = item.get(
                    "Text",
                    "",
                )

                item_url = item.get(
                    "FirstURL",
                    "",
                )

                if item_text:
                    parts.append(
                        item_text
                    )

                if item_url:
                    parts.append(
                        item_url
                    )

        return "\n\n".join(
            parts[:10]
        )

    except Exception:

        return ""


# =========================================================
# قراءة الملفات
# =========================================================

def read_file(file):

    if not file:
        return ""

    try:

        data = file.getvalue()

        name = (
            file.name or ""
        ).lower()


        if name.endswith(
            ".txt"
        ):

            return data.decode(
                "utf-8",
                errors="ignore",
            )


        if name.endswith(
            ".pdf"
        ):

            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(data)
            )

            parts = []

            for page in reader.pages:

                parts.append(
                    page.extract_text()
                    or ""
                )

            return "\n".join(
                parts
            )


        if name.endswith(
            ".docx"
        ):

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

            return "\n".join(
                parts
            )

    except Exception:

        return ""

    return ""


# =========================================================
# تحويل الصوت إلى نص
# =========================================================

def audio_to_text(audio):

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
        language="ar-EG",
    )


# =========================================================
# إرسال الطلب
# =========================================================

def ask_yosef(
    text,
    extra_content=None,
):

    content = [
        {
            "type": "text",
            "text": text or "",
        }
    ]


    if extra_content:

        content.extend(
            extra_content
        )


    # البحث عند الحاجة
    if needs_search(text):

        search_result = search_web(
            text
        )

        if search_result:

            content.append(
                {
                    "type": "text",
                    "text": (
                        "معلومات حديثة من البحث:\n\n"
                        + search_result[:10000]
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
        st.session_state.messages[-16:]
    )


    messages.append(
        {
            "role": "user",
            "content": content,
        }
    )


    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.4,
            stream=True,
            extra_body={
                "reasoning": {
                    "exclude": True
                }
            },
        )

        return response

    except Exception as error:

        error_text = str(error)

        if (
            "429" in error_text
            or "free-models-per-day" in error_text
        ):

            st.warning(
                "⏳ الحد المجاني في OpenRouter انتهى حاليًا."
            )

        else:

            st.error(
                "❌ حصل خطأ أثناء تشغيل Yosef AI."
            )

        return None


# =========================================================
# خانة الشات
# + صورة
# + ملف
# + صوت
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

        text = (
            prompt.text or ""
        )

        uploaded_file = None


        if prompt.files:

            uploaded_file = (
                prompt.files[0]
            )


        # =================================================
        # الصوت
        # =================================================

        if prompt.audio:

            try:

                text = audio_to_text(
                    prompt.audio
                )

            except sr.UnknownValueError:

                st.error(
                    "❌ مش قادر أفهم التسجيل."
                )

                st.stop()

            except sr.RequestError:

                st.error(
                    "❌ خدمة الصوت غير متاحة حاليًا."
                )

                st.stop()


        # =================================================
        # تجهيز المحتوى الإضافي
        # =================================================

        extra_content = []


        if uploaded_file:

            file_type = (
                uploaded_file.type or ""
            )


            # =================================================
            # صورة
            # =================================================

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
            # ملف
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
                                "محتوى الملف:\n\n"
                                + file_text[:20000]
                            ),
                        }
                    )

                else:

                    extra_content.append(
                        {
                            "type": "text",
                            "text": (
                                "الملف المرفق اسمه: "
                                + uploaded_file.name
                            ),
                        }
                    )


        # =================================================
        # التأكد من وجود رسالة
        # =================================================

        if (
            not text
            and not uploaded_file
        ):

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
        # إرسال
        # =================================================

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "🤖 بيفكر..."
            ):

                stream_response = ask_yosef(
                    text,
                    extra_content,
                )


            if stream_response is None:

                st.stop()


            full_answer = ""


            try:

                for chunk in stream_response:

                    if not chunk.choices:
                        continue

                    delta = (
                        chunk
                        .choices[0]
                        .delta
                    )

                    piece = (
                        delta.content
                        or ""
                    )

                    if piece:

                        full_answer += piece

                        st.write(
                            full_answer
                        )

            except Exception:

                full_answer = ""


            if not full_answer:

                st.error(
                    "لم يصل رد من النموذج."
                )

                st.stop()


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
                "content": full_answer,
            }
        )


    except Exception as error:

        st.error(
            "❌ حصل خطأ: "
            + str(error)
    )
