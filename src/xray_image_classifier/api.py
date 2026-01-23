from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Response
from PIL import Image
import io
import torch
from torchvision import transforms
from prometheus_client import Counter, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST
import time


# =========================
# IMPORT MODEL
# =========================
from xray_image_classifier import model
from xray_image_classifier.model import XRayClassifier 

# =========================
# CONFIG
# =========================
NUM_CLASSES = 4
IMAGE_SIZE = 224

CLASS_NAMES = [
    "pneumonia",
    "covid",
    "normal",
    "tuberculosis",
]

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =========================
# LOAD MODEL
# =========================
MODELS = {
    "densenet121": XRayClassifier(
        num_classes=4,
        in_channels=3,
        backbone="densenet121",
        pretrained=False,
    ),
    "efficientnet-b0": XRayClassifier(
        num_classes=4,
        in_channels=3,
        backbone="efficientnet-b0",
        pretrained=False,
    ),
}

MODELS["densenet121"].load_state_dict(
    torch.load("models/xray_classifier_densenet121_finetuned.pth", map_location=DEVICE)
)
MODELS["efficientnet-b0"].load_state_dict(
    torch.load("models/xray_classifier_efficientnet-b0_finetuned.pth", map_location=DEVICE)
)

for m in MODELS.values():
    m.to(DEVICE)
    m.eval()


# =========================
# TRANSFORMS 
# =========================
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])

# -----------------------------
# Prometheus metrics
# -----------------------------

REQUEST_COUNT = Counter(
    "xray_api_requests_total",
    "Total number of inference requests received",
)

INFERENCE_LATENCY = Histogram(
    "xray_inference_latency_seconds",
    "Time spent running model inference",
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10),
)

INPUT_SIZE_BYTES = Summary(
    "xray_input_size_bytes",
    "Size of uploaded X-ray images in bytes",
)

# =========================
# FASTAPI APP
# =========================
app = FastAPI(
    title="Chest X-ray Classifier",
    version="1.0",
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    model_name: str = Query(
        "densenet121",
        description="Model to use for inference",
        enum=["densenet121", "efficientnet-b0"],
    ),
):
    if model_name not in MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{model_name}'",
        )

    # Request count
    REQUEST_COUNT.inc()

    # Read file
    image_bytes = await file.read()

    # Metrics: input size
    INPUT_SIZE_BYTES.observe(len(image_bytes))

    # Decode image
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )

    # Preprocess
    x = transform(image).unsqueeze(0).to(DEVICE)

    selected_model = MODELS[model_name]

    # Inference + latency metric
    start_time = time.time()

    with torch.no_grad():
        logits = selected_model(x)
        probs = torch.softmax(logits, dim=1)

    INFERENCE_LATENCY.observe(time.time() - start_time)

    # Post-processing
    conf, idx = torch.max(probs, dim=1)

    return {
        "prediction": CLASS_NAMES[idx.item()],
        "confidence": float(conf.item()),
        "probabilities": {
            CLASS_NAMES[i]: float(probs[0, i])
            for i in range(NUM_CLASSES)
        },
    }

@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )