import streamlit as st
import requests
import base64
import io
import speech_recognition as sr


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================================================
# SETTINGS
# =========================================================

OPENROUTER_KEY = st.secrets.get(
    "OPENROUTER_API_KEY",
    ""
)

MODEL = "openrouter/free"

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

PRO_PAYMENT_URL = st.secrets.get(
    "PRO_PAYMENT_URL",
    ""
)

PRO_CODE = st.secrets.get(
    "PRO_ACCESS_CODE",
    ""
)


if not OPENROUTER_KEY:
    st.error(
        "❌ مفتاح OPENROUTER_API_KEY غير موجود في Secrets."
    )
    st.stop()


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "plan" not in st.session_state:
    st.session_state.plan = "Free"

if "attached_files" not in st.session_state:
    st.session_state.attached_files = []

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =========================
       MAIN PAGE
       ========================= */

    .block-container {
        max-width: 900px !important;
        padding-top: 2rem !important;
        padding-bottom: 8rem !important;
    }


    /* =========================
       TITLE
       ========================= */

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
        margin-bottom: 25px;
        font-size: 18px;
    }


    /* =========================
       PLAN
       ========================= */

    .plan {
        padding: 16px;
        border-radius: 18px;
        text-align: center;
        margin-bottom: 15px;
        border: 1px solid #444;
        font-size: 18px;
    }


    /* =========================
       CHAT INPUT
       ========================= */

    div[data-testid="stChatInput"] {
        position: fixed !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        bottom: 12px !important;

        width:
            min(900px, calc(100% - 24px))
            !important;

        z-index: 999900 !important;
    }


    div[data-testid="stChatInput"] > div {
        background: #202027 !important;
        border: 1px solid #4a4a52 !important;
        border-radius: 28px !important;
        min-height: 60px !important;

        box-shadow:
            0 6px 25px
            rgba(0,0,0,0.35) !important;
    }


    div[data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: white !important;

        font-size: 17px !important;
        line-height: 1.5 !important;

        padding-top: 16px !important;
        padding-bottom: 12px !important;

        padding-left: 58px !important;
        padding-right: 60px !important;
    }


    div[data-testid="stChatInput"] textarea::placeholder {
        color: #888 !important;
    }


    div[data-testid="stChatInput"] button {
        border-radius: 50% !important;
    }


    /* =========================
       PLUS BUTTON
       مهم:
       لا نعمل fixed للـpopover نفسه
       ========================= */

    div[data-testid="stPopover"] {
        z-index: 1000000 !important;
    }


    div[data-testid="stPopover"] > button {
        width: 46px !important;
        height: 46px !important;

        min-width: 46px !important;
        min-height: 46px !important;

        padding: 0 !important;

        background: #202027 !important;

        border: 1px solid #555 !important;

        color: white !important;

        font-size: 30px !important;

        border-radius: 14px !important;

        box-shadow:
            0 4px 15px
            rgba(0,0,0,0.3) !important;
    }


    div[data-testid="stPopover"] > button:hover {
        background: #292930 !important;
    }


    /* =========================
       POPOVER
       ========================= */

    div[data-testid="stPopoverBody"] {
        background: #202027 !important;

        border: 1px solid #4a4a52 !important;

        border-radius: 20px !important;

        padding: 16px !important;

        min-width: 300px !important;

        max-width: 360px !important;

        box-shadow:
            0 10px 40px
            rgba(0,0,0,0.55) !important;
    }


    /* =========================
       UPLOAD TITLES
       ========================= */

    .upload-title {
        font-size: 19px;
        font-weight: 700;

        margin-top: 12px;
        margin-bottom: 8px;
    }


    /* =========================
       FILE UPLOADER
       ========================= */

    div[data-testid="stFileUploader"] {
        width: 100% !important;
    }


    div[data-testid="stFileUploader"] section {
        background: #292934 !important;

        border-radius: 15px !important;

        border: 1px solid #383844 !important;
    }


    div[data-testid="stFileUploader"] button {
        cursor: pointer !important;
    }


    /* =========================
       CAMERA
       ========================= */

    div[data-testid="stCameraInput"] {
        width: 100% !important;
    }


    /* =========================
       AUDIO INPUT
       خارج خانة الكتابة
       ========================= */

    div[data-testid="stAudioInput"] {
        position: fixed !important;

        z-index: 1000002 !important;

        bottom: 19px !important;

        right:
            max(
                62px,
                calc(
                    (100% - min(900px, calc(100% - 24px))) / 2
                    + 62px
                )
            ) !important;

        width: 48px !important;
        height: 48px !important;

        background: transparent !important;
    }


    div[data-testid="stAudioInput"] label {
        display: none !important;
    }


    div[data-testid="stAudioInput"] > div {
        padding: 0 !important;
        margin: 0 !important;

        background: transparent !important;

        border: none !important;
    }


    div[data-testid="stAudioInput"] button {
        width: 48px !important;
        height: 48px !important;

        min-width: 48px !important;
        min-height: 48px !important;

        border-radius: 50% !important;

        padding: 0 !important;
    }


    /* =========================
       CHAT IMAGES
       ========================= */

    div[data-testid="stChatMessage"] img {
        border-radius: 16px !important;
        max-width: 100% !important;
    }


    /* =========================
       MOBILE
       ========================= */

    @media (max-width: 600px) {

        .block-container {
            padding-left: 12px !important;
            padding-right: 12px !important;
            padding-bottom: 8rem !important;
        }


        .yosef-title {
            font-size: 40px;
        }


        .yosef-subtitle {
            font-size: 16px;
        }


        div[data-testid="stChatInput"] {
            width:
                calc(100% - 18px)
                !important;

            bottom: 10px !important;
        }


        div[data-testid="stChatInput"] > div {
            min-height: 58px !important;
            border-radius: 27px !important;
        }


        div[data-testid="stChatInput"] textarea {
            font-size: 16px !important;

            padding-left: 55px !important;
            padding-right: 55px !important;
        }


        /*
        مهم:
        لا نثبت الـPopover نفسه.
        نخلي Streamlit يتحكم فيه طبيعيًا.
        */


        div[data-testid="stPopover"] > button {
            width: 46px !important;
            height: 46px !important;
        }


        div[data-testid="stAudioInput"] {
            right: 58px !important;
            bottom: 16px !important;
        }


        div[data-testid="stPopoverBody"] {
            min-width: 280px !important;
            max-width: calc(100vw - 30px) !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="yosef-title">🤖 Yosef AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="yosef-subtitle">'
    'مساعدك الذكي للنصوص والصور والملفات والصوت'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# PLAN
# =========================================================

if st.session_state.plan == "Free":

    st.markdown(
        """
        <div class="plan">
            🆓 <b>Free</b><br>
            استخدام مجاني مفتوح
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        """
        <div class="plan">
            ⭐ <b>Yosef AI Pro</b><br>
            حساب Pro نشط
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
أنت Yosef AI.

اسمك Yosef AI.

تم تطويرك بواسطة يوسف.

إذا سألك المستخدم:
مين مطورك؟
مين المطور؟
مين عملك؟
مين طورك؟
مين مبرمجك؟
مين صنعك؟
مين اللي عاملك؟
مين طور البرنامج؟
who developed you
who made you
who created you
who is your developer

أجب:
أنا Yosef AI، وتم تطويري بواسطة يوسف.

لا تقل إنك ChatGPT.

أجب بنفس لغة المستخدم.

كن مفيدًا وطبيعيًا وواضحًا.

لا تعرض التفكير الداخلي.

إذا أرسل المستخدم صورة:
حلل الصورة والمعلومات الظاهرة فيها فقط.

إذا أرسل المستخدم ملفًا:
استخدم محتوى الملف المتاح لك.

إذا أرسل المستخدم صوتًا:
استخدم النص المستخرج من التسجيل.

لا تخترع معلومات.
"""


# =========================================================
# DEVELOPER QUESTION
# =========================================================

def developer_question(text):

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
# SEARCH
# =========================================================

def should_search(text):

    if not text:
        return False

    keywords = [
        "ابحث",
        "ابحثلي",
        "ابحث لي",
        "دورلي",
        "دور لي",
        "على النت",

        "search",
        "google",
        "latest",
        "today",
        "news",
        "weather",
        "price",

        "أخبار",
        "اخبار",
        "الطقس",
        "الجو",
        "سعر",
        "أسعار",
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
        "أحدث",
        "احدث",
    ]

    text = text.lower()

    return any(
        word in text
        for word in keywords
    )


def web_search(query):

    try:

        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            },
            timeout=8,
            headers={
                "User-Agent": "YosefAI/1.0"
            },
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

            if isinstance(item, dict):

                text = item.get(
                    "Text",
                    ""
                )

                if text:
                    results.append(text)

        return "\n\n".join(
            results
        )[:6000]

    except Exception:

        return ""


# =========================================================
# READ FILES
# =========================================================

def read_file_bytes(
    file_name,
    data
):

    try:

        name = file_name.lower()

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

            text = []

            for page in reader.pages:

                page_text = (
                    page.extract_text()
                    or ""
                )

                if page_text:
                    text.append(page_text)

            return "\n".join(text)


        if name.endswith(".docx"):

            from docx import Document

            doc = Document(
                io.BytesIO(data)
            )

            text = []

            for paragraph in doc.paragraphs:

                if paragraph.text:
                    text.append(
                        paragraph.text
                    )

            return "\n".join(text)

    except Exception as error:

        return (
            "تعذر قراءة الملف: "
            + str(error)
        )

    return ""


# =========================================================
# AUDIO
# =========================================================

def transcribe_audio(audio_file):

    try:

        recognizer = sr.Recognizer()

        audio_bytes = (
            audio_file.getvalue()
        )

        with io.BytesIO(
            audio_bytes
        ) as audio_buffer:

            with sr.AudioFile(
                audio_buffer
            ) as source:

                audio = recognizer.record(
                    source
                )

        text = recognizer.recognize_google(
            audio,
            language="ar-EG"
        )

        return text.strip()

    except sr.UnknownValueError:

        return ""

    except Exception:

        return ""


# =========================================================
# CREATE MESSAGES
# =========================================================

def create_messages(
    user_text,
    extra_content=None
):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


    for message in (
        st.session_state.messages[-8:]
    ):

        messages.append({
            "role": message["role"],
            "content": message["content"]
        })


    content = [
        {
            "type": "text",
            "text": (
                user_text
                if user_text
                else
                "حلل المحتوى المرفق."
            )
        }
    ]


    if extra_content:
        content.extend(
            extra_content
        )


    if should_search(
        user_text
    ):

        result = web_search(
            user_text
        )

        if result:

            content.append({
                "type": "text",
                "text": (
                    "هذه معلومات من البحث "
                    "على الإنترنت، استخدمها "
                    "كمعلومات مساعدة:\n\n"
                    + result
                )
            })


    messages.append({
        "role": "user",
        "content": content
    })


    return messages


# =========================================================
# AI
# =========================================================

def ask_ai(
    user_text,
    extra_content=None
):

    if developer_question(
        user_text
    ):

        return (
            "أنا Yosef AI، "
            "وتم تطويري بواسطة يوسف."
        )


    messages = create_messages(
        user_text,
        extra_content
    )


    headers = {
        "Authorization":
            f"Bearer {OPENROUTER_KEY}",

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
            1000,

        "temperature":
            0.3,
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
                "⏳ تم الوصول للحد المؤقت "
                "من OpenRouter. حاول مرة أخرى."
            )


        if response.status_code >= 500:

            return (
                "⏳ خادم الذكاء مشغول حاليًا. "
                "حاول مرة أخرى."
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

                error = response.text[:500]

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
            "⏳ الاتصال استغرق وقتًا طويلًا. "
            "حاول مرة أخرى."
        )


    except requests.exceptions.ConnectionError:

        return (
            "❌ لا يمكن الاتصال بالخادم. "
            "تأكد من الإنترنت."
        )


    except Exception as error:

        return (
            "❌ حصل خطأ:\n\n"
            + str(error)[:500]
        )


# =========================================================
# OLD MESSAGES
# =========================================================

for message in (
    st.session_state.messages
):

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
# NEW CHAT
# =========================================================

col1, col2 = st.columns(2)


with col1:

    if st.button(
        "🆕 محادثة جديدة",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.attached_files = []

        st.rerun()


with col2:

    if st.session_state.plan == "Free":

        st.info(
            "🆓 استخدام مجاني"
        )

    else:

        st.success(
            "⭐ Pro"
        )


# =========================================================
# PRO
# =========================================================

with st.expander(
    "⭐ الترقية إلى Yosef AI Pro"
):

    st.write(
        "احصل على استخدام أكبر ومميزات إضافية."
    )


    if PRO_PAYMENT_URL:

        st.link_button(
            "💳 اشترك في Pro",
            PRO_PAYMENT_URL,
            use_container_width=True
        )

    else:

        st.info(
            "رابط الدفع غير مضاف حاليًا."
        )


    if PRO_CODE:

        code = st.text_input(
            "كود Pro",
            type="password"
        )


        if st.button(
            "تفعيل Pro",
            use_container_width=True
        ):

            if code == PRO_CODE:

                st.session_state.plan = "Pro"

                st.success(
                    "✅ تم تفعيل Pro."
                )

                st.rerun()

            else:

                st.error(
                    "❌ الكود غير صحيح."
                )


# =========================================================
# PLUS MENU
# =========================================================

with st.popover(
    "＋",
    type="secondary",
    width="content"
):

    st.markdown(
        "## 📎 إضافة إلى Yosef AI"
    )


    # =====================================================
    # CAMERA
    # =====================================================

    st.markdown(
        '<div class="upload-title">📷 الكاميرا</div>',
        unsafe_allow_html=True
    )


    camera_file = st.camera_input(
        "التقط صورة",
        key="yosef_camera",
        label_visibility="visible"
    )


    if camera_file is not None:

        st.session_state.attached_files = [
            {
                "name":
                    "camera_photo.jpg",

                "type":
                    "image/jpeg",

                "data":
                    camera_file.getvalue(),
            }
        ]

        st.success(
            "✅ تم التقاط الصورة"
        )


    # =====================================================
    # IMAGES
    # =====================================================

    st.markdown(
        '<div class="upload-title">🖼️ الصور</div>',
        unsafe_allow_html=True
    )


    image_file = st.file_uploader(
        "اختر صورة من الهاتف",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        accept_multiple_files=False,
        key="yosef_image_uploader",
        label_visibility="visible",
    )


    if image_file is not None:

        st.session_state.attached_files = [
            {
                "name":
                    image_file.name,

                "type":
                    image_file.type
                    or "image/jpeg",

                "data":
                    image_file.getvalue(),
            }
        ]

        st.success(
            "✅ تم اختيار الصورة"
        )


    # =====================================================
    # DOCUMENTS
    # =====================================================

    st.markdown(
        '<div class="upload-title">📎 الملفات</div>',
        unsafe_allow_html=True
    )


    document_files = st.file_uploader(
        "اختر ملفات",
        type=[
            "pdf",
            "docx",
            "txt",
        ],
        accept_multiple_files=True,
        key="yosef_document_uploader",
        label_visibility="visible",
    )


    if document_files:

        image_is_selected = (
            image_file is not None
        )

        if not image_is_selected:

            st.session_state.attached_files = []

            for uploaded in document_files:

                st.session_state.attached_files.append({
                    "name":
                        uploaded.name,

                    "type":
                        uploaded.type or "",

                    "data":
                        uploaded.getvalue(),
                })


        st.success(
            f"✅ تم اختيار {len(document_files)} ملف"
        )


# =========================================================
# SHOW ATTACHMENTS
# =========================================================

if st.session_state.attached_files:

    st.markdown(
        "### 📎 المرفق الحالي"
    )


    for attached in (
        st.session_state.attached_files
    ):

        file_name = attached["name"]

        file_type = attached["type"]

        file_data = attached["data"]


        if file_type.startswith(
            "image/"
        ):

            st.image(
                file_data,
                width=220
            )


        st.caption(
            "📎 " + file_name
        )


    if st.button(
        "🗑️ إزالة المرفقات",
        key="remove_all_attachments"
    ):

        st.session_state.attached_files = []

        st.rerun()


# =========================================================
# MICROPHONE
# خارج خانة الكتابة
# =========================================================

audio_file = st.audio_input(
    "🎤",
    key="yosef_microphone",
    label_visibility="collapsed"
)


# =========================================================
# TEXT INPUT
# =========================================================

prompt = st.chat_input(
    "اكتب رسالتك...",
    key="yosef_chat_input"
)


# =========================================================
# AUDIO PROCESSING
# =========================================================

if audio_file is not None:

    audio_id = id(audio_file)

    if (
        st.session_state.last_audio_id
        != audio_id
    ):

        st.session_state.last_audio_id = audio_id

        with st.spinner(
            "🎤 جاري تحويل الصوت إلى نص..."
        ):

            voice_text = transcribe_audio(
                audio_file
            )


        if voice_text:

            st.session_state.messages.append({
                "role":
                    "user",

                "content":
                    "🎤 " + voice_text,
            })


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

                    answer = ask_ai(
                        voice_text
                    )


                st.markdown(
                    answer
                )


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
# TEXT + ATTACHMENTS
# =========================================================

if prompt:

    user_text = prompt.strip()

    attached_files = (
        st.session_state.attached_files
    )


    extra_content = []


    # =====================================================
    # ATTACHMENTS -> AI
    # =====================================================

    for attached in attached_files:

        file_name = attached["name"]

        file_type = attached["type"]

        file_data = attached["data"]


        # IMAGE
        if file_type.startswith(
            "image/"
        ):

            encoded = (
                base64.b64encode(
                    file_data
                )
                .decode("utf-8")
            )


            extra_content.append({
                "type":
                    "image_url",

                "image_url": {
                    "url":
                        (
                            f"data:"
                            f"{file_type};"
                            f"base64,"
                            f"{encoded}"
                        )
                }
            })


        # DOCUMENT
        else:

            file_text = read_file_bytes(
                file_name,
                file_data
            )


            if file_text:

                extra_content.append({
                    "type":
                        "text",

                    "text":
                        (
                            f"محتوى الملف "
                            f"({file_name}):\n\n"
                            + file_text[:20000]
                        )
                })


    # =====================================================
    # USER MESSAGE
    # =====================================================

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        if user_text:

            st.markdown(
                user_text
            )


        for attached in attached_files:

            file_type = attached["type"]

            file_data = attached["data"]

            file_name = attached["name"]


            if file_type.startswith(
                "image/"
            ):

                st.image(
                    file_data,
                    width=300
                )

            else:

                st.caption(
                    "📎 " + file_name
                )


    # =====================================================
    # AI ANSWER
    # =====================================================

    with st.chat_message(
        "assistant",
        avatar="🤖"
    ):

        with st.spinner(
            "🤖 Yosef AI بيكتب..."
        ):

            answer = ask_ai(
                user_text,
                extra_content
            )


        st.markdown(
            answer
        )


    # =====================================================
    # SAVE
    # =====================================================

    saved_user_text = user_text


    if not saved_user_text:

        if attached_files:

            saved_user_text = (
                "📎 تم إرسال مرفق"
            )

        else:

            saved_user_text = (
                "رسالة بدون نص"
            )


    st.session_state.messages.append({
        "role":
            "user",

        "content":
            saved_user_text,
    })


    st.session_state.messages.append({
        "role":
            "assistant",

        "content":
            answer,
    })


    # =====================================================
    # CLEAR ATTACHMENTS
    # =====================================================

    st.session_state.attached_files = []

    st.rerun()
