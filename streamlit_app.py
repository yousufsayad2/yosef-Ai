import streamlit as st
from google import genai

st.set_page_config(page_title="Yosef AI", page_icon="🤖")

st.title("🤖 Yosef AI")

api_key = st.text_input("Gemini API Key", type="password")

if api_key:
    try:
        client = genai.Client(api_key=api_key)

        if "chat" not in st.session_state:
            st.session_state.chat = client.chats.create(
                model="gemini-2.5-flash"
            )

        prompt = st.chat_input("اكتب رسالتك...")

        if prompt:
            st.chat_message("user").write(prompt)

            response = st.session_state.chat.send_message(prompt)

            st.chat_message("assistant").write(response.text)

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
else:
    st.info("أدخل مفتاح Gemini API للبدء.")
