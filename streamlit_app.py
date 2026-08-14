import streamlit as st
from openai import OpenAI
import base64
import re
import requests
import io
import wave
import speech_recognition as sr

from streamlit_webrtc import webrtc_streamer, WebRtcMode


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .yosef-title {
        text-align: center;
        font-size: 32px;
        font-weight: bold;
    }

    .yosef-subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 20px;
    }

    .voice-call-box {
        text-align: center;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
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

if "audio_frames" not in st.session_state:
    st.session_state.audio_frames = []


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
- إذا كانت المعلومات غير كافية، وضح ذلك.
- لا تذكر تفاصيل البحث الداخلية للمستخدم إلا إذا طلبها.
"""


# =========================================================
# العنوان
# =========================================================

st.markdown(
    '<div class="yosef-title">🤖 Yosef AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="yosef-subtitle">'
    'أهلاً بيك 👋<br>'
    'أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# محادثة جديدة
# =========================================================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):

    st.session_state.messages = []
    st.session_state.voice_call = False
    st.session_state.audio_frames = []

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

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in keywords
    )


# =========================================================
# البحث في الخلفية
# =========================================================

def search_web(query):

    try:

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )

        if response.status_code != 200:
            return []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL
        )

        matches = pattern.findall(response.text)

        results = []

        for href, title in matches[:5]:

            clean_title = re.sub(
                r"<.*?>",
                "",
                title
            ).strip()

            results.append(
                {
                    "title": clean_title,
                    "href": href
                }
            )

        return results

    except Exception:

        return []


# =========================================================
# سؤال Yosef AI
# =========================================================

def ask_yosef(text):

    content = [
        {
            "type": "text",
            "text": text
        }
    ]

    # البحث التلقائي والمخفي
    if needs_web_search(text):

        results = search_web(text)

        if results:

            search_text = (
                "\n\n"
                "معلومات حديثة من البحث على الإنترنت:\n\n"
            )

            for result in results:

                title = result.get("title", "")
                url = result.get("href", "")

                search_text += (
                    title
                    + "\n"
                    + url
                    + "\n\n"
                )

            content.append(
                {
                    "type": "text",
                    "text": search_text
                }
            )

    # تاريخ المحادثة
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

    api_messages.append(
        {
            "role": "user",
            "content": content
        }
    )

    # OpenRouter
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

    return answer


# =========================================================
# تشغيل الرد الصوتي
# =========================================================

def speak_text(text):

    safe_text = (
        text
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
        .replace("\n", " ")
        .replace("\r", " ")
    )

    html = (
        "<script>"
        "const text = `"
        + safe_text
        + "`;"
        ""
        "if ('speechSynthesis' in window) {"
        ""
        "window.speechSynthesis.cancel();"
        ""
        "const speech = "
        "new SpeechSynthesisUtterance(text);"
        ""
        "speech.lang = 'ar-SA';"
        "speech.rate = 1.0;"
        "speech.pitch = 1.0;"
        ""
        "window.speechSynthesis.speak(speech);"
        "}"
        "</script>"
    )

    st.components.v1.html(
        html,
        height=1
    )


# =========================================================
# زر المحادثة الصوتية
# =========================================================

st.markdown(
    '<div class="voice-call-box">',
    unsafe_allow_html=True
)

if not st.session_state.voice_call:

    start_call = st.button(
        "📞 محادثة صوتية",
        key="start_voice_call"
    )

    if start_call:

        st.session_state.voice_call = True
        st.session_state.audio_frames = []

        st.rerun()

else:

    stop_call = st.button(
        "🔴 إنهاء المكالمة",
        key="stop_voice_call"
    )

    if stop_call:

        st.session_state.voice_call = False
        st.session_state.audio_frames = []

        st.rerun()

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# =========================================================
# وضع المحادثة الصوتية
# =========================================================

if st.session_state.voice_call:

    st.markdown("---")

    st.subheader("📞 محادثة Yosef AI الصوتية")

    st.caption(
        "اسمح للمتصفح باستخدام الميكروفون واتكلم."
    )

    # WebRTC
    ctx = webrtc_streamer(
        key="yosef_voice_call",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={
            "audio": True,
            "video": False
        },
        audio_receiver_size=256
    )

    # استقبال الصوت
    if ctx.state.playing:

        try:

            frames = ctx.audio_receiver.get_frames(
                timeout=1
            )

            for frame in frames:

                st.session_state.audio_frames.append(
                    frame
                )

        except Exception:

            pass

    # إرسال الكلام
    if st.button(
        "🎙️ إرسال الكلام إلى Yosef",
        use_container_width=True
    ):

        frames = st.session_state.audio_frames

        if not frames:

            st.warning
