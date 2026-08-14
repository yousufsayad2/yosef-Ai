import streamlit as st
from openai import OpenAI
import base64

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
    api_key=api_key,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

system_prompt = """أنت Yosef AI، مساعد ذكي داخل تطبيق اسمه Yosef AI.
عندما يسألك المستخدم عن اسمك، قل إن اسمك Yosef AI.
لا تقل إنك ChatGPT أو المساعد الرسمي لـ OpenAI."""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.button("🆕 محادثة جديدة"):
    st.session_state.messages = []
    st.rerun()

prompt = st.chat_input(
    "اكتب رسالتك...",
    accept_file=True,
    file_type=["png", "jpg", "jpeg", "webp", "txt", "pdf", "docx"]
)

if prompt:
    try:
        prompt_text = prompt.text or ""
        uploaded_file = prompt.files[0] if prompt.files else None

        # إظهار رسالة المستخدم فورًا
        with st.chat_message("user"):
            st.markdown(prompt_text)

            if uploaded_file:
                if (uploaded_file.type or "").startswith("image/"):
                    st.image(uploaded_file)

        content = [
            {
                "type": "text",
                "text": prompt_text
            }
        ]

        if uploaded_file:
            file_type = uploaded_file.type or ""

            if file_type.startswith("image/"):
                image_bytes = uploaded_file.getvalue()
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{file_type};base64,{image_base64}"
                    }
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
            messages=api_messages
        )

        answer = response.choices[0].message.content

        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.messages.append({
            "role": "user",
            "content": prompt_text
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
