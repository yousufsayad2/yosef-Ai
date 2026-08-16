# =========================================================
# المرفقات
# =========================================================

if "pending_attachment" not in st.session_state:
    st.session_state.pending_attachment = None


# =========================================================
# تصميم زر +
# =========================================================

st.markdown(
    """
    <style>

    /* زر المرفقات يكون قريب من خانة الكتابة */
    div[data-testid="stPopover"] {
        position: fixed !important;
        left: 18px !important;
        bottom: 18px !important;
        z-index: 999999 !important;
    }

    div[data-testid="stPopover"] > button {
        width: 44px !important;
        height: 44px !important;
        min-height: 44px !important;

        border-radius: 50% !important;

        font-size: 28px !important;
        font-weight: 400 !important;

        padding: 0 !important;

        background: transparent !important;
        border: none !important;

        color: inherit !important;
    }

    /* قائمة المرفقات */
    div[data-testid="stPopoverBody"] {
        min-width: 210px !important;
        border-radius: 16px !important;
    }

    /* نخلي خانة الكتابة الأصلية في مكانها */
    div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 10px !important;
        left: 10px !important;
        right: 10px !important;
        z-index: 999998 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# زر +
# =========================================================

with st.popover(
    "＋",
    use_container_width=False
):

    st.markdown(
        "### 📎 إضافة إلى Yosef AI"
    )

    # -----------------------------------------------------
    # الصورة
    # -----------------------------------------------------

    image_file = st.file_uploader(
        "🖼️ صورة من الهاتف",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        accept_multiple_files=False,
        key="yosef_image",
    )

    if image_file is not None:

        st.session_state.pending_attachment = {
            "name": image_file.name,
            "type": image_file.type or "image/jpeg",
            "data": image_file.getvalue(),
        }


    # -----------------------------------------------------
    # الكاميرا
    # -----------------------------------------------------

    camera_file = st.camera_input(
        "📷 الكاميرا",
        key="yosef_camera",
    )

    if camera_file is not None:

        st.session_state.pending_attachment = {
            "name": "camera_photo.jpg",
            "type": "image/jpeg",
            "data": camera_file.getvalue(),
        }


    # -----------------------------------------------------
    # الملفات
    # -----------------------------------------------------

    document_file = st.file_uploader(
        "📄 ملف",
        type=[
            "pdf",
            "docx",
            "txt",
        ],
        accept_multiple_files=False,
        key="yosef_document",
    )

    if document_file is not None:

        st.session_state.pending_attachment = {
            "name": document_file.name,
            "type": document_file.type or "",
            "data": document_file.getvalue(),
        }


# =========================================================
# المرفق الحالي
# =========================================================

attachment = st.session_state.pending_attachment

if attachment:

    file_type = attachment["type"]
    file_data = attachment["data"]
    file_name = attachment["name"]

    st.markdown(
        "📎 **المرفق المحدد:** "
        + file_name
    )

    if file_type.startswith("image/"):

        st.image(
            file_data,
            width=180
        )

    if st.button(
        "🗑️ إزالة المرفق",
        key="remove_attachment"
    ):

        st.session_state.pending_attachment = None

        st.rerun()


# =========================================================
# خانة الكتابة الأصلية
# =========================================================

prompt = st.chat_input(
    "اكتب رسالتك..."
)


# =========================================================
# إرسال الرسالة
# =========================================================

if prompt:

    user_text = prompt.strip()

    extra_content = []

    attachment = (
        st.session_state.pending_attachment
    )


    # =====================================================
    # معالجة المرفق
    # =====================================================

    if attachment:

        file_type = attachment["type"]
        file_data = attachment["data"]
        file_name = attachment["name"]


        # -------------------------------------------------
        # صورة
        # -------------------------------------------------

        if file_type.startswith("image/"):

            encoded = (
                base64.b64encode(
                    file_data
                )
                .decode("utf-8")
            )

            extra_content.append({

                "type":
                    "image_url",

                "image_url": {

                    "url":
                        (
                            f"data:"
                            f"{file_type};"
                            f"base64,"
                            f"{encoded}"
                        )
                }
            })


        # -------------------------------------------------
        # PDF / DOCX / TXT
        # -------------------------------------------------

        else:

            file_text = read_file_bytes(
                file_name,
                file_data
            )

            if file_text:

                extra_content.append({

                    "type":
                        "text",

                    "text":
                        (
                            "محتوى الملف "
                            "المرفق:\n\n"
                            + file_text[:20000]
                        )
                })


    # =====================================================
    # عرض المستخدم
    # =====================================================

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        st.markdown(
            user_text
        )

        if attachment:

            if file_type.startswith(
                "image/"
            ):

                st.image(
                    file_data,
                    width=300
                )

            else:

                st.caption(
                    "📎 "
                    + file_name
                )


    # =====================================================
    # رد Yosef AI
    # =====================================================

    with st.chat_message(
        "assistant",
        avatar="🤖"
    ):

        with st.spinner(
            "🤖 Yosef AI بيكتب..."
        ):

            answer = ask_ai(
                user_text,
                extra_content
            )

        st.markdown(
            answer
        )


    # =====================================================
    # حفظ المحادثة
    # =====================================================

    st.session_state.messages.append({

        "role":
            "user",

        "content":
            user_text
    })

    st.session_state.messages.append({

        "role":
            "assistant",

        "content":
            answer
    })


    # =====================================================
    # حذف المرفق
    # =====================================================

    st.session_state.pending_attachment = None

    st.rerun()
