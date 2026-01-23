from fastapi.testclient import TestClient
from xray_image_classifier.api import app
client = TestClient(app)

#Simple test to check if the API is running

IMAGE_PATH = "/Users/rita/Documents/MLOPs/MLOps_88/data/processed/test/COVID19/COVID19(562).jpg"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_default_model():
    with open(IMAGE_PATH, "rb") as f:
        response = client.post(
            "/predict",
            files={"file": ("xray.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200

    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "probabilities" in data
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_with_model_selection():
    with open(IMAGE_PATH, "rb") as f:
        response = client.post(
            "/predict?model_name=efficientnet-b0",
            files={"file": ("xray.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 200


