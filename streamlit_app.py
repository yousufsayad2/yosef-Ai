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

prompt = st.chat_input(
    "اكتب رسالتك...",
    accept_file=True,
    file_type=["png", "jpg", "jpeg", "webp", "pdf", "txt", "docx"]
)

uploaded_file = None

if prompt:
    if prompt.files:
        uploaded_file = prompt.files[0]

    prompt_text = prompt.text
                  
      
            
            response = client.chat.completions.create(
                model="openrouter/free",
                messages=api_messages
            )

            answer = response.choices[0].message.content

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            with st.chat_message("assistant"):
                st.markdown(answer)

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
