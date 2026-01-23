import streamlit as st
import requests
from PIL import Image


# Configuration
API_URL = "http://127.0.0.1:8000/predict"

st.set_page_config(
    page_title="Chest X-ray Classifier",
    layout="centered",
)

st.title("Chest X-ray Classifier")
st.write("Upload a chest X-ray image and run inference using the trained model.")


# Model selection
model_name = st.selectbox(
    "Select model",
    options=["densenet121", "efficientnet-b0"],
)


# File uploader
uploaded_file = st.file_uploader(
    "Upload an X-ray image",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    # Display image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded X-ray")


    # Predict button
    if st.button("Run inference"):
        with st.spinner("Sending image to backend..."):
            try:
                # Prepare multipart form data
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type,
                    )
                }

                params = {"model_name": model_name}

                response = requests.post(
                    API_URL,
                    files=files,
                    params=params,
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()

                    st.success("Inference completed!")

                    st.subheader("Prediction")
                    st.write(f"**Class:** {result['prediction']}")
                    st.write(f"**Confidence:** {result['confidence']:.2f}")

                    st.subheader("Class probabilities")
                    st.json(result["probabilities"])

                else:
                    st.error(
                        f"Backend error ({response.status_code}): {response.text}"
                    )

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to backend: {e}")