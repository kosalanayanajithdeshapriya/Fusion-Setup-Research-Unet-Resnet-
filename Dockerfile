# Tomato growth-stage fusion demo — CPU-only inference image for Cloud Run.
# The 5.7GB training dataset and training-only scripts are deliberately not
# copied in; only what app/inference.py actually needs at runtime is.
FROM python:3.10-slim

WORKDIR /app

# opencv (used by inputs/unet_lpf_extractor.py) needs libgl/libglib at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU-only torch/torchvision build first (Cloud Run has no GPU) — avoids
# pulling multi-GB CUDA wheels. requirements.txt's pinned versions then
# install as normal, but pip sees torch/torchvision already satisfied.
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
        torch==2.6.0 torchvision==0.21.0 \
    && pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY inputs/*.py inputs/*.json inputs/*.pth inputs/
COPY scripts/model_common.py scripts/model_common.py
COPY checkpoints/ checkpoints/
COPY results/tables/comparison_summary.csv results/tables/comparison_summary.csv
COPY .streamlit/ .streamlit/

EXPOSE 8080

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
