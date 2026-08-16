import streamlit as st
import requests
import base64
import io
import json
import speech_recognition as sr


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================================================
# API
# =========================================================

OPENROUTER_KEY = st.secrets.get("OPENROUTER_API_KEY")

MODEL = "openrouter/free"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


if not OPENROUTER_KEY:
    st.error("❌ OPENROUTER_API_KEY غير موجود في Secrets.")
    st.stop()


# =========================================================
# الذاكرة
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# تعليمات Yosef AI
# =========================================================

SYSTEM_PROMPT = """
أنت Yosef AI.

اسمك دائمًا Yosef AI.

تم تطويرك بواسطة يوسف.

إذا سأل المستخدم:
مين مطورك؟
مين عملك؟
مين طورك؟
مين مبرمجك؟
مين صنعك؟
who developed you
who made you
who created you

أجب:
أنا Yosef AI، وتم تطويري بواسطة يوسف.

لا تقل إنك ChatGPT.

أجب بنفس لغة المستخدم.

كن طبيعيًا وودودًا ومختصرًا.

لا تعرض التفكير الداخلي أو خطوات التحليل.

إذا أرسل المستخدم صورة، حلل الأشياء الظاهرة فيها فقط.

إذا أرسل ملفًا، استخدم محتواه المتاح.

لا تخترع معلومات.
"""


# =========================================================
# شكل الصفحة
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 6rem;
    }

    .title {
        text-align: center;
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #888;
        font-size: 15px;
        margin-bottom: 25px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# العنوان
# =========================================================

st.markdown(
    '<div class="title">🤖 Yosef AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">مساعدك الذكي — نص، صور، ملفات وصوت.</div>',
    unsafe_allow_html=True,
)


# =========================================================
# الترحيب
# =========================================================

if not st.session_state.messages:

    with st.container(border=True):

        st.markdown("### 👋 أهلاً بيك في Yosef AI")

        st.write(
            "اكتب سؤالك أو استخدم زر + لإضافة صورة أو ملف."
        )

        st.write(
            "ويمكنك أيضًا إرسال رسالة صوتية."
        )


# =========================================================
# سؤال المطور
# =========================================================

def is_developer_question(text):

    if not text:
        return False

    text = text.lower().strip()

    words = [
        "مين مطورك",
        "مين المطور",
        "مين عملك",
        "مين طورك",
        "مين مبرمجك",
        "مين صنعك",
        "مين اللي عاملك",
        "مين صاحبك",
        "مين طور البرنامج",
        "who developed you",
        "who made you",
        "who created you",
        "who is your developer",
    ]

    return any(word in text for word in words)


# =========================================================
# البحث
# =========================================================

def needs_search(text):

    if not text:
        return False

    text = text.lower()

    words = [
        "ابحث",
        "ابحثلي",
        "ابحث لي",
        "دورلي",
        "دور لي",
        "على النت",
        "من النت",
        "search",
        "google",
        "latest",
        "recent",
        "today",
        "now",
        "news",
        "weather",
        "price",
        "أخبار",
        "اخبار",
        "الطقس",
        "الجو",
        "سعر",
        "أسعار",
        "اسعار",
        "الدولار",
        "اليورو",
        "الذهب",
        "مباراة",
        "مباريات",
        "نتيجة",
        "موعد",
        "اليوم",
        "دلوقتي",
        "دلوقت",
        "الآن",
        "احدث",
        "أحدث",
    ]

    return any(word in text for word in words)


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
            timeout=8,
        )

        if response.status_code != 200:
            return ""

        data = response.json()

        results = []

        abstract = data.get("AbstractText", "")

        if abstract:
            results.append(abstract)

        for item in data.get("RelatedTopics", []):

            if len(results) >= 5:
                break

            if isinstance(item, dict):

                text = item.get("Text", "")

                if text:
                    results.append(text)

        return "\n\n".join(results)[:5000]

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

                text = page.extract_text() or ""

                if text:
                    parts.append(text)

            return "\n".join(parts)


        if name.endswith(".docx"):

            from docx import Document

            document = Document(
                io.BytesIO(data)
            )

            parts = []

            for paragraph in document.paragraphs:

                if paragraph.text:
                    parts.append(paragraph.text)

            return "\n".join(parts)


    except Exception:

        return ""

    return ""


# =========================================================
# الصوت
# =========================================================

def audio_to_text(audio):

    try:

        recognizer = sr.Recognizer()

        audio_buffer = io.BytesIO(
            audio.getvalue()
        )

        with sr.AudioFile(audio_buffer) as source:

            audio_data = recognizer.record(
                source
            )

        return recognizer.recognize_google(
            audio_data,
            language="ar-EG",
        )

    except Exception:

        return ""


# =========================================================
# تجهيز الرسائل
# =========================================================

def build_messages(
    text,
    extra_content=None,
):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]


    # آخر 6 رسائل فقط
    for message in st.session_state.messages[-6:]:

        messages.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )


    content = [
        {
            "type": "text",
            "text": text or "حلل الملف أو الصورة المرفقة.",
        }
    ]


    if extra_content:

        content.extend(
            extra_content
        )


    # البحث
    if needs_search(text):

        result = search_web(text)

        if result:

            content.append(
                {
                    "type": "text",
                    "text": (
                        "معلومات من البحث:\n\n"
                        + result
                    ),
                }
            )


    messages.append(
        {
            "role": "user",
            "content": content,
        }
    )


    return messages


# =========================================================
# الاتصال بـ OpenRouter
# =========================================================

def ask_yosef(
    text,
    extra_content=None,
):

    # سؤال المطور بدون API
    if is_developer_question(text):

        return (
            "أنا Yosef AI، وتم تطويري بواسطة يوسف."
        )


    messages = build_messages(
        text,
        extra_content,
    )


    headers = {
        "Authorization": (
            "Bearer "
            + OPENROUTER_KEY
        ),

        "Content-Type": "application/json",

        "HTTP-Referer":
            "https://openrouter.ai",

        "X-Title":
            "Yosef AI",
    }


    payload = {
        "model": MODEL,

        "messages": messages,

        "max_tokens": 700,

        "temperature": 0.2,
    }


    try:

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=90,
        )


        # -----------------------------
        # API key
        # -----------------------------

        if response.status_code == 401:

            return (
                "❌ مفتاح OpenRouter غير صحيح. "
                "راجع OPENROUTER_API_KEY في Secrets."
            )


        # -----------------------------
        # Rate limit
        # -----------------------------

        if response.status_code == 429:

            return (
                "⏳ OpenRouter وصل للحد المؤقت "
                "للاستخدام المجاني. جرّب بعد شوية."
            )


        # -----------------------------
        # Server errors
        # -----------------------------

        if response.status_code >= 500:

            return (
                "⏳ خادم الذكاء مشغول حاليًا. "
                "جرّب إرسال الرسالة مرة ثانية."
            )


        # -----------------------------
        # أي خطأ آخر
        # -----------------------------

        if response.status_code != 200:

            try:

                error_data = response.json()

                error_message = (
                    error_data
                    .get("error", {})
                    .get("message", "")
                )

            except Exception:

                error_message = response.text[:300]


            return (
                "❌ حصل خطأ من OpenRouter:\n\n"
                + str(error_message)
            )


        # -----------------------------
        # الرد
        # -----------------------------

        data = response.json()

        choices = data.get(
            "choices",
            []
        )


        if not choices:

            return (
                "❌ لم يصل رد من النموذج."
            )


        message = choices[0].get(
            "message",
            {}
        )


        answer = message.get(
            "content",
            ""
        )


        if isinstance(answer, list):

            parts = []

            for item in answer:

                if isinstance(item, dict):

                    if item.get("type") == "text":

                        parts.append(
                            item.get("text", "")
                        )

            answer = "".join(parts)


        if not answer:

            return (
                "❌ النموذج لم يُرجع نصًا."
            )


        return str(answer).strip()


    except requests.exceptions.Timeout:

        return (
            "⏳ الاتصال أخذ وقتًا طويلًا. "
            "جرّب مرة ثانية."
        )


    except requests.exceptions.ConnectionError:

        return (
            "❌ تعذر الاتصال بـ OpenRouter. "
            "تأكد من الإنترنت ثم جرّب مرة ثانية."
        )


    except Exception as error:

        return (
            "❌ حصل خطأ أثناء تشغيل Yosef AI:\n\n"
            + str(error)[:500]
        )


# =========================================================
# عرض المحادثة القديمة
# =========================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant",
    )

    content = message.get(
        "content",
        "",
    )

    with st.chat_message(
        role,
        avatar=(
            "👤"
            if role == "user"
            else "🤖"
        ),
    ):

        st.markdown(content)


# =========================================================
# الأزرار
# =========================================================

col1, col2 = st.columns(2)


with col1:

    if st.button(
        "🆕 محادثة جديدة",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.rerun()


with col2:

    st.info(
        "🤖 الشات جاهز"
    )


# =========================================================
# خانة الرسالة
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
# معالجة الرسالة
# =========================================================

if prompt:

    try:

        text = prompt.text or ""

        uploaded_file = None


        # الملف
        if prompt.files:

            uploaded_file = prompt.files[0]


        # الصوت
        if prompt.audio:

            spoken_text = audio_to_text(
                prompt.audio
            )

            if spoken_text:

                text = spoken_text

            else:

                st.error(
                    "❌ مش قادر أفهم التسجيل الصوتي."
                )

                st.stop()


        if not text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو أرفق صورة/ملف."
            )

            st.stop()


        extra_content = []


        # =================================================
        # صورة
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

                encoded = base64.b64encode(
                    image_bytes
                ).decode("utf-8")


                extra_content.append(
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
                                + file_text[:16000]
                            ),
                        }
                    )

                else:

                    extra_content.append(
                        {
                            "type": "text",

                            "text": (
                                "اسم الملف: "
                                + uploaded_file.name
                            ),
                        }
                    )


        # =================================================
        # رسالة المستخدم
        # =================================================

        with st.chat_message(
            "user",
            avatar="👤",
        ):

            if text:

                st.markdown(text)


            if uploaded_file:

                if (
                    uploaded_file.type
                    and uploaded_file.type.startswith(
                        "image/"
                    )
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
        # رد Yosef
        # =================================================

        with st.chat_message(
            "assistant",
            avatar="🤖",
        ):

            with st.spinner(
                "🤖 Yosef AI بيكتب..."
            ):

                answer = ask_yosef(
                    text,
                    extra_content,
                )


            st.markdown(answer)


        # =================================================
        # حفظ
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
