import streamlit as st
from openai import OpenAI
import base64
import io
import speech_recognition as sr
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖"
)

st.title("🤖 Yosef AI")
st.write("أهلاً بيك 👋")
st.write("أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!")

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

system_prompt = """أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.
عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.
لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.
أجب باللغة التي يستخدمها المستخدم.
"""

# =========================
# عرض المحادثة
# =========================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# محادثة جديدة
# =========================

if st.button("🆕 محادثة جديدة"):
    st.session_state.messages = []
    st.rerun()


# =========================
# الصوت
# =========================

voice_enabled = st.checkbox(
    "🔊 تشغيل رد Yosef AI بصوت",
    value=False
)


# =========================
# الإدخال
# =========================

prompt = st.chat_input(
    "اكتب رسالتك أو سجل صوتك...",
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


if prompt:

    try:

        prompt_text = prompt.text or ""

        uploaded_file = (
            prompt.files[0]
            if prompt.files
            else None
        )


        # =========================
        # تحويل الصوت إلى نص
        # =========================

        if prompt.audio:

            with st.spinner("🎙️ جاري تحويل صوتك إلى نص..."):

                audio_bytes = prompt.audio.getvalue()

                recognizer = sr.Recognizer()

                audio_file = io.BytesIO(
                    audio_bytes
                )

                with sr.AudioFile(audio_file) as source:

                    audio_data = recognizer.record(
                        source
                    )

                try:

                    prompt_text = recognizer.recognize_google(
                        audio_data,
                        language="ar-EG"
                    )

                except sr.UnknownValueError:

                    st.error(
                        "❌ مش قادر أفهم الكلام في التسجيل. "
                        "جرّب تتكلم أوضح."
                    )

                    st.stop()

                except sr.RequestError as e:

                    st.error(
                        "❌ خدمة تحويل الصوت إلى نص "
                        f"غير متاحة حاليًا: {e}"
                    )

                    st.stop()


        # =========================
        # التأكد من وجود رسالة
        # =========================

        if not prompt_text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو سجل صوت أو ارفع ملف."
            )

            st.stop()


        # =========================
        # عرض رسالة المستخدم
        # =========================

        with st.chat_message("user"):

            if prompt_text:
                st.markdown(prompt_text)

            if prompt.audio:
                st.caption(
                    "🎙️ تم تحويل الرسالة الصوتية إلى نص."
                )

            if uploaded_file:

                file_type = (
                    uploaded_file.type or ""
                )

                if file_type.startswith("image/"):

                    st.image(uploaded_file)

                else:

                    st.caption(
                        f"📎 {uploaded_file.name}"
                    )


        # =========================
        # تجهيز محتوى الرسالة
        # =========================

        content = [
            {
                "type": "text",
                "text": prompt_text
            }
        ]


        # =========================
        # إضافة الصورة
        # =========================

        if uploaded_file:

            file_type = (
                uploaded_file.type or ""
            )

            if file_type.startswith("image/"):

                image_bytes = (
                    uploaded_file.getvalue()
                )

                image_base64 = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                content.append({

                    "type": "image_url",

                    "image_url": {

                        "url": (
                            f"data:{file_type};"
                            f"base64,{image_base64}"
                        )

                    }

                })


        # =========================
        # تاريخ المحادثة
        # =========================

        api_messages = [

            {
                "role": "system",
                "content": system_prompt
            }

        ]

        for message in st.session_state.messages:

            api_messages.append({

                "role": message["role"],
                "content": message["content"]

            })


        api_messages.append({

            "role": "user",
            "content": content

        })


        # =========================
        # Yosef AI
        # =========================

        response = client.chat.completions.create(

            model="openrouter/free",

            messages=api_messages,

            max_tokens=800

        )


        answer = (

            response.choices[0]
            .message.content

            or "لم أتمكن من إنشاء رد."

        )


        # =========================
        # عرض الرد
        # =========================

        with st.chat_message("assistant"):

            st.markdown(answer)


            # =====================
            # تشغيل صوت الرد
            # =====================

            if voice_enabled:

                safe_answer = json.dumps(
                    answer,
                    ensure_ascii=False
                )

                components.html(

                    f"""
                    <div style="
                        text-align:center;
                        padding:5px;
                    ">

                    <button
                        onclick="speakAnswer()"
                        style="
                            border:0;
                            border-radius:12px;
                            padding:10px 18px;
                            font-size:16px;
                            cursor:pointer;
                        "
                    >
                    🔊 تشغيل صوت Yosef AI
                    </button>

                    </div>

                    <script>

                    function speakAnswer() {{

                        const text = {safe_answer};

                        window.speechSynthesis.cancel();

                        const speech =
                            new SpeechSynthesisUtterance(text);

                        speech.lang = "ar-SA";

                        speech.rate = 1.0;

                        speech.pitch = 1.0;

                        window.speechSynthesis.speak(
                            speech
                        );
                    }}

                    </script>
                    """,

                    height=60

                )


        # =========================
        # حفظ المحادثة
        # =========================

        st.session_state.messages.append({

            "role": "user",

            "content": prompt_text

        })


        st.session_state.messages.append({

            "role": "assistant",

            "content": answer

        })


    except Exception as e:

        st.error(
            f"حدث خطأ: {e}"
        )
