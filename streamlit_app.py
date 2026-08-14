import streamlit as st
from openai import OpenAI
import base64
import io
import speech_recognition as sr


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# OpenRouter
# =========================================================

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


# =========================================================
# الذاكرة
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_call" not in st.session_state:
    st.session_state.voice_call = False


# =========================================================
# تعليمات Yosef AI
# =========================================================

system_prompt = """
أنت Yosef AI.

اسمك Yosef AI.

لا تقل إنك ChatGPT.

أجب باللغة التي يستخدمها المستخدم.

كن طبيعيًا وودودًا ومفيدًا.

في المحادثة الصوتية:
- تكلم بطريقة طبيعية.
- اجعل الرد واضحًا ومختصرًا.
- لا تستخدم مقدمات طويلة.
- تعامل مع المستخدم كأنه يتحدث مع مساعد صوتي.

إذا أرسل المستخدم صورة:
- حلل الصورة وساعده فيها.
- لا تخترع أشياء غير واضحة في الصورة.

إذا أرسل المستخدم ملفًا:
- استخدم المعلومات المتاحة منه.
- إذا لم تستطع قراءة محتوى الملف، وضح ذلك.
"""


# =========================================================
# العنوان
# =========================================================

st.title("🤖 Yosef AI")

st.write("أهلاً بيك 👋")
st.write("أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!")


# =========================================================
# محادثة جديدة
# =========================================================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True,
    key="new_chat"
):

    st.session_state.messages = []
    st.session_state.voice_call = False

    st.rerun()


# =========================================================
# عرض المحادثة
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            message["content"]
        )


# =========================================================
# طلب الرد من Yosef
# =========================================================

def ask_yosef(text, extra_content=None):

    content = [
        {
            "type": "text",
            "text": text
        }
    ]

    # إضافة صورة أو محتوى إضافي
    if extra_content:

        content.extend(
            extra_content
        )

    api_messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # تاريخ المحادثة
    for message in st.session_state.messages:

        api_messages.append(
            {
                "role": message["role"],
                "content": message["content"]
            }
        )

    # الرسالة الحالية
    api_messages.append(
        {
            "role": "user",
            "content": content
        }
    )

    try:

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=api_messages,
            max_tokens=800
        )

        answer = (
            response.choices[0]
            .message.content
        )

        if not answer:

            return "لم أتمكن من إنشاء رد."

        return answer

    except Exception as error:

        error_text = str(error)

        if (
            "429" in error_text
            or "free-models-per-day" in error_text
        ):

            st.warning(
                "⏳ وصلت للحد المجاني للطلبات اليوم."
            )

            st.info(
                "جرّب مرة أخرى بعد تجدد الحد المجاني."
            )

        else:

            st.error(
                "❌ حصل خطأ أثناء تشغيل Yosef AI."
            )

        return None


# =========================================================
# تحويل النص إلى صوت
# =========================================================

def speak_text(text):

    safe_text = str(text)
# =========================================================
# خانة الكتابة + الصور + الملفات + الصوت
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
        "docx"
    ]
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


        # -------------------------------------------------
        # لو مفيش كلام ولا ملف
        # -------------------------------------------------

        if not text and not uploaded_file and not prompt.audio:

            st.warning(
                "اكتب رسالة أو ارفع صورة أو ملف."
            )

            st.stop()


        # -------------------------------------------------
        # عرض رسالة المستخدم
        # -------------------------------------------------

        with st.chat_message("user"):

            if text:
                st.markdown(text)

            if uploaded_file:

                file_type = uploaded_file.type or ""

                if file_type.startswith("image/"):

                    st.image(uploaded_file)

                else:

                    st.write(
                        "📎 " + uploaded_file.name
                    )


        # -------------------------------------------------
        # تجهيز الرسالة
        # -------------------------------------------------

        content = [
            {
                "type": "text",
                "text": text
            }
        ]


        # -------------------------------------------------
        # إرسال الصورة للذكاء الاصطناعي
        # -------------------------------------------------

        if uploaded_file:

            file_type = uploaded_file.type or ""

            if file_type.startswith("image/"):

                image_bytes = uploaded_file.getvalue()

                image_base64 = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                "data:"
                                + file_type
                                + ";base64,"
                                + image_base64
                            )
                        }
                    }
                )


        # -------------------------------------------------
        # تاريخ المحادثة
        # -------------------------------------------------

        api_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]


        for message in st.session_state.messages:

            api_messages.append(
                {
                    "role": message["role"],
                    "content": message["content"]
                }
            )


        # -------------------------------------------------
        # رسالة المستخدم الحالية
        # -------------------------------------------------

        api_messages.append(
            {
                "role": "user",
                "content": content
            }
        )


        # -------------------------------------------------
        # إرسال إلى Yosef AI
        # -------------------------------------------------

        with st.spinner(
            "🤖 Yosef AI بيفكر..."
        ):

            response = client.chat.completions.create(
                model="openrouter/free",
                messages=api_messages,
                max_tokens=800
            )


        # -------------------------------------------------
        # الحصول على الرد
        # -------------------------------------------------

        answer = (
            response.choices[0]
            .message.content
            or "لم أتمكن من إنشاء رد."
        )


        # -------------------------------------------------
        # عرض الرد
        # -------------------------------------------------

        with st.chat_message("assistant"):

            st.markdown(answer)


        # -------------------------------------------------
        # حفظ المحادثة
        # -------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": text
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


    except Exception as error:

        st.error(
            "❌ حصل خطأ: "
            + str(error)
        )
   
