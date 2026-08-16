import streamlit as st
import requests
import base64
import io
import json


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

if "pending_attachment" not in st.session_state:
    st.session_state.pending_attachment = None


# =========================================================
# التصميم
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 8rem;
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

    /* نخفي أي chat_input قديم لو كان موجود */
    div[data-testid="stChatInput"] {
        display: none !important;
    }

    /* مكان الـ Custom Chat */
    .yosef-chat-wrapper {
        position: fixed;
        left: 50%;
        bottom: 12px;
        transform: translateX(-50%);
        width: min(900px, calc(100% - 24px));
        z-index: 999999;
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
# استدعاء الذكاء الاصطناعي
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
        st.session_state.pending_attachment = None

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
# CUSTOM CHAT BAR
# =========================================================

CHAT_HTML = """
<div class="chat-root">

    <div id="menu" class="attach-menu">

        <button id="cameraBtn" class="attach-item">
            <span class="icon">📷</span>
            <span>كاميرا</span>
        </button>

        <button id="imageBtn" class="attach-item">
            <span class="icon">🖼️</span>
            <span>الصور</span>
        </button>

        <button id="fileBtn" class="attach-item">
            <span class="icon">📎</span>
            <span>ملفات</span>
        </button>

    </div>

    <div class="chat-bar">

        <button
            id="plusBtn"
            class="plus-btn"
            type="button"
        >
            +
        </button>

        <textarea
            id="messageInput"
            rows="1"
            placeholder="اكتب رسالتك..."
        ></textarea>

        <button
            id="sendBtn"
            class="send-btn"
            type="button"
        >
            ↑
        </button>

    </div>

    <input
        id="imageInput"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        style="display:none"
    />

    <input
        id="cameraInput"
        type="file"
        accept="image/*"
        capture="environment"
        style="display:none"
    />

    <input
        id="fileInput"
        type="file"
        accept=".pdf,.docx,.txt"
        style="display:none"
    />

</div>
"""


CHAT_CSS = """
:host {
    display: block;
    width: 100%;
}

.chat-root {
    position: relative;
    width: 100%;
    direction: rtl;
    font-family: sans-serif;
}

.chat-bar {
    width: 100%;
    min-height: 58px;
    box-sizing: border-box;

    display: flex;
    align-items: center;

    gap: 7px;

    padding: 7px 8px;

    background: #1f1f23;

    border: 1px solid #3f3f46;

    border-radius: 22px;

    box-shadow:
        0 4px 18px rgba(0,0,0,0.30);
}

.plus-btn,
.send-btn {
    flex: 0 0 42px;

    width: 42px;
    height: 42px;

    border: none;
    border-radius: 50%;

    display: flex;
    align-items: center;
    justify-content: center;

    cursor: pointer;

    font-size: 27px;
    font-weight: 600;
}

.plus-btn {
    background: transparent;
    color: #eeeeee;
}

.send-btn {
    background: #ffffff;
    color: #222222;
}

.plus-btn:active,
.send-btn:active {
    transform: scale(0.94);
}

#messageInput {
    flex: 1;

    min-width: 0;

    resize: none;

    border: none;
    outline: none;

    background: transparent;

    color: #eeeeee;

    font-family: sans-serif;

    font-size: 16px;

    line-height: 24px;

    padding: 8px 4px;

    max-height: 120px;
}

#messageInput::placeholder {
    color: #929292;
}

.attach-menu {
    position: absolute;

    right: 8px;

    bottom: 67px;

    width: 190px;

    padding: 8px;

    background: #26262b;

    border: 1px solid #45454c;

    border-radius: 17px;

    box-shadow:
        0 10px 35px rgba(0,0,0,0.45);

    display: none;

    z-index: 9999999;
}

.attach-menu.open {
    display: block;
}

.attach-item {
    width: 100%;

    min-height: 48px;

    border: none;

    background: transparent;

    color: #eeeeee;

    border-radius: 12px;

    display: flex;

    align-items: center;

    gap: 13px;

    padding: 8px 12px;

    cursor: pointer;

    font-size: 16px;

    font-family: sans-serif;

    direction: rtl;

    text-align: right;
}

.attach-item:hover {
    background: #36363d;
}

.icon {
    width: 30px;

    font-size: 23px;

    text-align: center;
}

@media (max-width: 600px) {

    .chat-bar {
        min-height: 56px;
        border-radius: 20px;
    }

    .plus-btn,
    .send-btn {
        width: 40px;
        height: 40px;
        flex-basis: 40px;
    }

    #messageInput {
        font-size: 16px;
    }

    .attach-menu {
        right: 4px;
        width: 180px;
    }
}
"""


CHAT_JS = """
export default function(component) {

    const {
        parentElement,
        setTriggerValue
    } = component;


    const plusBtn =
        parentElement.querySelector("#plusBtn");

    const sendBtn =
        parentElement.querySelector("#sendBtn");

    const input =
        parentElement.querySelector("#messageInput");

    const menu =
        parentElement.querySelector("#menu");

    const cameraBtn =
        parentElement.querySelector("#cameraBtn");

    const imageBtn =
        parentElement.querySelector("#imageBtn");

    const fileBtn =
        parentElement.querySelector("#fileBtn");

    const cameraInput =
        parentElement.querySelector("#cameraInput");

    const imageInput =
        parentElement.querySelector("#imageInput");

    const fileInput =
        parentElement.querySelector("#fileInput");


    // =====================================================
    // فتح / إغلاق قائمة +
    // =====================================================

    plusBtn.onclick = (event) => {

        event.preventDefault();
        event.stopPropagation();

        menu.classList.toggle("open");
    };


    // =====================================================
    // الضغط خارج القائمة
    // =====================================================

    const closeMenu = (event) => {

        if (!parentElement.contains(event.target)) {

            menu.classList.remove("open");
        }
    };

    document.addEventListener(
        "click",
        closeMenu
    );


    // =====================================================
    // إرسال الملف إلى Python
    // =====================================================

    function processFile(file, source) {

        if (!file) {
            return;
        }

        const maxSize =
            200 * 1024 * 1024;

        if (file.size > maxSize) {

            setTriggerValue(
                "error",
                "الملف أكبر من 200MB."
            );

            return;
        }

        const reader =
            new FileReader();

        reader.onload = () => {

            const result =
                reader.result;

            const parts =
                result.split(",");

            const base64 =
                parts.length > 1
                    ? parts[1]
                    : "";

            setTriggerValue(
                "attachment",
                JSON.stringify({

                    name:
                        file.name || "attachment",

                    type:
                        file.type ||
                        "application/octet-stream",

                    source:
                        source,

                    data:
                        base64
                })
            );

            menu.classList.remove(
                "open"
            );
        };

        reader.onerror = () => {

            setTriggerValue(
                "error",
                "❌ تعذر قراءة الملف."
            );
        };

        reader.readAsDataURL(file);
    }


    // =====================================================
    // الكاميرا
    // =====================================================

    cameraBtn.onclick = (event) => {

        event.preventDefault();
        event.stopPropagation();

        cameraInput.click();
    };


    cameraInput.onchange = () => {

        if (
            cameraInput.files &&
            cameraInput.files.length > 0
        ) {

            processFile(
                cameraInput.files[0],
                "camera"
            );
        }

        cameraInput.value = "";
    };


    // =====================================================
    // الصور
    // =====================================================

    imageBtn.onclick = (event) => {

        event.preventDefault();
        event.stopPropagation();

        imageInput.click();
    };


    imageInput.onchange = () => {

        if (
            imageInput.files &&
            imageInput.files.length > 0
        ) {

            processFile(
                imageInput.files[0],
                "image"
            );
        }

        imageInput.value = "";
    };


    // =====================================================
    // الملفات
    // =====================================================

    fileBtn.onclick = (event) => {

        event.preventDefault();
        event.stopPropagation();

        fileInput.click();
    };


    fileInput.onchange = () => {

        if (
            fileInput.files &&
            fileInput.files.length > 0
        ) {

            processFile(
                fileInput.files[0],
                "file"
            );
        }

        fileInput.value = "";
    };


    // =====================================================
    // إرسال الرسالة
    // =====================================================

    function sendMessage() {

        const text =
            input.value.trim();

        if (!text) {
            return;
        }

        setTriggerValue(
            "message",
            text
        );

        input.value = "";

        input.style.height = "auto";
    }


    sendBtn.onclick = (event) => {

        event.preventDefault();

        sendMessage();
    };


    // =====================================================
    // Enter للإرسال
    // =====================================================

    input.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Enter"
                &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage();
            }
        }
    );


    // =====================================================
    // تكبير خانة الكتابة
    // =====================================================

    input.addEventListener(
        "input",
        () => {

            input.style.height =
                "auto";

            input.style.height =
                Math.min(
                    input.scrollHeight,
                    120
                ) + "px";
        }
    );


    // =====================================================
    // Cleanup
    // =====================================================

    return () => {

        document.removeEventListener(
            "click",
            closeMenu
        );
    };
}
"""


# =========================================================
# تسجيل الـ Component
# =========================================================

yosef_chat = st.components.v2.component(
    name="yosef_ai_chat_bar_v3",
    html=CHAT_HTML,
    css=CHAT_CSS,
    js=CHAT_JS,
    isolate_styles=True,
)


# =========================================================
# تشغيل الـ Component
# =========================================================

chat_result = yosef_chat(
    key="yosef_chat_bar_v3"
)


# =========================================================
# خطأ المرفق
# =========================================================

error_value = getattr(
    chat_result,
    "error",
    None
)

if error_value:

    st.error(
        str(error_value)
    )


# =========================================================
# استقبال المرفق
# =========================================================

attachment_value = getattr(
    chat_result,
    "attachment",
    None
)

if attachment_value:

    try:

        attachment = json.loads(
            attachment_value
        )

        encoded_data = attachment.get(
            "data",
            ""
        )

        if encoded_data:

            file_data = base64.b64decode(
                encoded_data
            )

            st.session_state.pending_attachment = {

                "name":
                    attachment.get(
                        "name",
                        "attachment"
                    ),

                "type":
                    attachment.get(
                        "type",
                        ""
                    ),

                "data":
                    file_data,
            }

    except Exception as error:

        st.error(
            "❌ تعذر تجهيز المرفق: "
            + str(error)
        )


# =========================================================
# استقبال الرسالة
# =========================================================

message_value = getattr(
    chat_result,
    "message",
    None
)


if message_value:

    user_text = str(
        message_value
    ).strip()

    extra_content = []

    attachment = (
        st.session_state.pending_attachment
    )


    # =====================================================
    # تجهيز المرفق
    # =====================================================

    if attachment:

        file_type = attachment["type"]

        file_data = attachment["data"]

        file_name = attachment["name"]


        # -------------------------------------------------
        # صورة
        # -------------------------------------------------

        if file_type.startswith(
            "image/"
        ):

            encoded = base64.b64encode(
                file_data
            ).decode(
                "utf-8"
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


        # -------------------------------------------------
        # ملف
        # -------------------------------------------------

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

        if attachment:

            if attachment["type"].startswith(
                "image/"
            ):

                st.image(
                    attachment["data"],
                    width=300
                )

            else:

                st.caption(
                    "📎 "
                    + attachment["name"]
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
    # حذف المرفق بعد الإرسال
    # =====================================================

    st.session_state.pending_attachment = None

    st.rerun()
