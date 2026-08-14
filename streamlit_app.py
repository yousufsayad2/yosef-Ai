import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖"
)

st.title("🤖 Yosef AI")

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
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[
                {"role": "system", "content": system_prompt},
                *st.session_state.messages
            ]
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
