import streamlit as st
from openai import OpenAI
import base64
import re
import requests
import io
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
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .yosef-title {
        text-align: center;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .yosef-subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 25px;
    }

    .call-row {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 5px;
    }

    /* نخلي زر المكالمة صغير */
    div[data-testid="stButton"] button {
        border-radius: 12px;
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
- لا تذكر للمستخدم تفاصيل البحث الداخلية إلا إذا طلبها.
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
# البحث على الإنترنت
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

    # -----------------------------------------
    # البحث تلقائيًا ومخفيًا
    # -----------------------------------------

    if needs_web_search(text):

        results = search_web(text)

        if results:

            search_text = (
                "\n\n"
                "معلومات حديثة من البحث على الإنترنت:\n\n"
            )

            for result in results:

                title = result.get(
                    "title",
                    ""
                )

                url = result.get(
                    "href",
                    ""
                )

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


    # -----------------------------------------
    # OpenRouter
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

    return answer


# =========================================================
# تشغيل الرد الصوتي من المتصفح
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
# زر المكالمة الصوتية
# =========================================================

st.markdown(
    '<div class="call-row">',
    unsafe_allow_html=True
)

if not st.session_state.voice_call:

    call_button = st.button(
        "📞",
        key="voice_call_start",
        help="بدء محادثة صوتية"
    )

    if call_button:

        st.session_state.voice_call = True

        st.rerun()

else:

    call_button = st.button(
        "🔴",
        key="voice_call_stop",
        help="إنهاء المحادثة الصوتية"
    )

    if call_button:

        st.session_state.voice_call = False

        st.rerun()

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# =========================================================
# المحادثة الصوتية
# =========================================================

if st.session_state.voice_call:

    st.info(
        "📞 المحادثة الصوتية مفعّلة — سجل رسالتك من الميكروفون."
    )

    voice_audio = st.audio_input(
        "🎙️"
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
                "❌ مش قادر أفهم التسجيل. جرّب تتكلم أوضح."
            )

        except sr.RequestError:

            st.error(
                "❌ خدمة التعرف على الصوت غير متاحة حاليًا."
            )

        except Exception as e:

            st.error(
                "❌ حصل خطأ في المحادثة الصوتية: "
                + str(e)
            )


# =========================================================
# خانة الشات الرئيسية
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
# معالجة رسالة الشات
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
        # تحويل تسجيل الميكروفون إلى نص
        # -----------------------------------------

        if prompt.audio:

            try:

                audio_bytes = (
                    prompt.audio.getvalue()
                )

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
                    "🎙️ جاري تحويل صوتك إلى نص..."
                ):

                    prompt_text = (
                        recognizer.recognize_google(
                            audio_data,
                            language="ar-EG"
                        )
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


        # -----------------------------------------
        # التأكد من الرسالة
        # -----------------------------------------

        if not prompt_text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو استخدم الميكروفون أو ارفع ملف."
            )

            st.stop()


        # -----------------------------------------
        # عرض رسالة المستخدم
        # -----------------------------------------

        with st.chat_message("user"):

            if prompt_text:

                st.markdown(
                    prompt_text
                )

            if uploaded_file:

                file_type = (
                    uploaded_file.type or ""
                )

                if file_type.startswith(
                    "image/"
                ):

                    st.image(
                        uploaded_file
                    )

                else:

                    st.caption(
                        "📎 "
                        + uploaded_file.name
                    )


        # -----------------------------------------
        # محتوى الرسالة
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

            if file_type.startswith(
                "image/"
            ):

                image_bytes = (
                    uploaded_file.getvalue()
                )

                image_base64 = (
                    base64.b64encode(
                        image_bytes
                    ).decode("utf-8")
                )

                content.append(
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


        # -----------------------------------------
        # البحث التلقائي
        # -----------------------------------------

        if prompt_text and needs_web_search(
            prompt_text
        ):

            results = search_web(
                prompt_text
            )

            if results:

                search_text = (
                    "\n\n"
                    "معلومات حديثة من البحث:\n\n"
                )

                for result in results:

                    title = result.get(
                        "title",
                        ""
                    )

                    url = result.get(
                        "href",
                        ""
                    )

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


        # -----------------------------------------
        # Yosef AI
        # -----------------------------------------

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


        # -----------------------------------------
        # عرض الرد
        # -----------------------------------------

        with st.chat_message("assistant"):

            st.markdown(
                answer
            )


        # -----------------------------------------
        # حفظ المحادثة
        # -----------------------------------------

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


    except Exception as e:

        st.error(
            "حدث خطأ: "
            + str(e)
        )
