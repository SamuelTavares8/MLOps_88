from locust import HttpUser, task, between
import os

IMAGE_PATH = "/Users/rita/Documents/MLOPs/MLOps_88/data/processed/test/COVID19/COVID19(562).jpg"

class MyUser(HttpUser):
    """
    Locust user that simulates concurrent users
    sending X-ray images to the inference API.
    """

    wait_time = between(1, 2)

    def on_start(self) -> None:
        """
        Load the X-ray image once per user.
        This avoids disk I/O during the test.
        """
        image_path = IMAGE_PATH

        with open(image_path, "rb") as f:
            self.image_data = f.read()

    @task(3)
    def predict_densenet(self) -> None:
       """
       Task using DenseNet121 model.
       Weight = 3 (more frequent).
       """
       self.client.post(
           "/predict?model_name=densenet121",
           files={"file": ("xray.jpg", self.image_data, "image/jpeg")},
       )

    @task(1)
    def predict_efficientnet(self) -> None:
        """
        Task using EfficientNet-B0 model.
        Weight = 1 (less frequent).
        """
        self.client.post(
            "/predict?model_name=efficientnet-b0",
            files={"file": ("xray.jpg", self.image_data, "image/jpeg")},
        )

