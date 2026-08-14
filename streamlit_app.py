import streamlit as st
from openai import OpenAI
import base64
import re
import requests
import io
import wave

from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av


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
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

إذا تم إعطاؤك معلومات من البحث على الإنترنت:
- استخدم المعلومات المتاحة.
- لا تخترع معلومات.
- إذا كانت المعلومات غير كافية وضح ذلك.
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

if st.button("🆕 محادثة جديدة"):

    st.session_state.messages = []
    st.session_state.voice_call = False

    st.rerun()


# =========================================================
# عرض المحادثة
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# =========================================================
# البحث التلقائي
# =========================================================

def needs_web_search(text):

    keywords = [
        "الطقس",
        "الجو",
        "درجة الحرارة",
        "مطر",
        "رياح",

        "أخبار",
        "خبر",
        "الأخبار",
        "آخر الأخبار",

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
        "ماتش",

        "today",
        "now",
        "latest",
        "news",
        "weather",
        "price",
        "current",
        "score",
        "match"
    ]

    text = text.lower()

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# البحث في الخلفية
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

            title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            results.append({
                "title": title,
                "href": href
            })

        return results

    except Exception:

        return []


# =========================================================
# الحصول على رد AI
# =========================================================

def ask_yosef(text):

    content = [
        {
            "type": "text",
            "text": text
        }
    ]

    # بحث تلقائي ومخفي
    if needs_web_search(text):

        results = search_web(text)

        if results:

            search_text = (
                "\n\n"
                "معلومات حديثة من البحث:\n\n"
            )

            for result in results:

                search_text += (
                    f"{result['title']}\n"
                    f"{result['href']}\n\n"
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

    return (
        response.choices[0]
        .message.content
        or "لم أتمكن من إنشاء رد."
    )


# =========================================================
# JavaScript لتحويل رد Yosef إلى صوت
# =========================================================

def speak_text(text):

    safe_text = (
        text
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    st.components.v1.html(
        f"""
        <script>

        const text = `{safe_text}`;

        if ("speechSynthesis" in window) {{

            window.speechSynthesis.cancel();

            const speech =
                new SpeechSynthesisUtterance(text);

            speech.lang = "ar-SA";
            speech.rate = 1.0;
            speech.pitch = 
