import streamlit as st
from openai import OpenAI
import base64
import io
import json
import speech_recognition as sr
import streamlit.components.v1 as components
from ddgs import DDGS

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
    api_key=api_key
)

if "messages" not in st.session_state:
    st.session_state.messages = []

system_prompt = """أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.
عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.
لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.
أجب باللغة التي يستخدمها المستخدم.
إذا تم تزويدك بنتائج بحث، استخدمها ولا تخترع معلومات غير موجودة فيها.
"""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.button("🆕 محادثة جديدة"):
    st.session_state.messages = []
    st.rerun()

col1, col2 = st.columns(2)

with col1:
    web_enabled = st.toggle("🔎 بحث", value=True)

with col2:
    voice_enabled = st.toggle("🔊 صوت الرد", value=False)


def needs_web_search(text):
    keywords = [
        "الطقس",
        "الجو",
        "درجة الحرارة",
        "أخبار",
        "خبر",
        "الأخبار",
        "سعر",
        "الأسعار",
        "اليوم",
        "دلوقتي",
        "الآن",
        "حاليا",
        "حاليًا",
        "أحدث",
        "آخر",
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
        "current"
    ]

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in keywords
    )


def search_web(query):
    try:
        with DDGS(timeout=10) as ddgs:
            return list(
                ddgs.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=5
                )
            )
    except Exception:
        return []


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

        if prompt.audio:

            with st.spinner(
                "🎙️ جاري تحويل صوتك إلى نص..."
            ):

                audio_bytes = (
                    prompt.audio.getvalue()
                )

                recognizer = sr.Recognizer()

                with sr.AudioFile(
                    io.BytesIO(audio_bytes)
                ) as source:

                    audio_data = recognizer.record(
                        source
                    )

                try:

                    prompt_text = (
                        recognizer.recognize_google(
                            audio_data,
                            language="ar-EG"
                        )
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

        if not prompt_text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو سجل صوت أو ارفع ملف."
            )

            st.stop()

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

        content = [
            {
                "type": "text",
                "text": prompt_text
            }
        ]

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

        should_search = (
            web_enabled
            and bool(prompt_text)
            and needs_web_search(prompt_text)
        )

        if should_search:

            with st.spinner(
                "🔎 جاري البحث..."
            ):

                search_results = search_web(
                    prompt_text
                )

            if search_results:

                search_text = (
                    "\n\n"
                    "معلومات حديثة من البحث:\n\n"
                )

                for i, result in enumerate(
                    search_results,
                    start=1
                ):

                    title = result.get(
                        "title",
                        ""
                    )

                    body = result.get(
                        "body",
                        ""
                    )

                    url = result.get(
                        "href",
                        ""
                    )

                    search_text += (
                        f"{i}. {title}\n"
                        f"{body}\n"
                        f"المصدر: {url}\n\n"
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

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=api_messages,
            max_tokens=800
        )

       
