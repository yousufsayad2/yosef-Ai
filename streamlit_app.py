import streamlit as st
from openai import OpenAI
import base64
import io
import json
import re
import requests
import speech_recognition as sr
import streamlit.components.v1 as components


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# العنوان
# =========================================================

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
- بالنسبة للمعلومات الحالية مثل الطقس والأخبار والأسعار، اعتمد على نتائج البحث عند توفرها.
"""


# =========================================================
# عرض المحادثة السابقة
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# =========================================================
# محادثة جديدة
# =========================================================

if st.button("🆕 محادثة جديدة"):

    st.session_state.messages = []

    st.rerun()


# =========================================================
# تحديد الأسئلة التي تحتاج بحث
# =========================================================

def needs_web_search(text):

    keywords = [

        # الطقس
        "الطقس",
        "الجو",
        "درجة الحرارة",
        "حرارة",
        "هتمطر",
        "مطر",
        "رياح",

        # الأخبار
        "أخبار",
        "خبر",
        "الأخبار",
        "اخر الاخبار",
        "آخر الأخبار",

        # الأسعار
        "سعر",
        "الأسعار",
        "كام",
        "بكام",
        "سعر الدولار",
        "سعر الذهب",

        # الوقت الحالي
        "اليوم",
        "دلوقتي",
        "الآن",
        "حاليا",
        "حاليًا",
        "حالياً",

        # الجديد
        "أحدث",
        "آخر",
        "الجديد",

        # مواعيد ونتائج
        "موعد",
        "متى",
        "نتيجة",
        "نتائج",

        # الرياضة
        "مباراة",
        "مباريات",
        "ماتش",
        "ماتشات",
        "الدوري",

        # English
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
# بحث بسيط بدون ddgs
# =========================================================

def search_web(query):

    try:

        url = "https://html.duckduckgo.com/html/"

        response = requests.get(
            url,
            params={
                "q": query
            },
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Linux; Android 10) "
                    "AppleWebKit/537.36 "
                    "Chrome/120 Mobile Safari/537.36"
                )
            },
            timeout=15
        )

        if response.status_code != 200:
            return []

        html = response.text

        results = []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL
        )

        matches = pattern.findall(html)

        for href, title in matches[:5]:

            title = re.sub(
                r"<.*?>",
                "",
                title
            )

            title = title.strip()

            results.append({
                "title": title,
                "href": href
            })

        return results

    except Exception:

        return []


# =========================================================
# خانة الكتابة
# الميكروفون سيظهر داخلها تلقائياً
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
# عند إرسال رسالة
# =========================================================

if prompt:

    try:

        # =====================================================
        # النص
        # =====================================================

        prompt_text = prompt.text or ""


        # =====================================================
        # الملف
        # =====================================================

        uploaded_file = (

            prompt.files[0]

            if prompt.files

            else None

        )


        # =====================================================
        # تحويل الصوت إلى نص
        # =====================================================

        if prompt.audio:

            with st.spinner(
                "🎙️ جاري تحويل صوتك إلى نص..."
            ):

                audio_bytes = (
                    prompt.audio.getvalue()
                )

                recognizer = sr.Recognizer()

                audio_file = io.BytesIO(
                    audio_bytes
                )

                try:

                    with sr.AudioFile(
                        audio_file
                    ) as source:

                        audio_data = (
                            recognizer.record(source)
                        )


                    prompt_text = (
                        recognizer.recognize_google(
                            audio_data,
                            language="ar-EG"
                        )
                    )


                except sr.UnknownValueError:

                    st.error(
                        "❌ مش قادر أفهم التسجيل. "
                        "جرّب تتكلم أوضح."
                    )

                    st.stop()


                except sr.RequestError as e:

                    st.error(
                        "❌ خدمة تحويل الصوت إلى نص "
                        f"غير متاحة حاليًا: {e}"
                    )

                    st.stop()


                except Exception as e:

                    st.error(
                        f"❌ حصل خطأ في قراءة التسجيل: {e}"
                    )

                    st.stop()


        # =====================================================
        # التأكد من وجود رسالة
        # =====================================================

        if not prompt_text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو سجل صوت أو ارفع ملف."
            )

            st.stop()


        # =====================================================
        # عرض رسالة المستخدم
        # =====================================================

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

                    st.image(
                        uploaded_file
                    )

                else:

                    st.caption(
                        f"📎 {uploaded_file.name}"
                    )


        # =====================================================
        # محتوى الرسالة
        # =====================================================

        content = [

            {
                "type": "text",
                "text": prompt_text
            }

        ]


        # =====================================================
        # إضافة الصورة
        # =====================================================

        if uploaded_file:

            file_type = (
                uploaded_file.type or ""
            )


            if file_type.startswith("image/"):

                image_bytes = (
                    uploaded_file.getvalue()
                )


                image_base64 = (
                    base64.b64encode(
                        image_bytes
                    ).decode("utf-8")
                )


                content.append({

                    "type": "image_url",

                    "image_url": {

                        "url": (
                            f"data:{file_type};"
                            f"base64,{image_base64}"
                        )

                    }

                })


        # =====================================================
        # البحث التلقائي - مخفي عن المستخدم
        # =====================================================

        search_results = []


        if prompt_text and needs_web_search(
            prompt_text
        ):

            search_results = search_web(
                prompt_text
            )


        # =====================================================
        # إرسال نتائج البحث للذكاء الاصطناعي
        # =====================================================

        if search_results:

            search_text = (
                "\n\n"
                "معلومات تم العثور عليها "
                "من البحث على الإنترنت:\n\n"
            )


            for i, result in enumerate(
                search_results,
                start=1
            ):

                title = result.get(
                    "title",
                    ""
                )

                url = result.get(
                    "href",
                    ""
                )


                search_text += (

                    f"{i}. {title}\n"
                    f"الرابط: {url}\n\n"

                )


            content.append({

                "type": "text",

                "text": search_text

            })


        # =====================================================
        # تاريخ المحادثة
        # =====================================================

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


        # =====================================================
        # إرسال إلى Yosef AI
        # =====================================================

        response = (
            client.chat.completions.create(

                model="openrouter/free",

                messages=api_messages,

                max_tokens=800

            )
        )


        answer = (

            response.choices[0]
            .message.content

            or "لم أتمكن من إنشاء رد."

        )


        # =====================================================
        # عرض رد Yosef AI
        # =====================================================

        with st.chat_message("assistant"):

            st.markdown(answer)


            # =================================================
            # تشغيل الصوت تلقائياً
            # =================================================

            safe_answer = json.dumps(
                answer,
                ensure_ascii=False
            )


            components.html(

                f"""

                <script>

                const text = {safe_answer};

                function speakYosef() {{

                    try {{

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

                    }} catch (error) {{

                        console.log(error);

                    }}

                }}

                window.addEventListener(
                    "load",
                    function() {{

                        setTimeout(
                            speakYosef,
                            500
                        );

                    }}
                );

                </script>

                """,

                height=1
            )


        # =====================================================
        # حفظ المحادثة
        # =====================================================

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
