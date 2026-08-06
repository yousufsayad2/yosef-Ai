import streamlit as st
from google import genai

st.set_page_config(
    page_title="Yosef AI",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Yosef AI")

api_key = st.text_input(
    "Gemini API Key",
    type="password"
)

if api_key:

    client = genai.Client(api_key=api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

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
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            answer = response.text

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

else:
    st.info("🔑 أدخل مفتاح Gemini API للبدء.")
