import streamlit as st
import cv2
from PIL import Image
from streamlit_qrcode_scanner import qrcode_scanner
from pyzbar.pyzbar import decode


qr_codes = []

cam = cv2.VideoCapture(0)
if cam.isOpened():
    st.write("Camera available")

    qr_data = qrcode_scanner()

    if qr_data:
        st.success("Valid QR Code")
        qr_codes.append(qr_data)

else:
    st.error("No camera available")

cam.release()

uploaded_file = st.file_uploader(
    "Upload QR Code Image",
    type="image"
)

if uploaded_file:
    input_images = Image.open(uploaded_file)
    if input_images:
        st.success("Valid QR Code")
        image_list = input_images if isinstance(input_images, list) else [input_images]
    
    for i in image_list:
        decoded = decode(i)[0].data.decode("utf-8")
        st.write(i)
        st.text(decoded)
        qr_codes.append(decoded)