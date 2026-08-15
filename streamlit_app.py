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

# =========================================================
# التصميم
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

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

    .plan {
        padding: 12px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 15px;
        border: 1px solid #444;
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
مين عملك؟
مين طورك؟
مين مبرمجك؟
مين صنعك؟
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
# البحث على الإنترنت
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

                "User-Agent":
                    "YosefAI/1.0"
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
        )[:6000]

    except Exception:

        return ""

# =========================================================
# قراءة الملفات
# =========================================================

def read_file(file):

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

            return "\n".join(
                text
            )

        # DOCX
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

            return "\n".join(
                text
            )

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

    # ذاكرة آخر 8 رسائل

    for message in (
        st.session_state.messages[-8:]
    ):

        messages.append({

            "role":
                message["role"],

            "content":
                message["content"]
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

    # صورة أو ملف

    if extra_content:

        content.extend(
            extra_content
        )

    # البحث

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
# استدعاء الذكاء الاصطناعي
# =========================================================

def ask_ai(
    user_text,
    extra_content=None
):

    # إجابة المطور مباشرة

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

        # مفتاح خطأ

        if response.status_code == 401:

            return (
                "❌ مفتاح OpenRouter غير صحيح."
            )

        # الحد من OpenRouter نفسه

        if response.status_code == 429:

            return (
                "⏳ تم الوصول للحد المؤقت "
                "من OpenRouter. حاول مرة أخرى."
            )

        # السيرفر

        if response.status_code >= 500:

            return (
                "⏳ خادم الذكاء مشغول حاليًا. "
                "حاول مرة أخرى."
            )

        # أخطاء أخرى

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

        # بعض النماذج قد ترجع List

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
# الإدخال
# =========================================================

prompt = st.chat_input(

    "اكتب رسالتك...",

    accept_file=True,

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
# تنفيذ الرسالة
# =========================================================

if prompt:

    user_text = (
        prompt.text
        or ""
    )

    uploaded_file = None

    if prompt.files:

        uploaded_file = (
            prompt.files[0]
        )

    extra_content = []

    # =====================================================
    # الصورة / الملف
    # =====================================================

    if uploaded_file:

        file_type = (
            uploaded_file.type
            or ""
        )

        # صورة

        if file_type.startswith(
            "image/"
        ):

            image_data = (
                uploaded_file
                .getvalue()
            )

            encoded = (
                base64.b64encode(
                    image_data
                )
                .decode("utf-8")
            )

            extra_content.append({

                "type":
                    "image_url",

                "image_url": {

                    "url":
                        f"data:{file_type};base64,{encoded}"
                }
            })

        # ملف

        else:

            file_text = read_file(
                uploaded_file
            )

            if file_text:

                extra_content.append({

                    "type":
                        "text",

                    "text":
                        "محتوى الملف:\n\n"
                        + file_text[:20000]
                })

    # =====================================================
    # عرض المستخدم
    # =====================================================

    with st.chat_message(

        "user",

        avatar="👤"
    ):

        if user_text:

            st.markdown(
                user_text
            )

        if uploaded_file:

            if (

                uploaded_file.type

                and

                uploaded_file.type.startswith(
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

            answer = ask_ai(

                user_text,

                extra_content
            )

        st.markdown(
            answer
        )

    # =====================================================
    # حفظ
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
