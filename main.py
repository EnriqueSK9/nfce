import streamlit as st
import cv2
from PIL import Image
from streamlit_qrcode_scanner import qrcode_scanner
from pyzbar.pyzbar import decode

cam = cv2.VideoCapture(0)

if cam.isOpened():
    st.write("Camera available")

    qr_data = qrcode_scanner()

    if qr_data:
        st.success("Valid QR Code")
        st.write(qr_data)

else:
    st.error("No camera available")

cam.release()

uploaded_file = st.file_uploader(
    "Upload QR Code Image",
    type="image"
)

if uploaded_file:
    image = Image.open(uploaded_file)

    st.image(image)
    st.text(decode(image)[0].data.decode("utf-8"))

