import streamlit as st
from openai import OpenAI
import base64
import io
import re
import requests
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

MODEL_NAME = st.secrets.get(
    "OPENROUTER_MODEL",
    "openrouter/free"
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
- تحدث بطريقة طبيعية.
- اجعل الرد واضحًا ومختصرًا.
- لا تستخدم مقدمات طويلة.
- تعامل مع المستخدم كأنه يتحدث مع مساعد صوتي.

إذا أرسل المستخدم صورة:
- حلل الصورة.
- لا تخترع تفاصيل غير واضحة.

إذا أرسل المستخدم ملفًا:
- استخدم المعلومات المتاحة منه.
- لا تخترع محتوى الملف.

إذا أعطيتك معلومات من البحث:
- استخدم المعلومات الموجودة.
- لا تخترع معلومات غير موجودة.
"""


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .yosef-title {
        text-align: center;
        font-size: 34px;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 5px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 20px;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


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
        st.markdown(message["content"])


# =========================================================
# البحث الذكي
# =========================================================

def needs_web_search(text):
    if not text:
        return False

    text_lower = text.lower()

    explicit_words = [
        "ابحث",
        "ابحثلي",
        "ابحث لي",
        "دورلي",
        "دور لي",
        "شوفلي",
        "شوف لي",
        "على النت",
        "من النت",
        "على الإنترنت",
        "من الإنترنت",
        "search",
        "google",
        "look up"
    ]

    for word in explicit_words:
        if word in text_lower:
            return True

    current_words = [
        "اليوم",
        "دلوقتي",
        "دلوقت",
        "الآن",
        "حاليا",
        "حاليًا",
        "النهارده",
        "بكره",
        "غدا",
        "آخر",
        "اخر",
        "أحدث",
        "احدث",
        "الجديد",
        "current",
        "today",
        "now",
        "latest",
        "recent"
    ]

    for word in current_words:
        if word in text_lower:
            return True

    live_topics = [
        "أخبار",
        "اخبار",
        "خبر",
        "الأخبار",
        "الاخبار",
        "الطقس",
        "الجو",
        "درجة الحرارة",
        "مطر",
        "رياح",
        "سعر",
        "أسعار",
        "اسعار",
        "بكام",
        "الدولار",
        "اليورو",
        "الذهب",
        "البورصة",
        "مباراة",
        "مباريات",
        "ماتش",
        "نتيجة",
        "نتائج",
        "موعد",
        "news",
        "weather",
        "price",
        "prices",
        "score",
        "match"
    ]

    for word in live_topics:
        if word in text_lower:
            return True

    return False


# =========================================================
# البحث على الإنترنت
# =========================================================

def search_web(query):
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
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

            if clean_title and href:
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
# تجهيز نتائج البحث
# =========================================================

def get_search_context(query):
    if not needs_web_search(query):
        return ""

    results = search_web(query)

    if not results:
        return ""

    search_text = (
        "معلومات حديثة من البحث على الإنترنت:\n\n"
    )

    for result in results:
        search_text += (
            "العنوان: "
            + result["title"]
            + "\n"
            + "الرابط: "
            + result["href"]
            + "\n\n"
        )

    search_text += (
        "استخدم المعلومات السابقة للمساعدة في الإجابة. "
        "لا تخترع معلومات غير موجودة فيها."
    )

    return search_text


# =========================================================
# تحويل الرد إلى صوت
# =========================================================

def speak_text(text):
    if not text:
        return

    safe_text = str(text)

    safe_text = safe_text.replace("\\", "\\\\")
    safe_text = safe_text.replace("`", "\\`")
    safe_text = safe_text.replace("${", "\\${")
    safe_text = safe_text.replace("\n", " ")
    safe_text = safe_text.replace("\r", " ")

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


# =========================================================
# التعامل مع أخطاء OpenRouter
# =========================================================

def show_ai_error(error):
    error_text = str(error)

    if (
        "429" in error_text
        or "free-models-per-day" in error_text
        or "Rate limit exceeded" in error_text
    ):
        st.warning(
            "⏳ الحد المجاني للطلبات انتهى حاليًا."
        )
        st.info(
            "جرّب مرة أخرى بعد تجدد الحد المجاني."
        )
        return

    if "401" in error_text:
        st.error(
            "❌ مفتاح OpenRouter غير صحيح أو غير موجود."
        )
        return

    if "404" in error_text:
        st.error(
            "❌ الموديل غير متاح حاليًا."
        )
        return

    st.error(
        "❌ حصل خطأ أثناء تشغيل Yosef AI."
    )


# =========================================================
# سؤال Yosef AI
# =========================================================

def ask_yosef(text, extra_content=None):
    if not text:
        text = "ساعدني في هذا الطلب."

    content = [
        {
            "type": "text",
            "text": text
        }
    ]

    if extra_content:
        content.extend(extra_content)

    search_context = get_search_context(text)

    if search_context:
        content.append(
            {
                "type": "text",
                "text": search_context
            }
        )

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

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=api_messages,
            max_tokens=800
        )

        answer = (
            response.choices[0]
            .message.content
            or "لم أتمكن من إنشاء رد."
        )

        return answer

    except Exception as error:
        show_ai_error(error)
        return None


# =========================================================
# زر المحادثة الصوتية
# =========================================================

if not st.session_state.voice_call:
    if st.button(
        "📞 محادثة صوتية",
        use_container_width=True,
        key="start_voice_call"
    ):
        st.session_state.voice_call = True
        st.rerun()

else:
    st.success(
        "📞 المحادثة الصوتية مفعّلة"
    )

    if st.button(
        "🔴 إنهاء المحادثة الصوتية",
        use_container_width=True,
        key="stop_voice_call"
    ):
        st.session_state.voice_call = False
        st.rerun()


# =========================================================
# وضع المحادثة الصوتية
# =========================================================

if st.session_state.voice_call:
    st.markdown("---")

    st.subheader(
        "🎙️ اتكلم مع Yosef AI"
    )

    st.caption(
        "اضغط على الميكروفون وسجّل كلامك."
    )

    voice_audio = st.audio_input(
        "🎙️ الميكروفون",
        key="voice_microphone"
    )

    if voice_audio:
        try:
            audio_bytes = voice_audio.getvalue()
            audio_buffer = io.BytesIO(audio_bytes)

            recognizer = sr.Recognizer()

            with st.spinner(
                "🎧 Yosef AI بيسمعك..."
            ):
                with sr.AudioFile(audio_buffer) as source:
                    audio_data = recognizer.record(source)

                spoken_text = recognizer.recognize_google(
                    audio_data,
                    language="ar-EG"
                )

            with st.chat_message("user"):
                st.markdown(spoken_text)

            with st.spinner(
                "🤖 Yosef AI بيفكر..."
            ):
                answer = ask_yosef(spoken_text)

            if answer is not None:
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    speak_text(answer)

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

        except sr.UnknownValueError:
            st.error(
                "❌ مش قادر أفهم التسجيل. اتكلم أوضح وجرب تاني."
            )

        except sr.RequestError:
            st.error(
                "❌ خدمة تحويل الصوت إلى نص غير متاحة حاليًا."
            )

        except Exception as error:
            st.error(
                "❌ حصل خطأ في المحادثة الصوتية: "
                + str(error)
            )


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
# استقبال رسالة الشات
# =========================================================

if prompt:
    try:
        text = prompt.text or ""

        uploaded_file = None

        if prompt.files:
            uploaded_file = prompt.files[0]

        # -------------------------------------------------
        # تحويل صوت خانة الشات إلى نص
        # -------------------------------------------------

        if prompt.audio:
            try:
                audio_bytes = prompt.audio.getvalue()
                audio_buffer = io.BytesIO(audio_bytes)

                recognizer = sr.Recognizer()

                with sr.AudioFile(audio_buffer) as source:
                    audio_data = recognizer.record(source)

                with st.spinner(
                    "🎙️ جاري فهم صوتك..."
                ):
                    text = recognizer.recognize_google(
                        audio_data,
                        language="ar-EG"
                    )

            except sr.UnknownValueError:
                st.error(
                    "❌ مش قادر أفهم التسجيل."
                )
                st.stop()

            except sr.RequestError:
                st.error(
                    "❌ خدمة تحويل الصوت إلى نص غير متاحة."
                )
                st.stop()

        # -------------------------------------------------
        # التأكد من وجود رسالة
        # -------------------------------------------------

        if not text and not uploaded_file:
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
        # محتوى إضافي
        # -------------------------------------------------

        extra_content = []

        # -------------------------------------------------
        # الصورة
        # -------------------------------------------------

        if uploaded_file:
            file_type = uploaded_file.type or ""

            if file_type.startswith("image/"):
                image_bytes = uploaded_file.getvalue()

                image_base64 = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                extra_content.append(
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

            else:
                extra_content.append(
                    {
                        "type": "text",
                        "text": (
                            "المستخدم أرفق ملفًا اسمه: "
                            + uploaded_file.name
                            + "."
                        )
                    }
                )

        # -------------------------------------------------
        # سؤال Yosef
        # -------------------------------------------------

        with st.spinner(
            "🤖 Yosef AI بيفكر..."
        ):
            answer = ask_yosef(
                text,
                extra_content
            )

        if answer is None:
            st.stop()

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
        show_ai_error(error)
