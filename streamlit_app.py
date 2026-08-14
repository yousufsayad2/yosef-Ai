import streamlit as st
from openai import OpenAI
import base64
import io
import json
import re
import requests
import streamlit.components.v1 as components


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Yosef AI")
st.write("أهلاً بيك 👋")
st.write("أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!")


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
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

إذا تم إعطاؤك معلومات من البحث على الإنترنت:
- استخدم المعلومات المتاحة.
- لا تخترع معلومات غير موجودة.
- إذا كانت المعلومات غير كافية، وضح ذلك.
"""


# =========================================================
# المحادثة السابقة
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================================================
# محادثة جديدة
# =========================================================

if st.button("🆕 محادثة جديدة"):

    st.session_state.messages = []
    st.session_state.voice_call = False

    st.rerun()


# =========================================================
# زر المحادثة الصوتية
# =========================================================

if not st.session_state.voice_call:

    if st.button(
        "📞 بدء محادثة صوتية",
        use_container_width=True
    ):

        st.session_state.voice_call = True
        st.rerun()

else:

    st.success("📞 المحادثة الصوتية تعمل")

    if st.button(
        "🔴 إنهاء المحادثة الصوتية",
        use_container_width=True
    ):

        st.session_state.voice_call = False
        st.rerun()


# =========================================================
# البحث التلقائي
# =========================================================

def needs_web_search(text):

    keywords = [
        "الطقس",
        "الجو",
        "درجة الحرارة",
        "حرارة",
        "مطر",
        "رياح",
        "أخبار",
        "خبر",
        "الأخبار",
        "آخر الأخبار",
        "اخر الاخبار",
        "سعر",
        "الأسعار",
        "بكام",
        "سعر الدولار",
        "سعر الذهب",
        "اليوم",
        "دلوقتي",
        "الآن",
        "حاليا",
        "حاليًا",
        "أحدث",
        "آخر",
        "الجديد",
        "موعد",
        "متى",
        "نتيجة",
        "نتائج",
        "مباراة",
        "مباريات",
        "today",
        "now",
        "latest",
        "news",
        "weather",
        "price",
        "prices",
        "current",
        "score",
        "match"
    ]

    text_lower = text.lower()

    for keyword in keywords:

        if keyword in text_lower:
            return True

    return False


# =========================================================
# بحث مخفي
# =========================================================

def search_web(query):

    try:

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={
                "q": query
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=15
        )

        if response.status_code != 200:
            return []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL
        )

        matches = pattern.findall(
            response.text
        )

        results = []

        for href, title in matches[:5]:

            clean_title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            results.append({
                "title": clean_title,
                "href": href
            })

        return results

    except Exception:

        return []


# =========================================================
# تحويل الصوت إلى نص
# =========================================================

def transcribe_audio(audio_bytes):

    audio_base64 = base64.b64encode(
        audio_bytes
    ).decode("utf-8")

    response = requests.post(
        "https://openrouter.ai/api/v1/audio/transcriptions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/whisper-1",
            "input_audio": {
                "data": audio_base64,
                "format": "wav"
            }
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data.get("text", "").strip()


# =========================================================
# تحويل الرد إلى صوت
# =========================================================

def text_to_speech(text):

    response = requests.post(
        "https://openrouter.ai/api/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-4o-mini-tts-2025-12-15",
            "input": text,
            "voice": "alloy",
            "response_format": "mp3"
        },
        timeout=120
    )

    if not response.ok:
        return None

    return response.content


# =========================================================
# المحادثة الصوتية المستقلة
# =========================================================

if st.session_state.voice_call:

    st.markdown("### 📞 محادثة Yosef AI الصوتية")

    st.caption(
        "اضغط الميكروفون وتكلم، ثم سيستمع Yosef AI ويرد عليك."
    )

    voice_message = st.audio_input(
        "🎙️ اضغط هنا وتكلم"
    )

    if voice_message:

        with st.spinner(
            "🎧 Yosef AI بيسمعك..."
        ):

            try:

                voice_bytes = (
                    voice_message.getvalue()
                )

                spoken_text = transcribe_audio(
                    voice_bytes
                )

            except Exception as e:

                st.error(
                    f"حدث خطأ في تحويل الصوت: {e}"
                )

                spoken_text = ""

        if spoken_text:

            with st.chat_message("user"):
                st.markdown(spoken_text)

            # بحث تلقائي
            content = [
                {
                    "type": "text",
                    "text": spoken_text
                }
            ]

            if needs_web_search(
                spoken_text
            ):

                results = search_web(
                    spoken_text
                )

                if results:

                    search_text = (
                        "\n\n"
                        "معلومات حديثة من البحث:\n\n"
                    )

                    for result in results:

                        search_text += (
                            f"{result.get('title', '')}\n"
                            f"{result.get('href', '')}\n\n"
                        )

                    content.append({
                        "type": "text",
                        "text": search_text
                    })

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

            with st.spinner(
                "🤖 Yosef AI بيفكر..."
            ):

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

            with st.chat_message("assistant"):

                st.markdown(answer)

                with st.spinner(
                    "🔊 جاري تجهيز صوت Yosef AI..."
                ):

                    audio_reply = text_to_speech(
                        answer
                    )

                if audio_reply:

                    st.audio(
                        audio_reply,
                        format="audio/mp3",
                        autoplay=True
                    )

                else:

                    st.warning(
                        "تم إنشاء الرد، لكن تعذر تشغيل الصوت."
                    )

            st.session_state.messages.append({
                "role": "user",
                "content": spoken_text
            })

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })


# =========================================================
# الشات العادي
# =========================================================

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


# =========================================================
# الرسالة العادية
# =========================================================

if prompt:

    try:

        prompt_text = prompt.text or ""

        uploaded_file = (
            prompt.files[0]
            if prompt.files
            else None
        )

        # -----------------------------------------
        # الصوت العادي
        # -----------------------------------------

        if prompt.audio:

            with st.spinner(
                "🎙️ جاري تحويل صوتك إلى نص..."
            ):

                prompt_text = transcribe_audio(
                    prompt.audio.getvalue()
                )

        if not prompt_text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو سجل صوت أو ارفع ملف."
            )

            st.stop()

        # -----------------------------------------
        # عرض المستخدم
        # -----------------------------------------

        with st.chat_message("user"):

            if prompt_text:
                st.markdown(prompt_text)

            if uploaded_file:

                file_type = (
                    uploaded_file.type or ""
                )

                if file_type.startswith("image/"):

                    st.image(
                        uploaded_file
                    )

                else:

                    st.caption(
                        f"📎 {uploaded_file.name}"
                    )

        # -----------------------------------------
        # المحتوى
        # -----------------------------------------

        content = [
            {
                "type": "text",
                "text": prompt_text
            }
        ]

        # -----------------------------------------
        # الصورة
        # -----------------------------------------

        if uploaded_file:

            file_type = (
                uploaded_file.type or ""
            )

            if file_type.startswith("image/"):

                image_base64 = base64.b64encode(
                    uploaded_file.getvalue()
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

        # -----------------------------------------
        # بحث تلقائي ومخفي
        # -----------------------------------------

        if needs_web_search(prompt_text):

            results = search_web(
                prompt_text
            )

            if results:

                search_text = (
                    "\n\n"
                    "معلومات حديثة من البحث:\n\n"
                )

                for result in results:

                    search_text += (
                        f"{result.get('title', '')}\n"
                        f"{result.get('href', '')}\n\n"
                    )

                content.append({
                    "type": "text",
                    "text": search_text
                })

        # -----------------------------------------
        # تاريخ المحادثة
        # -----------------------------------------

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

        # -----------------------------------------
        # AI
        # -----------------------------------------

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

        # -----------------------------------------
        # الرد
        # -----------------------------------------

        with st.chat_message("assistant"):

            st.markdown(answer)

            audio_reply = text_to_speech(
                answer
            )

            if audio_reply:

                st.audio(
                    audio_reply,
                    format="audio/mp3"
                )

        # -----------------------------------------
        # حفظ
        # -----------------------------------------

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
