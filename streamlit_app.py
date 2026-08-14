import streamlit as st
from openai import OpenAI
import base64
import re
import requests
import io
import threading
import queue
import time
import wave
import numpy as np

from streamlit_webrtc import (
    webrtc_streamer,
    WebRtcMode,
    create_audio_sink_track,
    create_pcm_audio_source_track,
)


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered",
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
        margin-bottom: 20px;
    }

    .call-title {
        text-align: center;
        font-size: 22px;
        font-weight: 700;
        margin-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# OpenRouter
# =========================================================

api_key = st.secrets["OPENROUTER_API_KEY"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)


# =========================================================
# Session State
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_call" not in st.session_state:
    st.session_state.voice_call = False

if "voice_job" not in st.session_state:
    st.session_state.voice_job = None

if "voice_lock" not in st.session_state:
    st.session_state.voice_lock = threading.Lock()

if "voice_in_queue" not in st.session_state:
    st.session_state.voice_in_queue = queue.Queue()

if "voice_audio_source" not in st.session_state:
    st.session_state.voice_audio_source = None

if "voice_last_text" not in st.session_state:
    st.session_state.voice_last_text = ""

if "voice_last_answer" not in st.session_state:
    st.session_state.voice_last_answer = ""


# =========================================================
# تعليمات Yosef
# =========================================================

system_prompt = """
أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.

عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.

لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI.

أجب باللغة التي يستخدمها المستخدم.

كن طبيعيًا وودودًا ومختصرًا في المحادثة الصوتية.
لا تكرر كلام المستخدم بدون سبب.

إذا تم إعطاؤك معلومات من البحث على الإنترنت:
- استخدم المعلومات المتاحة.
- لا تخترع معلومات.
- إذا كانت المعلومات غير كافية، وضح ذلك.
- لا تذكر تفاصيل البحث الداخلية للمستخدم.
"""


# =========================================================
# العنوان
# =========================================================

st.markdown(
    '<div class="yosef-title">🤖 Yosef AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="yosef-subtitle">'
    'أهلاً بيك 👋<br>'
    'أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# محادثة جديدة
# =========================================================

if st.button(
    "🆕 محادثة جديدة",
    use_container_width=True,
):

    st.session_state.messages = []
    st.session_state.voice_call = False
    st.session_state.voice_last_text = ""
    st.session_state.voice_last_answer = ""

    st.rerun()


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
        "match",
    ]

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in keywords
    )


# =========================================================
# البحث
# =========================================================

def search_web(query):

    try:

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={
                "q": query,
            },
            headers={
                "User-Agent": "Mozilla/5.0",
            },
            timeout=15,
        )

        if response.status_code != 200:
            return []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )

        matches = pattern.findall(
            response.text
        )

        results = []

        for href, title in matches[:5]:

            title = re.sub(
                r"<.*?>",
                "",
                title,
            ).strip()

            results.append(
                {
                    "title": title,
                    "href": href,
                }
            )

        return results

    except Exception:
        return []


# =========================================================
# سؤال Yosef
# =========================================================

def ask_yosef(text):

    content = [
        {
            "type": "text",
            "text": text,
        }
    ]

    if needs_web_search(text):

        results = search_web(text)

        if results:

            search_text = (
                "\n\n"
                "معلومات حديثة من البحث:\n\n"
            )

            for result in results:

                title = result.get(
                    "title",
                    "",
                )

                url = result.get(
                    "href",
                    "",
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
                    "text": search_text,
                }
            )

    api_messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    for message in st.session_state.messages:

        api_messages.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )

    api_messages.append(
        {
            "role": "user",
            "content": content,
        }
    )

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=api_messages,
        max_tokens=500,
    )

    return (
        response.choices[0]
        .message.content
        or "مش عارف أجاوب على ده دلوقتي."
    )


# =========================================================
# OpenRouter STT
# =========================================================

def transcribe_wav(wav_bytes):

    audio_b64 = base64.b64encode(
        wav_bytes
    ).decode("utf-8")

    response = requests.post(
        "https://openrouter.ai/api/v1/audio/transcriptions",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/whisper-1",
            "input_audio": {
                "data": audio_b64,
                "format": "wav",
            },
            "language": "ar",
        },
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "text",
        "",
    ).strip()


# =========================================================
# OpenRouter TTS
# =========================================================

def make_speech(text):

    response = requests.post(
        "https://openrouter.ai/api/v1/audio/speech",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-4o-mini-tts-2025-12-15",
            "input": text,
            "voice": "alloy",
            "response_format": "pcm",
        },
        timeout=60,
    )

    response.raise_for_status()

    return response.content


# =========================================================
# تحويل PCM إلى int16
# =========================================================

def pcm_to_numpy(pcm_bytes):

    if not pcm_bytes:
        return np.zeros(
            0,
            dtype=np.int16,
        )

    return np.frombuffer(
        pcm_bytes,
        dtype=np.int16,
    )


# =========================================================
# تحويل WebRTC Frame إلى PCM
# =========================================================

def frame_to_pcm(frame):

    array = frame.to_ndarray()

    if array.ndim == 2:

        if array.shape[0] == 1:
            array = array[0]

        elif array.shape[1] == 1:
            array = array[:, 0]

        else:
            array = array.mean(
                axis=0
            )

    array = np.asarray(
        array,
        dtype=np.int16,
    )

    return array


# =========================================================
# WAV
# =========================================================

def pcm_to_wav(
    pcm_bytes,
    sample_rate,
):

    buffer = io.BytesIO()

    with wave.open(
        buffer,
        "wb",
    ) as wav_file:

        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        wav_file.writeframes(
            pcm_bytes
        )

    return buffer.getvalue()


# =========================================================
# عامل المحادثة الصوتية
# =========================================================

def voice_worker(
    input_queue,
    output_source,
    stop_event,
):

    speech_buffer = []

    sample_rate = 48000

    speaking = False
    last_voice_time = time.time()

    silence_seconds = 0.85

    min_utterance_seconds = 0.45

    while not stop_event.is_set():

        try:

            frame = input_queue.get(
                timeout=0.1
            )

        except queue.Empty:

            continue

        try:

            pcm = frame_to_pcm(
                frame
            )

            sample_rate = (
                frame.sample_rate
            )

            if len(pcm) == 0:
                continue

            rms = float(
                np.sqrt(
                    np.mean(
                        pcm.astype(
                            np.float32
                        ) ** 2
                    )
                )
            )

            # مستوى الصوت
            voice_detected = rms > 700

            if voice_detected:

                speaking = True
                last_voice_time = time.time()

                speech_buffer.append(
                    pcm
                )

            elif speaking:

                speech_buffer.append(
                    pcm
                )

                silence_duration = (
                    time.time()
                    - last_voice_time
                )

                if silence_duration >= silence_seconds:

                    audio = np.concatenate(
                        speech_buffer
                    )

                    speech_buffer = []
                    speaking = False

                    duration = (
                        len(audio)
                        / float(sample_rate)
                    )

                    if duration < min_utterance_seconds:
                        continue

                    wav_bytes = pcm_to_wav(
                        audio.tobytes(),
                        sample_rate,
                    )

                    try:

                        spoken_text = (
                            transcribe_wav(
                                wav_bytes
                            )
                        )

                    except Exception:

                        continue

                    if not spoken_text:
                        continue

                    try:

                        answer = ask_yosef(
                            spoken_text
                        )

                    except Exception:

                        continue

                    try:

                        pcm_reply = make_speech(
                            answer
                        )

                        output_source.push(
                            pcm_to_numpy(
                                pcm_reply
                            )
                        )

                    except Exception:

                        continue

        except Exception:

            continue


# =========================================================
# إنشاء موارد المكالمة
# =========================================================

def start_voice_resources():

    if (
        st.session_state.voice_audio_source
        is None
    ):

        st.session_state.voice_audio_source = (
            create_pcm_audio_source_track(
                key="yosef-output",
                sample_rate=24000,
                ptime=20,
                lifecycle_scope="streamlit-session",
            )
        )

    if (
        st.session_state.voice_job
        is None
    ):

        stop_event = threading.Event()

        worker = threading.Thread(
            target=voice_worker,
            args=(
                st.session_state.voice_in_queue,
                st.session_state.voice_audio_source,
                stop_event,
            ),
            daemon=True,
        )

        worker.start()

        st.session_state.voice_job = (
            stop_event,
            worker,
        )


# =========================================================
# إيقاف المكالمة
# =========================================================

def stop_voice_resources():

    job = st.session_state.voice_job

    if job:

        stop_event, worker = job

        stop_event.set()

        st.session_state.voice_job = None

    if (
        st.session_state.voice_audio_source
        is not None
    ):

        try:

            st.session_state.voice_audio_source.clear()

        except Exception:

            pass

        st.session_state.voice_audio_source = None


# =========================================================
# عرض المحادثة السابقة
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# زر المكالمة
# =========================================================

if not st.session_state.voice_call:

    call_button = st.button(
        "📞 بدء مكالمة صوتية",
        use_container_width=True,
    )

    if call_button:

        st.session_state.voice_call = True

        start_voice_resources()

        st.rerun()

else:

    st.markdown(
        '<div class="call-title">'
        '📞 Yosef AI بيتكلم معاك'
        '</div>',
        unsafe_allow_html=True,
    )

    stop_button = st.button(
        "🔴 إنهاء المكالمة",
        use_container_width=True,
    )

    if stop_button:

        st.session_state.voice_call = False

        stop_voice_resources()

        st.rerun()


# =========================================================
# وضع المكالمة
# =========================================================

if st.session_state.voice_call:

    start_voice_resources()

    audio_sink = create_audio_sink_track(
        key="yosef-input",
        lifecycle_scope="streamlit-session",
    )

    ctx = webrtc_streamer(
        key="yosef-realtime-call",
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={
            "audio": True,
            "video": False,
        },
        sink_audio_track=audio_sink,
        source_audio_track=(
            st.session_state.voice_audio_source
        ),
        rtc_configuration={
            "iceServers": [
                {
                    "urls": [
                        "stun:stun.l.google.com:19302"
                    ]
                }
            ]
        },
        media_stream_constraints={
            "audio": True,
            "video": False,
        },
        sendback_audio=True,
        async_processing=True,
    )

    if ctx.state.playing:

        try:

            while True:

                frames = (
                    audio_sink.get_frames(
                        timeout=0.05
                    )
                )

                if not frames:
                    break

                for frame in frames:

                    st.session_state.voice_in_queue.put(
                        frame
                    )

        except Exception:

            pass

    st.caption(
        "🎙️ اتكلم بشكل طبيعي. لما تسكت لحظة، Yosef هيرد عليك."
    )


# =========================================================
# الشات العادي
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
        "docx",
    ],
)


# =========================================================
# معالجة الشات
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
        # صوت عادي
        # -----------------------------------------

        if prompt.audio:

            audio_bytes = (
                prompt.audio.getvalue()
            )

            try:

                prompt_text = transcribe_wav(
                    audio_bytes
                )

            except Exception as e:

                st.error(
                    "❌ تعذر تحويل التسجيل إلى نص: "
                    + str(e)
                )

                st.stop()


        if not prompt_text and not uploaded_file:

            st.warning(
                "اكتب رسالة أو استخدم الميكروفون أو ارفع ملف."
            )

            st.stop()


        # -----------------------------------------
        # المستخدم
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
        # المحتوى
        # -----------------------------------------

        content = [
            {
                "type": "text",
                "text": prompt_text,
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

                image_base64 = (
                    base64.b64encode(
                        uploaded_file.getvalue()
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
                        },
                    }
                )


        # -----------------------------------------
        # البحث
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
                        result.get(
                            "title",
                            "",
                        )
                        + "\n"
                        + result.get(
                            "href",
                            "",
                        )
                        + "\n\n"
                    )

                content.append(
                    {
                        "type": "text",
                        "text": search_text,
                    }
                )


        # -----------------------------------------
        # الرسائل
        # -----------------------------------------

        api_messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        for message in st.session_state.messages:

            api_messages.append(
                {
                    "role": message["role"],
                    "content": message["content"],
                }
            )

        api_messages.append(
            {
                "role": "user",
                "content": content,
            }
        )


        # -----------------------------------------
        # AI
        # -----------------------------------------

        with st.spinner(
            "🤖 Yosef AI بيفكر..."
        ):

            response = client.chat.completions.create(
                model="openrouter/free",
                messages=api_messages,
                max_tokens=800,
            )

        answer = (
            response.choices[0]
            .message.content
            or "لم أتمكن من إنشاء رد."
        )


        # -----------------------------------------
        # الرد
        # -----------------------------------------

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                answer
            )


        # -----------------------------------------
        # حفظ
        # -----------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt_text,
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )


    except Exception as e:

        st.error(
            "حدث خطأ: "
            + str(e)
                    )
