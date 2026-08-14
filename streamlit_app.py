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


system_prompt = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

إذا تم إعطاؤك معلومات من البحث على الإنترنت،
استخدمها للإجابة ولا تخترع معلومات.
"""


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if st.button("🆕 محادثة جديدة"):
    st.session_state.messages = []
    st.rerun()


# أدوات صغيرة
col1, col2 = st.columns(2)

with col1:
    web_enabled = st.toggle(
        "🔎 بحث",
        value=True
    )

with col2:
    voice_enabled = st.toggle(
        "🔊 صوت الرد",
        value=False
    )


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

    for keyword in keywords:
        if keyword in text_lower:
            return True

    return False


def search_web(query):

    try:
        with DDGS(timeout=10) as ddgs:
            results = list(
                ddgs.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=5
                )
            )

        return results

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

    prompt_text = prompt.text or ""

    uploaded_file = (
        prompt.files[0]
        if prompt.files
        else None
    )


    # الصوت → نص
    if prompt.audio:

        with st.spinner("🎙️ جاري تحويل صوتك إلى نص..."):

            audio_bytes = prompt.audio.getvalue()

            recognizer = sr.Recognizer()

            audio_file = io.BytesIO(audio_bytes)

            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)

            try:
                prompt_text = recognizer.recognize_google(
                    audio_data,
                    language="ar-EG"
                )

            except sr.UnknownValueError:
                st.error(
                    "❌ مش قادر أفهم التسجيل. جرّب تتكلم أوضح."
                )
                st.stop()

            except sr.RequestError as e:
                st.error(
                    f"❌ خدمة تحويل الصوت غير متاحة: {e}"
                )
                st.stop()


    if not prompt_text and not uploaded_file:
        st.warning(
            "اكتب رسالة أو سجل صوت أو ارفع ملف."
        )
        st.stop()


    # عرض رسالة المستخدم
    with st.chat_message("user"):

        if prompt_text:
            st.markdown(prompt_text)

        if prompt.audio:
            st.caption(
                "🎙️ تم تحويل الرسالة الصوتية إلى نص."
            )

        if uploaded_file:

            file_type = uploaded_file.type or ""

            if file_type.startswith("image/"):
                st.image(uploaded_file)
            else:
                st.caption(
                    f"📎 {uploaded_file.name}"
                )


    # محتوى الرسالة
    content = [
        {
            "type": "text",
            "text": prompt_text
        }
    ]


    # الصورة
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
                            f"data:{file_type};"
                            f"base64,{image_base64}"
                        )
                    }
                }
            )


    # البحث
    search_results = []

    if web_enabled and prompt_text:

        if needs_web_search(prompt_text):

            with st.spinner("🔎 جاري البحث..."):
                search_results = search_web(
                    prompt_text
                )


    # إضافة نتائج البحث للذكاء الاصطناعي
    if search_results:

        search_text = (
            "معلومات حديثة من البحث على الإنترنت:\n\n"
        )

        for result in search_results:

            title = result.get("title", "")
            body = result.get("body", "")
            url = result.get("href", "")

           
