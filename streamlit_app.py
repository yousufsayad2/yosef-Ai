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

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True
):

    st.session_state.messages = []
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

                search_text += (
                    f"{result['title']}\n"
                    f"{result['href']}\n\n"
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
# تشغيل الرد الصوتي
# =========================================================

def speak_text(text):

    safe_text = (
        text
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
        .replace("\n", " ")
    )

    html = """
    <script>
        const text = `__TEXT__`;

        if ("speechSynthesis" in window) {

            window.speechSynthesis.cancel();

            const speech =
                new SpeechSynthesisUtterance(text);

            speech.lang = "ar-SA";
            speech.rate = 1.0;
            speech.pitch = 1.0;

            window.speechSynthesis.speak(speech);
        }
    </script>
    """

    html = html.replace(
        "__TEXT__",
        safe_text
    )

    st.components.v1.html(
        html,
        height=1
    )


# =========================================================
# زر المحادثة الصوتية
# =========================================================

if not st.session_state.voice_call:

    st.markdown("### 🎙️")

    if st.button(
        "📞 بدء محادثة صوتية",
        use_container_width=True
    ):

        st.session_state.voice_call = True
        st.session_state.audio_frames = []

        st.rerun()


# =========================================================
# وضع المحادثة الصوتية
# =========================================================

if st.session_state.voice_call:

    st.markdown("---")

    st.markdown("## 📞 محادثة Yosef AI")

    st.success(
        "🟢 المحادثة الصوتية مفعّلة"
    )

    st.caption(
        "اسمح للمتصفح باستخدام الميكروفون، ثم اتكلم."
    )


    # -----------------------------------------
    # WebRTC
    # -----------------------------------------

    ctx = webrtc_streamer(
        key="yosef_voice_call",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={
            "audio": True,
            "video": False
        },
        audio_receiver_size=256
    )


    # -----------------------------------------
    # استقبال الصوت
    # -----------------------------------------

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


    # -----------------------------------------
    # إرسال الكلام إلى Yosef
    # -----------------------------------------

    if st.button(
        "🎙️ إرسال الكلام",
        use_container_width=True
    ):

        frames = st.session_state.audio_frames


        if not frames:

            st.warning(
                "اتكلم في الميكروفون الأول."
            )

        else:

            try:

                pcm_data = b""
                sample_rate = 48000


                # -----------------------------
                # تجميع الصوت
                # -----------------------------

                for frame in frames:

                    audio = frame.to_ndarray()


                    if len(audio.shape) > 1:

                        audio = audio[0]


                    pcm_data += audio.tobytes()

                    sample_rate = frame.sample_rate


                # -----------------------------
                # إنشاء WAV
                # -----------------------------

                wav_buffer = io.BytesIO()


                with wave.open(
                    wav_buffer,
                    "wb"
                ) as wav_file:

                    wav_file.setnchannels(1)

                    wav_file.setsampwidth(2)

                    wav_file.setframerate(
                        sample_rate
                    )

                    wav_file.writeframes(
                        pcm_data
                    )


                wav_buffer.seek(0)


                # -----------------------------
                # تحويل الصوت إلى نص
                # -----------------------------

                recognizer = sr.Recognizer()


                with sr.AudioFile(
                    wav_buffer
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


                st.session_state.audio_frames = []


                # -----------------------------
                # عرض كلام المستخدم
                # -----------------------------

                with st.chat_message("user"):

                    st.markdown(
                        spoken_text
                    )


                # -----------------------------
                # Yosef AI
                # -----------------------------

                with st.spinner(
                    "🤖 Yosef AI بيفكر..."
                ):

                    answer = ask_yosef(
                        spoken_text
                    )


                # -----------------------------
                # الرد
                # -----------------------------

                with st.chat_message("assistant"):

                    st.markdown(answer)

                    speak_text(answer)


                # -----------------------------
                # حفظ المحادثة
                # -----------------------------

                st.session_state.messages.append({
                    "role": "user",
                    "content": spoken_text
                })

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })


                st.rerun()


            except sr.UnknownValueError:

                st.error(
                    "❌ مش قادر أفهم الكلام. "
                    "اتكلم أوضح وجرب تاني."
                )


            except sr.RequestError:

                st.error(
                    "❌ خدمة التعرف على الصوت "
                    "غير متاحة حاليًا."
                )


            except Exception as e:

                st.error(
                    f"❌ حصل خطأ في المحادثة الصوتية: {e}"
                )


    # -----------------------------------------
    # إنهاء المكالمة
    # -----------------------------------------

    if st.button(
        "🔴 إنهاء المحادثة",
        use_container_width=True
    ):

        st.session_state.voice_call = False
        st.session_state.audio_frames = []

        st.rerun()


# =========================================================
# الشات العادي
# =========================================================

prompt = st.chat_input(
    "اكتب رسالتك أو استخدم الميكروفون 🎙️",
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
# معالجة الشات
# =========================================================

if prompt:

    try:

        prompt_text = prompt.text or ""


        # -----------------------------------------
        # الملف
        # -----------------------------------------

        uploaded_file = (
            prompt.files[0]
            if prompt.files
            else None
        )


        # -----------------------------------------
        # صوت الميكروفون العادي
        # -----------------------------------------

        if prompt.audio:

            st.info(
                "🎙️ تم تسجيل الصوت. "
                "جاري تحويله إلى نص..."
            )

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
                    "❌ خدمة تحويل الصوت إلى نص "
                    "غير متاحة."
                )

                st.stop()


        # -----------------------------------------
        # التأكد من وجود رسالة
        # -----------------------------------------

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

                st.markdown(
                    prompt_text
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

                    search_text += (
                        f"{result['title']}\n"
                        f"{result['href']}\n\n"
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
