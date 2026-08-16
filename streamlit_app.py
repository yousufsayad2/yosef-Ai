import streamlit as st
import requests
import base64
import io


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
# الإعدادات
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


# =========================================================
# التحقق من API
# =========================================================

if not OPENROUTER_KEY:

    st.error(
        "❌ مفتاح OPENROUTER_API_KEY غير موجود في Secrets."
    )

    st.stop()


# =========================================================
# Session State
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "plan" not in st.session_state:
    st.session_state.plan = "Free"

if "attached_file" not in st.session_state:
    st.session_state.attached_file = None


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
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }


    /* =========================================
       العنوان
       ========================================= */

    .yosef-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #888;
        margin-bottom: 25px;
    }


    /* =========================================
       Free / Pro
       ========================================= */

    .plan {
        padding: 12px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 15px;
        border: 1px solid #444;
    }


    /* =========================================
       شريط الكتابة الأصلي
       ========================================= */

    div[data-testid="stChatInput"] {

        position: fixed !important;

        left: 50% !important;

        transform: translateX(-50%) !important;

        bottom: 18px !important;

        width: min(
            900px,
            calc(100% - 30px)
        ) !important;

        z-index: 999990 !important;
    }


    /* جسم خانة الكتابة */

    div[data-testid="stChatInput"] > div {

        background: #202027 !important;

        border: 1px solid #45454d !important;

        border-radius: 24px !important;

        min-height: 58px !important;

        box-shadow:
            0 4px 18px rgba(0,0,0,0.25) !important;
    }


    /* textarea */

    div[data-testid="stChatInput"] textarea {

        background: transparent !important;

        color: white !important;

        font-size: 16px !important;

        padding-right: 55px !important;

        padding-left: 55px !important;
    }


    div[data-testid="stChatInput"] textarea::placeholder {

        color: #888 !important;
    }


    /* زر الإرسال */

    div[data-testid="stChatInput"] button {

        border-radius: 50% !important;
    }


    /* =========================================
       زر +
       ========================================= */

    div[data-testid="stPopover"] {

        position: fixed !important;

        z-index: 1000000 !important;

        bottom: 25px !important;

        right:
            calc(
                (100% - min(900px, calc(100% - 30px))) / 2
                + 8px
            ) !important;
    }


    div[data-testid="stPopover"] > button {

        width: 42px !important;

        height: 42px !important;

        min-height: 42px !important;

        padding: 0 !important;

        border: none !important;

        background: transparent !important;

        color: #ffffff !important;

        font-size: 30px !important;

        font-weight: 400 !important;

        line-height: 42px !important;

        box-shadow: none !important;

        border-radius: 50% !important;
    }


    div[data-testid="stPopover"] > button:hover {

        background: rgba(255,255,255,0.08) !important;
    }


    /* =========================================
       قائمة المرفقات
       ========================================= */

    div[data-testid="stPopoverBody"] {

        min-width: 230px !important;

        max-width: 280px !important;

        padding: 14px !important;

        border-radius: 18px !important;

        background: #202027 !important;

        border: 1px solid #444 !important;

        box-shadow:
            0 10px 35px rgba(0,0,0,0.35) !important;
    }


    /* =========================================
       المرفق الحالي
       ========================================= */

    .attachment-box {

        background: #202027;

        border: 1px solid #444;

        border-radius: 14px;

        padding: 10px;

        margin-bottom: 10px;
    }


    /* =========================================
       الموبايل
       ========================================= */

    @media (max-width: 600px) {

        .block-container {

            padding-left: 15px;
            padding-right: 15px;

            padding-bottom: 6rem;
        }


        .yosef-title {

            font-size: 40px;
        }


        div[data-testid="stChatInput"] {

            width:
                calc(100% - 30px) !important;

            bottom: 14px !important;
        }


        div[data-testid="stPopover"] {

            right: 24px !important;

            bottom: 22px !important;
        }


        div[data-testid="stPopover"] > button {

            width: 42px !important;

            height: 42px !important;

            font-size: 29px !important;
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
    'مساعدك الذكي للنصوص والصور والملفات والصوت'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# حالة الخطة
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
# النظام الأساسي
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

إذا أرسل ملفًا:
استخدم محتوى الملف المتاح لك.

لا تخترع معلومات.
"""


# =========================================================
# سؤال المطور
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
# البحث
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
# قراءة الملفات
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
                    text.append(
                        page_text
                    )

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
# تجهيز الرسائل
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
                else "حلل المحتوى المرفق."
            )
        }
    ]

    if extra_content:

        content.extend(
            extra_content
        )

    if should_search(user_text):

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
# الذكاء الاصطناعي
# =========================================================

def ask_ai(
    user_text,
    extra_content=None
):

    if developer_question(
        user_text
    ):

        return (
            "أنا Yosef AI، وتم تطويري بواسطة يوسف."
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
# المحادثة القديمة
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
# الأزرار
# =========================================================

col1, col2 = st.columns(2)

with col1:

    if st.button(
        "🆕 محادثة جديدة",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.attached_file = None

        st.rerun()


with col2:

    if (
        st.session_state.plan
        == "Free"
    ):

        st.info(
            "🆓 استخدام مجاني"
        )

    else:

        st.success(
            "⭐ Pro"
        )


# =========================================================
# Pro
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
# زر + للمرفقات
# =========================================================

with st.popover("＋"):

    st.markdown(
        "### 📎 إضافة إلى Yosef AI"
    )

    # -------------------------------
    # صورة
    # -------------------------------

    st.markdown(
        "🖼️ **صورة**"
    )

    image_file = st.file_uploader(
        "اختر صورة",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        accept_multiple_files=False,
        key="yosef_image",
    )

    if image_file is not None:

        st.session_state.attached_file = {
            "name":
                image_file.name,

            "type":
                image_file.type
                or "image/jpeg",

            "data":
                image_file.getvalue(),
        }


    # -------------------------------
    # كاميرا
    # -------------------------------

    st.markdown(
        "📷 **الكاميرا**"
    )

    camera_file = st.camera_input(
        "التقط صورة",
        key="yosef_camera",
    )

    if camera_file is not None:

        st.session_state.attached_file = {
            "name":
                "camera_photo.jpg",

            "type":
                "image/jpeg",

            "data":
                camera_file.getvalue(),
        }


    # -------------------------------
    # ملف
    # -------------------------------

    st.markdown(
        "📄 **ملف**"
    )

    document_file = st.file_uploader(
        "اختر ملف",
        type=[
            "pdf",
            "docx",
            "txt",
        ],
        accept_multiple_files=False,
        key="yosef_document",
    )

    if document_file is not None:

        st.session_state.attached_file = {
            "name":
                document_file.name,

            "type":
                document_file.type or "",

            "data":
                document_file.getvalue(),
        }


# =========================================================
# المرفق الحالي
# =========================================================

attached = (
    st.session_state.attached_file
)

if attached:

    file_name = attached["name"]

    file_type = attached["type"]

    file_data = attached["data"]

    st.markdown(
        '<div class="attachment-box">',
        unsafe_allow_html=True
    )

    st.write(
        "📎 المرفق الحالي:",
        file_name
    )

    if file_type.startswith(
        "image/"
    ):

        st.image(
            file_data,
            width=200
        )

    if st.button(
        "🗑️ إزالة المرفق",
        key="remove_attachment",
        use_container_width=True
    ):

        st.session_state.attached_file = None

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =========================================================
# خانة الكتابة
# =========================================================

prompt = st.chat_input(
    "اكتب رسالتك..."
)


# =========================================================
# تنفيذ الرسالة
# =========================================================

if prompt:

    user_text = prompt.strip()

    extra_content = []

    attached = (
        st.session_state.attached_file
    )


    # =====================================================
    # معالجة المرفق
    # =====================================================

    if attached:

        file_type = attached["type"]

        file_data = attached["data"]

        file_name = attached["name"]


        # صورة
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


        # ملف
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
                            "محتوى الملف "
                            "المرفق:\n\n"
                            + file_text[:20000]
                        )
                })


    # =====================================================
    # رسالة المستخدم
    # =====================================================

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        if user_text:

            st.markdown(
                user_text
            )

        if attached:

            if file_type.startswith(
                "image/"
            ):

                st.image(
                    file_data,
                    width=300
                )

            else:

                st.caption(
                    "📎 "
                    + file_name
                )


    # =====================================================
    # رد Yosef AI
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
    # حفظ المحادثة
    # =====================================================

    st.session_state.messages.append({
        "role":
            "user",

        "content":
            user_text
    })

    st.session_state.messages.append({
        "role":
            "assistant",

        "content":
            answer
    })


    # =====================================================
    # إزالة المرفق
    # =====================================================

    st.session_state.attached_file = None

    st.rerun()
