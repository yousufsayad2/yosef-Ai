import streamlit as st
import requests
import base64
import io
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

OPENROUTER_KEY = st.secrets.get(
    "OPENROUTER_API_KEY",
    ""
)

MODEL = "openrouter/free"

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)


if not OPENROUTER_KEY:

    st.error(
        "❌ OPENROUTER_API_KEY غير موجود في Secrets."
    )

    st.stop()


# =========================================================
# الذاكرة
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


if "camera_image" not in st.session_state:

    st.session_state.camera_image = None


# =========================================================
# تعليمات Yosef AI
# =========================================================

SYSTEM_PROMPT = """
أنت Yosef AI.

اسمك دائمًا Yosef AI.

تم تطويرك بواسطة يوسف.

إذا سأل المستخدم:
مين مطورك؟
مين المطور؟
مين عملك؟
مين طورك؟
مين مبرمجك؟
مين صنعك؟
مين اللي عاملك؟
مين صاحبك؟
مين طور البرنامج؟
who developed you
who made you
who created you
who is your developer

أجب:
أنا Yosef AI، وتم تطويري بواسطة يوسف.

لا تقل إنك ChatGPT.

أجب بنفس لغة المستخدم.

كن طبيعيًا وودودًا ومختصرًا.

لا تعرض التفكير الداخلي أو خطوات التحليل.

إذا أرسل المستخدم صورة:
حلل الأشياء الظاهرة فيها فقط.

إذا أرسل المستخدم ملفًا:
استخدم محتواه المتاح.

إذا أرسل المستخدم صوتًا:
استخدم النص المستخرج من التسجيل.

لا تخترع معلومات.
"""


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }

    .title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
        color: white;
    }

    .subtitle {
        text-align: center;
        color: #888;
        font-size: 17px;
        margin-bottom: 25px;
    }

    /* ================================
       الشات
       ================================ */

    div[data-testid="stChatInput"] {
        z-index: 999999 !important;
    }

    div[data-testid="stChatInput"] > div {
        border-radius: 28px !important;
        min-height: 62px !important;
        background: #202027 !important;
        border: 1px solid #484850 !important;
        box-shadow: 0 5px 25px rgba(0,0,0,.30) !important;
    }

    div[data-testid="stChatInput"] textarea {
        color: white !important;
        background: transparent !important;
        font-size: 17px !important;
        padding-top: 16px !important;
        padding-bottom: 12px !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: #888 !important;
    }

    /* زر المرفقات الأصلي
       نخليه + بدل أيقونة الورق */
    div[data-testid="stChatInput"] button[aria-label*="attach"],
    div[data-testid="stChatInput"] button[aria-label*="Attach"] {
        border-radius: 50% !important;
    }

    /* الصور داخل المحادثة */

    div[data-testid="stChatMessage"] img {
        max-width: 100% !important;
        border-radius: 16px !important;
    }

    /* الكاميرا */

    .camera-box {
        margin-top: 10px;
        margin-bottom: 15px;
    }

    /* الموبايل */

    @media (max-width: 600px) {

        .block-container {
            padding-left: 12px;
            padding-right: 12px;
            padding-bottom: 7rem;
        }

        .title {
            font-size: 40px;
        }

        .subtitle {
            font-size: 16px;
        }

        div[data-testid="stChatInput"] > div {
            border-radius: 27px !important;
            min-height: 58px !important;
        }

        div[data-testid="stChatInput"] textarea {
            font-size: 16px !important;
        }
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
    '<div class="subtitle">'
    'مساعدك الذكي — نص، صور، ملفات وصوت.'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# الترحيب
# =========================================================

if not st.session_state.messages:

    with st.container(border=True):

        st.markdown(
            "### 👋 أهلاً بيك في Yosef AI"
        )

        st.write(
            "اكتب رسالتك أو اضغط علامة + لإضافة صورة أو ملف."
        )

        st.write(
            "ويمكنك تسجيل رسالة صوتية من زر الميكروفون."
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

    return any(
        word in text
        for word in words
    )


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

    return any(
        word in text
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
                "User-Agent":
                    "YosefAI/1.0"
            },

            timeout=8,
        )

        if response.status_code != 200:

            return ""

        data = response.json()

        results = []

        abstract = data.get(
            "AbstractText",
            ""
        )

        if abstract:

            results.append(
                abstract
            )

        for item in data.get(
            "RelatedTopics",
            []
        ):

            if len(results) >= 5:

                break

            if isinstance(
                item,
                dict
            ):

                text = item.get(
                    "Text",
                    ""
                )

                if text:

                    results.append(
                        text
                    )

        return "\n\n".join(
            results
        )[:5000]

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


        # TXT

        if name.endswith(".txt"):

            return data.decode(
                "utf-8",
                errors="ignore"
            )


        # PDF

        if name.endswith(".pdf"):

            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(data)
            )

            parts = []

            for page in reader.pages:

                text = (
                    page.extract_text()
                    or ""
                )

                if text:

                    parts.append(
                        text
                    )

            return "\n".join(parts)


        # DOCX

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


    except Exception as error:

        return (
            "تعذر قراءة الملف: "
            + str(error)
        )

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
            "role":
                "system",

            "content":
                SYSTEM_PROMPT,
        }

    ]


    for message in (
        st.session_state.messages[-6:]
    ):

        messages.append({

            "role":
                message["role"],

            "content":
                message["content"],

        })


    content = [

        {
            "type":
                "text",

            "text":
                (
                    text
                    if text
                    else
                    "حلل الملف أو الصورة المرفقة."
                ),
        }

    ]


    if extra_content:

        content.extend(
            extra_content
        )


    if needs_search(text):

        result = search_web(text)

        if result:

            content.append({

                "type":
                    "text",

                "text":
                    (
                        "معلومات من البحث:\n\n"
                        + result
                    ),

            })


    messages.append({

        "role":
            "user",

        "content":
            content,

    })


    return messages


# =========================================================
# OpenRouter
# =========================================================

def ask_yosef(
    text,
    extra_content=None,
):

    if is_developer_question(text):

        return (
            "أنا Yosef AI، وتم تطويري بواسطة يوسف."
        )


    messages = build_messages(
        text,
        extra_content,
    )


    headers = {

        "Authorization":
            "Bearer "
            + OPENROUTER_KEY,

        "Content-Type":
            "application/json",

        "HTTP-Referer":
            "https://openrouter.ai",

        "X-Title":
            "Yosef AI",
    }


    payload = {

        "model":
            MODEL,

        "messages":
            messages,

        "max_tokens":
            700,

        "temperature":
            0.2,
    }


    try:

        response = requests.post(

            OPENROUTER_URL,

            headers=headers,

            json=payload,

            timeout=90,
        )


        if response.status_code == 401:

            return (
                "❌ مفتاح OpenRouter غير صحيح."
            )


        if response.status_code == 429:

            return (
                "⏳ OpenRouter وصل للحد المؤقت. "
                "جرّب بعد شوية."
            )


        if response.status_code >= 500:

            return (
                "⏳ خادم الذكاء مشغول حاليًا."
            )


        if response.status_code != 200:

            try:

                error_data = response.json()

                error_message = (
                    error_data
                    .get("error", {})
                    .get("message", "")
                )

            except Exception:

                error_message = (
                    response.text[:300]
                )

            return (
                "❌ حصل خطأ من OpenRouter:\n\n"
                + str(error_message)
            )


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


        if isinstance(
            answer,
            list
        ):

            parts = []

            for item in answer:

                if isinstance(
                    item,
                    dict
                ):

                    parts.append(
                        item.get(
                            "text",
                            ""
                        )
                    )

            answer = "".join(parts)


        if not answer:

            return (
                "❌ النموذج لم يُرجع نصًا."
            )


        return str(
            answer
        ).strip()


    except requests.exceptions.Timeout:

        return (
            "⏳ الاتصال أخذ وقتًا طويلًا. "
            "جرّب مرة ثانية."
        )


    except requests.exceptions.ConnectionError:

        return (
            "❌ تعذر الاتصال بـ OpenRouter."
        )


    except Exception as error:

        return (
            "❌ حصل خطأ:\n\n"
            + str(error)[:500]
        )


# =========================================================
# عرض المحادثة
# =========================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant"
    )

    content = message.get(
        "content",
        ""
    )

    with st.chat_message(

        role,

        avatar=(
            "👤"
            if role == "user"
            else "🤖"
        )

    ):

        st.markdown(
            content
        )


# =========================================================
# زر محادثة جديدة
# =========================================================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True,
):

    st.session_state.messages = []

    st.rerun()


# =========================================================
# الكاميرا
# =========================================================
#
# زر الكاميرا مستقل لأن Streamlit لا يوفر اختيار
# الكاميرا داخل زر Attach الخاص بـ chat_input.
#
# =========================================================

with st.expander(
    "📷 التقاط صورة بالكاميرا"
):

    camera_file = st.camera_input(
        "التقط صورة",
        key="yosef_camera",
        label_visibility="visible",
    )

    if camera_file is not None:

        st.session_state.camera_image = (
            camera_file.getvalue()
        )

        st.success(
            "✅ الصورة جاهزة للإرسال."
        )


# =========================================================
# خانة الشات
# =========================================================
#
# مهم:
# accept_file = multiple
# يجعل زر + الأصلي داخل خانة الشات يعمل
# فعليًا لرفع الصور والملفات.
#
# accept_audio = True
# يجعل الميكروفون الأصلي داخل الشات يعمل.
#
# =========================================================

prompt = st.chat_input(

    "اكتب رسالتك...",

    key="yosef_chat_input",

    accept_file="multiple",

    accept_audio=True,

    audio_sample_rate=16000,

    max_upload_size=200,

    file_type=[

        "png",
        "jpg",
        "jpeg",
        "webp",

        "pdf",
        "docx",
        "txt",

    ],

)


# =========================================================
# معالجة الرسالة
# =========================================================

if prompt:

    try:

        text = (
            prompt.text
            or ""
        ).strip()


        uploaded_files = (

            list(prompt.files)

            if getattr(
                prompt,
                "files",
                None
            )

            else []

        )


        # =====================================================
        # الصوت
        # =====================================================

        if getattr(
            prompt,
            "audio",
            None
        ):

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


        # =====================================================
        # صورة الكاميرا
        # =====================================================

        if st.session_state.camera_image:

            camera_bytes = (
                st.session_state.camera_image
            )

            uploaded_files.append(
                {
                    "name":
                        "camera_photo.jpg",

                    "type":
                        "image/jpeg",

                    "data":
                        camera_bytes,

                    "camera":
                        True,
                }
            )

            st.session_state.camera_image = None


        # =====================================================
        # التحقق
        # =====================================================

        if (
            not text
            and not uploaded_files
        ):

            st.warning(
                "اكتب رسالة أو أرفق صورة/ملف."
            )

            st.stop()


        extra_content = []


        # =====================================================
        # معالجة الملفات
        # =====================================================

        for uploaded_file in uploaded_files:


            # الكاميرا

            if isinstance(
                uploaded_file,
                dict
            ):

                file_name = (
                    uploaded_file["name"]
                )

                file_type = (
                    uploaded_file["type"]
                )

                file_bytes = (
                    uploaded_file["data"]
                )


            # upload عادي

            else:

                file_name = (
                    uploaded_file.name
                )

                file_type = (
                    uploaded_file.type
                    or ""
                )

                file_bytes = (
                    uploaded_file.getvalue()
                )


            # =================================================
            # صورة
            # =================================================

            if file_type.startswith(
                "image/"
            ):

                encoded = (
                    base64.b64encode(
                        file_bytes
                    )
                    .decode("utf-8")
                )


                extra_content.append({

                    "type":
                        "image_url",

                    "image_url": {

                        "url":
                            (
                                "data:"
                                + file_type
                                + ";base64,"
                                + encoded
                            )
                    },

                })


            # =================================================
            # ملف
            # =================================================

            else:

                file_text = ""

                try:

                    if isinstance(
                        uploaded_file,
                        dict
                    ):

                        class MemoryFile:

                            def __init__(
                                self,
                                name,
                                data
                            ):

                                self.name = name
                                self._data = data

                            def getvalue(
                                self
                            ):

                                return self._data


                        temp_file = MemoryFile(
                            file_name,
                            file_bytes
                        )

                        file_text = read_file(
                            temp_file
                        )

                    else:

                        file_text = read_file(
                            uploaded_file
                        )

                except Exception:

                    file_text = ""


                if file_text:

                    extra_content.append({

                        "type":
                            "text",

                        "text":
                            (
                                "محتوى الملف "
                                f"({file_name}):\n\n"
                                + file_text[:16000]
                            ),

                    })

                else:

                    extra_content.append({

                        "type":
                            "text",

                        "text":
                            (
                                "اسم الملف: "
                                + file_name
                            ),

                    })


        # =====================================================
        # رسالة المستخدم
        # =====================================================

        with st.chat_message(
            "user",
            avatar="👤",
        ):

            if text:

                st.markdown(
                    text
                )


            for uploaded_file in uploaded_files:

                if isinstance(
                    uploaded_file,
                    dict
                ):

                    file_name = (
                        uploaded_file["name"]
                    )

                    file_type = (
                        uploaded_file["type"]
                    )

                    file_bytes = (
                        uploaded_file["data"]
                    )

                    if file_type.startswith(
                        "image/"
                    ):

                        st.image(
                            file_bytes,
                            width=300
                        )

                    else:

                        st.caption(
                            "📎 "
                            + file_name
                        )

                else:

                    if (
                        uploaded_file.type
                        and
                        uploaded_file.type.startswith(
                            "image/"
                        )
                    ):

                        st.image(
                            uploaded_file,
                            width=300
                        )

                    else:

                        st.caption(
                            "📎 "
                            + uploaded_file.name
                        )


            if getattr(
                prompt,
                "audio",
                None
            ):

                st.audio(
                    prompt.audio
                )


        # =====================================================
        # رد Yosef
        # =====================================================

        with st.chat_message(
            "assistant",
            avatar="🤖",
        ):

            with st.spinner(
                "🤖 Yosef AI بيكتب..."
            ):

                answer = ask_yosef(
                    text,
                    extra_content
                )

            st.markdown(
                answer
            )


        # =====================================================
        # الحفظ
        # =====================================================

        saved_text = text


        if not saved_text:

            if uploaded_files:

                saved_text = (
                    "📎 تم إرسال مرفق"
                )

            else:

                saved_text = (
                    "🎤 رسالة صوتية"
                )


        st.session_state.messages.append({

            "role":
                "user",

            "content":
                saved_text,

        })


        st.session_state.messages.append({

            "role":
                "assistant",

            "content":
                answer,

        })


    except Exception as error:

        st.error(
            "❌ حصل خطأ: "
            + str(error)[:500]
                    )
