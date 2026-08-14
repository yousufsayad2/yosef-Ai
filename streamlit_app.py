import streamlit as st
from openai import OpenAI
import base64
import requests

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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.button("🆕 محادثة جديدة"):
    st.session_state.messages = []
    st.rerun()

voice_enabled = st.checkbox(
    "🔊 تشغيل رد Yosef AI بصوت",
    value=False
)

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

        # =========================
        # الصوت → نص
        # =========================
        if prompt.audio:
            audio_bytes = prompt.audio.getvalue()

            audio_base64 = base64.b64encode(
                audio_bytes
            ).decode("utf-8")

            transcription_response = requests.post(
                "https://openrouter.ai/api/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/whisper-large-v3",
                    "input_audio": {
                        "data": audio_base64,
                        "format": "wav"
                    }
                },
                timeout=120
            )

            transcription_response.raise_for_status()

            transcription_data = (
                transcription_response.json()
            )

            prompt_text = transcription_data.get(
                "text",
                ""
            ).strip()

        uploaded_file = (
            prompt.files[0]
            if prompt.files
            else None
        )

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

            if uploaded_file:
                file_type = uploaded_file.type or ""

                if file_type.startswith("image/"):
                    st.image(uploaded_file)
                else:
                    st.caption(
                        f"📎 {uploaded_file.name}"
                    )

            if prompt.audio:
                st.caption(
                    "🎙️ تم تحويل الرسالة الصوتية إلى نص."
                )

        # =========================
        # تجهيز الرسالة
        # =========================
        content = [
            {
                "type": "text",
                "text": prompt_text
            }
        ]

        if uploaded_file:

            file_type = uploaded_file.type or ""

            if file_type.startswith("image/"):

                image_bytes = uploaded_file.getvalue()

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
            response.choices[0].message.content
            or "لم أتمكن من إنشاء رد."
        )

        # =========================
        # عرض الرد + الصوت
        # =========================
        with st.chat_message("assistant"):

            st.markdown(answer)

            if voice_enabled:

                with st.spinner("🔊 جاري تحويل الرد إلى صوت..."):

                    speech_response = requests.post(
                        "https://openrouter.ai/api/v1/audio/speech",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "openai/gpt-4o-mini-tts-2025-12-15",
                            "input": answer,
                            "voice": "alloy",
                            "response_format": "mp3"
                        },
                        timeout=120
                    )

                if speech_response.ok:

                    st.audio(
                        speech_response.content,
                        format="audio/mpeg"
                    )

                else:

                    st.error(
                        "❌ حصل خطأ في الصوت:\n\n"
                        + speech_response.text
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
