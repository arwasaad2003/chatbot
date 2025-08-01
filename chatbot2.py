from PIL import Image
import io
import os
import tempfile
from gtts import gTTS
import google.generativeai as genai
import streamlit as st

# إعداد Gemini API
API_KEY = "AIzaSyAwrmq-qt8m-5SvZtCtc8OCaE78fNu9UYQ"
model = genai.GenerativeModel("models/gemini-1.5-flash")
genai.configure(api_key=API_KEY)

# إعداد صفحة Streamlit
st.set_page_config(page_title="Tourism & Museum Chatbot", layout="centered")
st.markdown("""
    <h1 style='text-align: center;'>🗿 Tourism & Museum Chatbot</h1>
    <p style='text-align: center;'>اسأل عن معالم مصر، التاريخ، المتاحف، أو ارفع صورة تمثال لتحليله!</p>
""", unsafe_allow_html=True)

# الحالة العامة للمحادثة
if "messages" not in st.session_state:
    st.session_state.messages = []
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# اختيار وسيلة الإدخال
input_method = st.selectbox("🎛️ اختر طريقة الإدخال:", ["كتابة فقط", "رفع صورة", "تصوير بالكاميرا"])

# معالجة الصورة في حالة الرفع أو الالتقاط
image_data = None
if input_method == "رفع صورة":
    uploaded_image = st.file_uploader("📁 ارفع صورة من جهازك", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        image_data = uploaded_image.read()
        st.image(Image.open(io.BytesIO(image_data)), caption="📸 الصورة المرفوعة", use_container_width=True)

elif input_method == "تصوير بالكاميرا":
    camera_image = st.camera_input("📷 التقط صورة بالكاميرا")
    if camera_image:
        image_data = camera_image.read()
        st.image(Image.open(io.BytesIO(image_data)), caption="📸 الصورة الملتقطة", use_container_width=True)

# عرض الرسائل في واجهة الشات
for msg in st.session_state.messages:
    with st.chat_message("👤" if msg["role"] == "user" else "🤖"):
        st.markdown(f"<div style='color: black;'>{msg['content']}</div>", unsafe_allow_html=True)
        if msg["role"] == "bot":
            lang = "ar" if any('\u0600' <= c <= '\u06FF' for c in msg["content"]) else "en"
            tts = gTTS(msg["content"], lang=lang)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                audio_path = fp.name
            with open(audio_path, "rb") as audio_file:
                st.audio(audio_file.read(), format="audio/mp3")
            os.remove(audio_path)

# واجهة الإدخال
with st.container():
    col1, col2 = st.columns([8, 1])

    default_value = "" if st.session_state.clear_input else st.session_state.get("message_input", "")
    with col1:
        user_input = st.text_input("💬", value=default_value, placeholder="اكتب سؤالك هنا...", label_visibility="collapsed", key="message_input")
    with col2:
        if st.button("🚀", key="send_button"):
            if not user_input.strip() and not image_data:
                st.warning("يرجى كتابة سؤال أو رفع صورة أولاً.")
            else:
                # إضافة رسالة المستخدم
                if user_input.strip():
                    st.session_state.messages.append({"role": "user", "content": user_input.strip()})

                # إعداد البيانات للنموذج
                parts = []
                if user_input.strip():
                    parts.append({"text": user_input.strip()})
                if image_data:
                    mime_type = "image/png" if input_method == "رفع صورة" and uploaded_image.type == "image/png" else "image/jpeg"
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data
                        }
                    })

                # الحصول على رد من Gemini
                try:
                    response = model.generate_content(parts, generation_config={"temperature": 0.4})
                    reply = response.text.strip()
                except Exception as e:
                    reply = f"حدث خطأ أثناء محاولة الحصول على الرد: {e}"

                # حفظ رد البوت
                st.session_state.messages.append({"role": "bot", "content": reply})

                # إعادة تهيئة حقل الإدخال
                st.session_state.clear_input = True
                st.rerun()

# إعادة تعيين حالة الإدخال بعد إعادة تشغيل التطبيق
if st.session_state.clear_input:
    st.session_state.clear_input = False
