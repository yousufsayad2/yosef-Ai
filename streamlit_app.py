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
# Session State
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_files" not in st.session_state:
    st.session_state.pending_files = []

if "camera_data" not in st.session_state:
    st.session_state.camera_data = None

if "camera_name" not in st.session_state:
    st.session_state.camera_name = ""

if "upload_version" not in st.session_state:
    st.session_state.upload_version = 0


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
# التصميم
# =========================================================

st.markdown(
    """
    <style>

    /* =========================================
       الصفحة
       ========================================= */

    .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 8rem;
    }


    /* =========================================
       العنوان
       ========================================= */

    .yosef-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
        color: white;
    }

    .yosef-subtitle {
        text-align: center;
        color: #888;
        font-size: 17px;
        margin-bottom: 25px;
    }


    /* =========================================
       شريط الشات السفلي
       ========================================= */

    [data-testid="stBottom"] {
        background: transparent !important;
    }


    /* =========================================
       زر +
       ========================================= */

    .plus-button button {

        width: 48px !important;
        height: 48px !important;

        min-width: 48px !important;
        min-height: 48px !important;

        padding: 0 !important;

        border: none !important;

        border-radius: 50% !important;

        background: transparent !important;

        color: white !important;

        font-size: 31px !important;

        line-height: 48px !important;

        box-shadow: none !important;

    }


    .plus-button button:hover {

        background:
            rgba(255,255,255,0.08) !important;

    }


    /* =========================================
       الشات input
       ========================================= */

    div[data-testid="stChatInput"] {

        position: relative !important;

        left: auto !important;

        bottom: auto !important;

        transform: none !important;

        width: 100% !important;

        margin: 0 !important;

        z-index: 100 !important;

    }


    div[data-testid="stChatInput"] > div {

        background:
            #202027 !important;

        border:
            1px solid #4a4a52 !important;

        border-radius:
            28px !important;

        min-height:
            60px !important;

        box-shadow:
            0 6px 25px
            rgba(0,0,0,0.35) !important;

    }


    div[data-testid="stChatInput"] textarea {

        background:
            transparent !important;

        color:
            white !important;

        font-size:
            17px !important;

        line-height:
            1.5 !important;

        padding-top:
            16px !important;

        padding-bottom:
            12px !important;

        padding-left:
            10px !important;

        padding-right:
            55px !important;

    }


    div[data-testid="stChatInput"]
    textarea::placeholder {

        color:
            #888 !important;

    }


    /* =========================================
       زر الميكروفون
       ========================================= */

    .voice-button {

        width: 48px;

        height: 48px;

    }


    /* =========================================
       قائمة +
       ========================================= */

    [data-testid="stPopoverBody"] {

        min-width:
            290px !important;

        max-width:
            340px !important;

        padding:
            18px !important;

        border-radius:
            22px !important;

        background:
            #202027 !important;

        border:
            1px solid #4a4a52 !important;

        box-shadow:
            0 12px 40px
            rgba(0,0,0,0.55) !important;

    }


    /* =========================================
       رفع الملفات
       ========================================= */

    [data-testid="stFileUploader"] {

        width:
            100% !important;

    }


    /* =========================================
       الكاميرا
       ========================================= */

    [data-testid="stCameraInput"] {

        width:
            100% !important;

    }


    /* =========================================
       المرفقات
       ========================================= */

    .attachment-box {

        background:
            #25252d;

        border:
            1px solid #41414a;

        border-radius:
            16px;

        padding:
            10px;

        margin-bottom:
            10px;

    }


    /* =========================================
       الصور
       ========================================= */

    div[data-testid="stChatMessage"] img {

        max-width:
            100% !important;

        border-radius:
            16px !important;

    }


    /* =========================================
       موبايل
       ========================================= */

    @media (max-width: 600px) {

        .block-container {

            padding-left:
                12px;

            padding-right:
                12px;

            padding-bottom:
                7rem;

        }


        .yosef-title {

            font-size:
                40px;

        }


        .yosef-subtitle {

            font-size:
                16px;

        }


        [data-testid="stPopoverBody"] {

            min-width:
                275px !important;

            max-width:
                calc(100vw - 30px) !important;

        }


        div[data-testid="stChatInput"] > div {

            min-height:
                58px !important;

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
    '<div class="yosef-title">🤖 Yosef AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="yosef-subtitle">'
    'مساعدك الذكي — نص، صور، ملفات وصوت.'
    '</div>',
    unsafe_allow_html=True,
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

                "q":
                    query,

                "format":
                    "json",

                "no_html":
                    "1",

                "skip_disambig":
                    "1",

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

                text = (
                    page.extract_text()
                    or ""
                )

                if text:
                    parts.append(
                        text
                    )

            return "\n".join(
                parts
            )


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

            return "\n".join(
                parts
            )


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

    except Exception:

        return ""


# =========================================================
# تجهيز الرسائل
# =========================================================

def build_messages(
    text,
    extra_content=None
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

        result = search_web(
            text
        )

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
# الاتصال بـ OpenRouter
# =========================================================

def ask_yosef(
    text,
    extra_content=None
):

    if is_developer_question(
        text
    ):

        return (
            "أنا Yosef AI، وتم تطويري بواسطة يوسف."
        )


    messages = build_messages(
        text,
        extra_content
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
                "⏳ OpenRouter وصل للحد المؤقت "
                "للاستخدام المجاني."
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

                    if item.get(
                        "type"
                    ) == "text":

                        parts.append(
                            item.get(
                                "text",
                                ""
                            )
                        )

            answer = "".join(
                parts
            )


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
            "❌ تعذر الاتصال بـ OpenRouter. "
            "تأكد من الإنترنت."
        )


    except Exception as error:

        return (
            "❌ حصل خطأ أثناء تشغيل Yosef AI:\n\n"
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
# محادثة جديدة
# =========================================================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):

    st.session_state.messages = []

    st.session_state.pending_files = []

    st.session_state.camera_data = None

    st.session_state.camera_name = ""

    st.rerun()


# =========================================================
# المرفقات المختارة
# =========================================================

if st.session_state.pending_files:

    st.markdown(
        "### 📎 المرفقات"
    )

    for uploaded in (
        st.session_state.pending_files
    ):

        file_type = (
            uploaded.type or ""
        )

        if file_type.startswith(
            "image/"
        ):

            st.image(
                uploaded,
                width=220
            )

        st.caption(
            "📎 "
            + uploaded.name
        )


if st.session_state.camera_data:

    st.markdown(
        "### 📷 صورة الكاميرا"
    )

    st.image(
        st.session_state.camera_data,
        width=220
    )

    st.caption(
        "📷 "
        + st.session_state.camera_name
    )


# =========================================================
# شريط الشات السفلي
# =========================================================

with st.bottom():

    # -----------------------------------------
    # زر +
    # -----------------------------------------

    plus_col, input_col, mic_col = st.columns(
        [0.10, 0.78, 0.12],
        vertical_alignment="center"
    )


    # =========================================
    # +
    # =========================================

    with plus_col:

        st.markdown(
            '<div class="plus-button">',
            unsafe_allow_html=True
        )

        with st.popover(
            "＋",
            key="yosef_plus"
        ):

            st.markdown(
                "## 📎 إضافة إلى Yosef AI"
            )


            # =====================================
            # الصور
            # =====================================

            st.markdown(
                "### 🖼️ الصور"
            )

            image_files = st.file_uploader(

                "اختار صورة من الهاتف",

                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp"
                ],

                accept_multiple_files=True,

                key="yosef_image_upload",

            )


            if image_files:

                st.session_state.pending_files = (
                    list(image_files)
                )

                st.success(
                    "✅ تم اختيار الصور"
                )


            # =====================================
            # الملفات
            # =====================================

            st.markdown(
                "### 📎 الملفات"
            )

            document_files = st.file_uploader(

                "اختار PDF أو DOCX أو TXT",

                type=[
                    "pdf",
                    "docx",
                    "txt"
                ],

                accept_multiple_files=True,

                key="yosef_document_upload",

            )


            if document_files:

                current = (
                    st.session_state.pending_files
                )

                names = {
                    x.name
                    for x in current
                }

                for file in document_files:

                    if file.name not in names:

                        current.append(
                            file
                        )

                st.session_state.pending_files = (
                    current
                )

                st.success(
                    "✅ تم اختيار الملفات"
                )


            # =====================================
            # الكاميرا
            # =====================================

            st.markdown(
                "### 📷 الكاميرا"
            )

            camera_file = st.camera_input(

                "التقط صورة",

                key="yosef_camera_input",

            )


            if camera_file:

                st.session_state.camera_data = (
                    camera_file.getvalue()
                )

                st.session_state.camera_name = (
                    "camera_photo.jpg"
                )

                st.success(
                    "✅ تم التقاط الصورة"
                )


            # =====================================
            # حذف المرفقات
            # =====================================

            if (
                st.session_state.pending_files
                or
                st.session_state.camera_data
            ):

                if st.button(
                    "🗑️ إزالة المرفقات",
                    use_container_width=True
                ):

                    st.session_state.pending_files = []

                    st.session_state.camera_data = None

                    st.session_state.camera_name = ""

                    st.rerun()


        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


    # =========================================
    # خانة الكتابة
    # =========================================

    with input_col:

        prompt = st.chat_input(
            "اكتب رسالتك...",
            key="yosef_chat_input"
        )


    # =========================================
    # الميكروفون
    # =========================================

    with mic_col:

        audio_file = st.audio_input(
            "🎤",
            key="yosef_audio",
            label_visibility="collapsed"
        )


# =========================================================
# إرسال الصوت
# =========================================================

if audio_file:

    with st.spinner(
        "🎤 جاري تحويل الصوت إلى نص..."
    ):

        voice_text = audio_to_text(
            audio_file
        )


    if voice_text:

        with st.chat_message(
            "user",
            avatar="👤"
        ):

            st.markdown(
                "🎤 " + voice_text
            )


        with st.chat_message(
            "assistant",
            avatar="🤖"
        ):

            with st.spinner(
                "🤖 Yosef AI بيكتب..."
            ):

                answer = ask_yosef(
                    voice_text
                )

            st.markdown(
                answer
            )


        st.session_state.messages.append({

            "role":
                "user",

            "content":
                "🎤 " + voice_text,

        })


        st.session_state.messages.append({

            "role":
                "assistant",

            "content":
                answer,

        })


        st.rerun()


    else:

        st.warning(
            "⚠️ لم أستطع فهم التسجيل الصوتي."
        )


# =========================================================
# إرسال الرسالة + المرفقات
# =========================================================

if prompt:

    text = prompt.strip()

    files = list(
        st.session_state.pending_files
    )

    extra_content = []


    # =============================================
    # إضافة صورة الكاميرا
    # =============================================

    if st.session_state.camera_data:

        class CameraFile:

            def __init__(
                self,
                data,
                name
            ):

                self._data = data
                self.name = name
                self.type = "image/jpeg"


            def getvalue(self):

                return self._data


        camera_object = CameraFile(

            st.session_state.camera_data,

            st.session_state.camera_name

        )

        files.append(
            camera_object
        )


    # =============================================
    # معالجة الملفات
    # =============================================

    for uploaded_file in files:

        file_type = (
            uploaded_file.type
            or ""
        )

        file_bytes = (
            uploaded_file.getvalue()
        )


        # =========================================
        # صورة
        # =========================================

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

                }

            })


        # =========================================
        # PDF / DOCX / TXT
        # =========================================

        else:

            file_text = read_file(
                uploaded_file
            )

            if file_text:

                extra_content.append({

                    "type":
                        "text",

                    "text":
                        (
                            "محتوى الملف "
                            + uploaded_file.name
                            + ":\n\n"
                            + file_text[:16000]
                        )

                })


    # =============================================
    # عرض رسالة المستخدم
    # =============================================

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        if text:

            st.markdown(
                text
            )


        for uploaded_file in files:

            file_type = (
                uploaded_file.type
                or ""
            )


            if file_type.startswith(
                "image/"
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


    # =============================================
    # رد Yosef
    # =============================================

    with st.chat_message(
        "assistant",
        avatar="🤖"
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


    # =============================================
    # حفظ
    # =============================================

    saved_text = text


    if not saved_text:

        if files:

            saved_text = (
                "📎 تم إرسال مرفق"
            )

        else:

            saved_text = (
                "رسالة بدون نص"
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


    # =============================================
    # تنظيف المرفقات
    # =============================================

    st.session_state.pending_files = []

    st.session_state.camera_data = None

    st.session_state.camera_name = ""

    st.rerun()
