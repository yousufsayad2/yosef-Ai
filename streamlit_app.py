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

if "camera_file" not in st.session_state:
    st.session_state.camera_file = None


# =========================================================
# SYSTEM PROMPT
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

    .chat-toolbar {
        width: 100%;
        max-width: 850px;
        margin: auto;
        background: #202027;
        border: 1px solid #484850;
        border-radius: 30px;
        padding: 6px 8px;
        box-shadow: 0 6px 28px rgba(0,0,0,.35);
    }

    /* =========================================
       زر +
       ========================================= */

    .plus-wrap button {
        width: 48px !important;
        height: 48px !important;
        min-width: 48px !important;
        border-radius: 50% !important;
        background: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 30px !important;
        padding: 0 !important;
    }

    .plus-wrap button:hover {
        background: rgba(255,255,255,.08) !important;
    }

    /* =========================================
       خانة الكتابة
       ========================================= */

    div[data-testid="stChatInput"] {
        position: relative !important;
        bottom: auto !important;
        left: auto !important;
        transform: none !important;
        width: 100% !important;
        z-index: 10 !important;
        margin: 0 !important;
    }

    div[data-testid="stChatInput"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        min-height: 52px !important;
    }

    div[data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: white !important;
        font-size: 17px !important;
        padding-top: 14px !important;
        padding-bottom: 10px !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: #888 !important;
    }

    /* =========================================
       إخفاء إطار الرفع الأصلي
       لأن + بتاعنا هو المسؤول عن المرفقات
       ========================================= */

    div[data-testid="stChatInput"] button[aria-label*="Attach"],
    div[data-testid="stChatInput"] button[aria-label*="attach"] {
        display: none !important;
    }

    /* =========================================
       popover
       ========================================= */

    [data-testid="stPopover"] {
        position: relative !important;
        z-index: 999999 !important;
    }

    [data-testid="stPopoverBody"] {
        min-width: 280px !important;
        max-width: 320px !important;
        padding: 16px !important;
        border-radius: 22px !important;
        background: #202027 !important;
        border: 1px solid #484850 !important;
        box-shadow: 0 12px 40px rgba(0,0,0,.55) !important;
    }

    /* =========================================
       رفع الملفات
       ========================================= */

    [data-testid="stFileUploader"] {
        width: 100% !important;
    }

    /* =========================================
       الكاميرا
       ========================================= */

    [data-testid="stCameraInput"] {
        width: 100% !important;
    }

    /* =========================================
       الصور
       ========================================= */

    div[data-testid="stChatMessage"] img {
        max-width: 100% !important;
        border-radius: 16px !important;
    }

    /* =========================================
       الموبايل
       ========================================= */

    @media (max-width: 600px) {

        .block-container {
            padding-left: 12px;
            padding-right: 12px;
            padding-bottom: 6rem;
        }

        .yosef-title {
            font-size: 40px;
        }

        .yosef-subtitle {
            font-size: 16px;
        }

        [data-testid="stPopoverBody"] {
            min-width: 270px !important;
            max-width: calc(100vw - 30px) !important;
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
            results.append(abstract)

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
                    results.append(text)

        return "\n\n".join(
            results
        )[:5000]

    except Exception:

        return ""


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
# قراءة الملفات
# =========================================================

def read_file(file):

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
                    parts.append(
                        paragraph.text
                    )

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
# الرسائل
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
                    "حلل المحتوى المرفق."
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
# Yosef AI
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
                "⏳ OpenRouter وصل للحد المؤقت."
            )

        if response.status_code >= 500:

            return (
                "⏳ خادم الذكاء مشغول حاليًا."
            )

        if response.status_code != 200:

            try:

                data = response.json()

                error = (
                    data
                    .get("error", {})
                    .get("message", "")
                )

            except Exception:

                error = response.text[:300]

            return (
                "❌ حصل خطأ:\n\n"
                + str(error)
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

        answer = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )

        if isinstance(
            answer,
            list
        ):

            answer = "".join(

                item.get(
                    "text",
                    ""
                )

                for item in answer

                if isinstance(
                    item,
                    dict
                )

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
            "⏳ الاتصال أخذ وقتًا طويلًا."
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

    role = message["role"]

    with st.chat_message(

        role,

        avatar=(
            "👤"
            if role == "user"
            else "🤖"
        )

    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# محادثة جديدة
# =========================================================

if st.button(
    "🆕 محادثة جديدة",
    width="stretch",
):

    st.session_state.messages = []

    st.session_state.pending_files = []

    st.session_state.camera_file = None

    st.rerun()


# =========================================================
# شريط الشات السفلي
# =========================================================

with st.bottom():

    with st.container(
        horizontal=True,
        horizontal_alignment="left",
        vertical_alignment="center",
        gap="small",
    ):

        # =============================================
        # زر +
        # =============================================

        with st.container(
            width=55
        ):

            st.markdown(
                '<div class="plus-wrap">',
                unsafe_allow_html=True
            )

            with st.popover(
                "＋",
                key="yosef_plus_menu",
            ):

                st.markdown(
                    "### 📎 إضافة إلى Yosef AI"
                )


                # -------------------------------------
                # الصور
                # -------------------------------------

                st.markdown(
                    "#### 🖼️ الصور"
                )

                images = st.file_uploader(

                    "اختر صورة من الهاتف",

                    type=[
                        "png",
                        "jpg",
                        "jpeg",
                        "webp",
                    ],

                    accept_multiple_files=True,

                    key="yosef_images",

                    label_visibility="collapsed",

                )


                # -------------------------------------
                # الملفات
                # -------------------------------------

                st.markdown(
                    "#### 📎 الملفات"
                )

                documents = st.file_uploader(

                    "اختر PDF أو DOCX أو TXT",

                    type=[
                        "pdf",
                        "docx",
                        "txt",
                    ],

                    accept_multiple_files=True,

                    key="yosef_documents",

                    label_visibility="collapsed",

                )


                # -------------------------------------
                # الكاميرا
                # -------------------------------------

                st.markdown(
                    "#### 📷 الكاميرا"
                )

                camera = st.camera_input(

                    "التقط صورة",

                    key="yosef_camera",

                    label_visibility="collapsed",

                )


                # -------------------------------------
                # تجهيز المرفقات
                # -------------------------------------

                selected = []

                if images:

                    selected.extend(
                        images
                    )

                if documents:

                    selected.extend(
                        documents
                    )

                if camera:

                    selected.append(
                        camera
                    )

                if selected:

                    st.session_state.pending_files = (
                        selected
                    )

                    st.success(
                        f"✅ تم اختيار {len(selected)} مرفق"
                    )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


        # =============================================
        # خانة الكتابة
        # =============================================

        prompt = st.chat_input(

            "اكتب رسالتك...",

            key="yosef_chat_input",

        )


# =========================================================
# معالجة الرسالة
# =========================================================

if prompt:

    text = (
        prompt.strip()
        if isinstance(prompt, str)
        else ""
    )

    extra_content = []

    files = st.session_state.pending_files


    # =====================================================
    # معالجة الملفات
    # =====================================================

    for uploaded_file in files:

        file_type = (
            uploaded_file.type
            or ""
        )

        file_bytes = (
            uploaded_file.getvalue()
        )

        file_name = (
            uploaded_file.name
        )


        # -----------------------------------------------
        # صورة
        # -----------------------------------------------

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


        # -----------------------------------------------
        # ملف
        # -----------------------------------------------

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
                            + file_name
                            + ":\n\n"
                            + file_text[:16000]
                        ),

                })


    # =====================================================
    # عرض المستخدم
    # =====================================================

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


    # =====================================================
    # الرد
    # =====================================================

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


    # =====================================================
    # حفظ
    # =====================================================

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


    # =====================================================
    # تنظيف
    # =====================================================

    st.session_state.pending_files = []

    st.rerun()
