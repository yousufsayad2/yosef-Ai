import streamlit as st
from openai import OpenAI
import io
import speech_recognition as sr


st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)


# =========================
# OpenRouter
# =========================

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


# =========================
# الذاكرة
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_call" not in st.session_state:
    st.session_state.voice_call = False


# =========================
# تعليمات Yosef AI
# =========================

system_prompt = """
أنت Yosef AI.

اسمك Yosef AI.

لا تقل إنك ChatGPT.

أجب باللغة التي يستخدمها المستخدم.

كن طبيعيًا وودودًا.

في المحادثة الصوتية:
- تكلم بطريقة طبيعية.
- اجعل الرد قصيرًا وواضحًا.
- لا تستخدم مقدمات طويلة.
- تعامل مع المستخدم كأنه يتحدث مع مساعد صوتي حقيقي.
"""


# =========================
# العنوان
# =========================

st.title("🤖 Yosef AI")

st.write("أهلاً بيك 👋")
st.write("أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!")


# =========================
# محادثة جديدة
# =========================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):

    st.session_state.messages = []
    st.session_state.voice_call = False

    st.rerun()


# =========================
# عرض المحادثة القديمة
# =========================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            message["content"]
        )


# =========================
# طلب الرد من Yosef
# =========================

def ask_yosef(text):

    api_messages = []

    api_messages.append(
        {
            "role": "system",
            "content": system_prompt
        }
    )

    for message in st.session_state.messages:

        api_messages.append(
            {
                "role": message["role"],
                "content": message["content"]
            }
        )

    api_messages.append(
        {
            "role": "user",
            "content": text
        }
    )

    try:

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=api_messages,
            max_tokens=800
        )

        answer = response.choices[0].message.content

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


# =========================
# تحويل النص إلى صوت
# =========================

def speak_text(text):

    safe_text = str(text)

    safe_text = safe_text.replace(
        "\\",
        "\\\\"
    )

    safe_text = safe_text.replace(
        "`",
        "\\`"
    )

    safe_text = safe_text.replace(
        "${",
        "\\${"
    )

    safe_text = safe_text.replace(
        "\n",
        " "
    )

    safe_text = safe_text.replace(
        "\r",
        " "
    )

    html = (
        "<script>"
        "const text = `"
        + safe_text
        + "`;"
        "if ('speechSynthesis' in window) {"
        "window.speechSynthesis.cancel();"
        "const speech = new SpeechSynthesisUtterance(text);"
        "speech.lang = 'ar-SA';"
        "speech.rate = 1.0;"
        "speech.pitch = 1.0;"
        "window.speechSynthesis.speak(speech);"
        "}"
        "</script>"
    )

    st.components.v1.html(
        html,
        height=1
    )


# =========================
# زر المحادثة الصوتية
# =========================

if not st.session_state.voice_call:

    if st.button(
        "📞 محادثة صوتية",
        use_container_width=True
    ):

        st.session_state.voice_call = True

        st.rerun()

else:

    st.success(
        "📞 المحادثة الصوتية مفعّلة"
    )

    if st.button(
        "🔴 إنهاء المحادثة الصوتية",
        use_container_width=True
    ):

        st.session_state.voice_call = False

        st.rerun()


# =========================
# المحادثة الصوتية
# =========================

if st.session_state.voice_call:

    st.subheader(
        "🎙️ اتكلم مع Yosef AI"
    )

    st.caption(
        "اضغط على الميكروفون واتكلم."
    )

    voice_audio = st.audio_input(
        "🎙️ اضغط هنا للتحدث"
    )

    if voice_audio:

        try:

            audio_bytes = voice_audio.getvalue()

            audio_buffer = io.BytesIO(
                audio_bytes
            )

            recognizer = sr.Recognizer()

            with sr.AudioFile(
                audio_buffer
            ) as source:

                audio_data = recognizer.record(
                    source
                )

            with st.spinner(
                "🎧 Yosef AI بيسمعك..."
            ):

                spoken_text = (
                    recognizer.recognize_google(
                        audio_data,
                        language="ar-EG"
                    )
                )

            with st.chat_message("user"):

                st.markdown(
                    spoken_text
                )

            with st.spinner(
                "🤖 Yosef AI بيفكر..."
            ):

                answer = ask_yosef(
                    spoken_text
                )

            if answer:

                with st.chat_message("assistant"):

                    st.markdown(
                        answer
                    )

                    speak_text(
                        answer
                    )

                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": spoken_text
                    }
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

                st.rerun()

        except sr.UnknownValueError:

            st.error(
                "❌ مش قادر أفهم التسجيل."
            )

        except sr.RequestError:

            st.error(
                "❌ خدمة تحويل الصوت إلى نص غير متاحة."
            )

        except Exception as error:

            st.error(
                "❌ حصل خطأ في المحادثة الصوتية: "
                + str(error)
            )


# =========================
# الشات العادي
# =========================

prompt = st.chat_input(
    "اكتب رسالتك..."
)


# =========================
# معالجة الرسالة
# =========================

if prompt:

    try:

        prompt_text = str(prompt)

        with st.chat_message("user"):

            st.markdown(
                prompt_text
            )

        with st.spinner(
            "🤖 Yosef AI بيفكر..."
        ):

            answer = ask_yosef(
                prompt_text
            )

        if answer:

            with st.chat_message("assistant"):

                st.markdown(
                    answer
                )

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt_text
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
