import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖"
)

st.title("🤖 Yosef AI")
st.write("أهلاً بيك 👋")
st.write("أنا Yosef AI، مساعدك الذكي. اسألني أي حاجة!")
api_key = st.secrets["OPENROUTER_API_KEY"]

if api_key:

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
with st.popover("➕"):
    uploaded_file = st.file_uploader(
        "📎 صورة أو مستند",
        type=["txt", "pdf", "png", "jpg", "jpeg"]
    )

    if st.button("📷 الكاميرا"):
        st.session_state.show_camera = True

    if st.session_state.get("show_camera", False):
        camera_image = st.camera_input("📷 التقط صورة")
prompt = st.chat_input("اكتب رسالتك...")
if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

                  try:
        content = [{"type": "text", "text": prompt}]
        image_file = None

        if uploaded_file and uploaded_file.type.startswith("image/"):
            image_file = uploaded_file
        elif camera_image:
            image_file = camera_image

        if image_file:
            image_bytes = image_file.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_file.type};base64,{image_base64}"
                }
            })
            })

        api_messages = [
            {"role": "system", "content": system_prompt},
            *st.session_state.messages[:-1],
            {"role": "user", "content": content}
        ]

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=api_messages
        )

        

        answer = response.choices[0].message.content

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        with st.chat_message("assistant"):
            st.markdown(answer)

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
