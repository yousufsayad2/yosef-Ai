import streamlit as st
from openai import OpenAI
import base64
import io
import speech_recognition as sr
import streamlit.components.v1 as components
import json
from ddgs import DDGS


# =========================
# إعداد الصفحة
# =========================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖"
)

st.title("🤖 Yosef AI")
st.write("أهلاً بيك 👋")
st.write("أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!")


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


# =========================
# تعليمات Yosef AI
# =========================

system_prompt = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

إذا تم تزويدك بنتائج بحث على الإنترنت:
- استخدمها للإجابة.
- لا تخترع معلومات غير موجودة في النتائج.
- إذا لم تكن النتائج كافية، قل إن المعلومات غير مؤكدة.
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
# إعدادات الصوت والبحث
# =========================

voice_enabled = st.checkbox(
    "🔊 تشغيل رد Yosef AI بصوت",
    value=False
)

web_enabled = st.checkbox(
    "🌐 البحث على الإنترنت عند الحاجة",
    value=True
)


# =========================
# تحديد هل السؤال يحتاج بحث
# =========================

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

        "حدث",
        "أحداث",

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


# =========================
# البحث على الإنترنت
# =========================

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


# =========================
# خانة الإدخال
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


# =========================
# عند إرسال رسالة
# =========================

if prompt:

    try:

        # =========================
        # النص
        # =========================

        prompt_text = prompt.text or ""


        # =========================
        # الملف
        # =========================

        uploaded_file = (
            prompt.files[0]
            if prompt.files
            else None
        )


        # =========================
        # تحويل الصوت إلى نص
        # =========================

        if prompt.audio:

            with st.spinner(
                "🎙️ جاري تحويل صوتك إلى نص..."
            ):

                audio_bytes = prompt.audio.getvalue()

                recognizer = sr.Recognizer()

                audio_file = io.BytesIO(
                    audio_bytes
                )

                with sr.AudioFile(audio_file) as source:

                    audio_data = recognizer.record(
                        source
                    )

                try:

                    prompt_text = recognizer.recognize_google(
                        audio_data,
                        language="ar-EG"
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


        # =========================
        # التأكد من وجود رسالة
        # =========================

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


        # =========================
        # تجهيز محتوى الرسالة
        # =========================

        content = [

            {
                "type": "text",
                "text": prompt_text
            }

        ]


        # =========================
        # إضافة الصورة
        # =========================

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


        # =========================
        # البحث
        # =========================

        search_results = []

        should_search = (

            web_enabled

            and prompt_text

            and needs_web_search(
                prompt_text
            )

        )


        if should_search:

            with st.spinner(
                "🌐 جاري البحث على الإنترنت..."
            ):

                search_results = search_web(
                    prompt_text
                )


        # =========================
        # إضافة نتائج البحث للـ AI
        # =========================

        if search_results:

            search_text = (
                "\n\n"
                "نتائج البحث على الإنترنت:\n\n"
            )


            for i, result in enumerate(
                search_results,
                start=1
            ):

                title = result.get(
                    "title",
                    "بدون عنوان"
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
                    f"الرابط: {url}\n"
                    f"المحتوى: {body}\n\n"

                )


            content.append(

                {
                    "type": "text",
                    "text": search_text
                }

            )


            # =========================
            # عرض المصادر
            # =========================

            with st.expander(
                "🌐 مصادر البحث"
            ):

                for result in search_results:

                    title = result.get(
                        "title",
                        "مصدر"
                    )

                    url = result.get(
                        "href",
                        ""
                    )

                    if url:

                        st.markdown(
                            f"- [{title}]({url})"
                        )


        elif should_search:

            st.info(
                "🌐 لم أتمكن من العثور على نتائج بحث."
            )


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


        # =========================
        # إرسال إلى Yosef AI
        # =========================

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


        # =========================
        # عرض الرد
        # =========================

        with st.chat_message("assistant"):

            st.markdown(answer)


            # =========================
            # تشغيل الصوت
            # =========================

            if voice_enabled:

                safe_answer = json.dumps(
                    answer,
                    ensure_ascii=False
                )


                components.html(

                    f"""

                    <div style="
                        text-align:center;
                        padding:5px;
                    ">

                        <button
                            onclick="speakAnswer()"
                            style="
                                border:0;
                                border-radius:12px;
                                padding:10px 18px;
                                font-size:16px;
                                cursor:pointer;
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
                            new SpeechSynthesisUtterance(
                                text
                            );

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
            f"حدث خطأ: {e}"
                )
