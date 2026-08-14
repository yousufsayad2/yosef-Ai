import streamlit as st
from openai import OpenAI
import base64
import json
import streamlit.components.v1 as components

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
إذا أرسل المستخدم صوتًا، افهم كلامه وأجب عنه مباشرة.
"""

# =========================
# عرض المحادثة السابقة
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
# تشغيل الصوت
# =========================

voice_enabled = st.checkbox(
    "🔊 تشغيل رد Yosef AI بصوت",
    value=False
)


# =========================
# الكتابة + الصور + الملفات + الصوت
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
        # لازم يكون فيه رسالة
        # =========================

        if (
            not prompt_text
            and not prompt.audio
            and not uploaded_file
        ):
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
                    "🎙️ تم استلام الرسالة الصوتية."
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

        content = []


        # النص
        if prompt_text:

            content.append({
                "type": "text",
                "text": prompt_text
            })


        # الصوت
        if prompt.audio:

            audio_bytes = (
                prompt.audio.getvalue()
            )

            audio_base64 = base64.b64encode(
                audio_bytes
            ).decode("utf-8")

            content.append({

                "type": "input_audio",

                "input_audio": {
                    "data": audio_base64,
                    "format": "wav"
                }

            })


        # الصورة
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

            model=(
                "nvidia/"
                "nemotron-3-nano-omni-30b-a3b-reasoning:free"
            ),

            messages=api_messages,

            max_tokens=800,

            extra_body={
                "reasoning": {
                    "effort": "none"
                }
            }

        )


        answer = (

            response.choices[0]
            .message.content

            or "لم أتمكن من إنشاء رد."

        )


        # =========================
        # عرض رد Yosef AI
        # =========================

        with st.chat_message("assistant"):

            st.markdown(answer)


            # =====================
            # نطق الرد من المتصفح
            # =====================

            if voice_enabled:

                safe_answer = json.dumps(
                    answer,
                    ensure_ascii=False
                )

                components.html(

                    f"""
                    <div style="
                        font-family: sans-serif;
                        text-align: center;
                        padding: 5px;
                    ">

                        <button
                            onclick="speakAnswer()"
                            style="
                                border: none;
                                border-radius: 12px;
                                padding: 10px 18px;
                                font-size: 16px;
                                cursor: pointer;
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

        if prompt.audio:

            user_history = "🎙️ رسالة صوتية"

        else:

            user_history = prompt_text


        st.session_state.messages.append({

            "role": "user",
            "content": user_history

        })


        st.session_state.messages.append({

            "role": "assistant",
            "content": answer

        })


    except Exception as e:

        st.error(
            f"حدث خطأ: {e}"
        )
