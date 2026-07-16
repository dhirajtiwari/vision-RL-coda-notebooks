# GPU training image for fault-code vision (GAN/OCR) + diagnostic RL (DQN).
# Build (with NVIDIA Container Toolkit on the host):
#   docker build -f docker/Dockerfile.ml -t warrantygraph-ml:latest .
# Run vision:
#   docker run --gpus all -v "$PWD":/workspace -w /workspace warrantygraph-ml:latest \
#     python -m ml.fault_code_vision.train_ocr --manifest ... --require-cuda
# Run RL DQN:
#   docker run --gpus all -v "$PWD":/workspace -w /workspace warrantygraph-ml:latest \
#     python -m ml.fault_code_rl.train --algo dqn --episodes 800 --require-cuda
#
# Bandits / tabular Q-learning do not need GPU (CPU fine).
# Base image provides CUDA + cuDNN. Adjust tag to match your cluster CUDA version.

FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

WORKDIR /workspace

# System deps for optional tesseract / fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ml.txt /tmp/requirements-ml.txt
# Torch already in base image; install remaining ML extras if needed
RUN pip install --no-cache-dir Pillow matplotlib tqdm PyYAML

COPY ml/ /workspace/ml/
COPY models/ /workspace/models/
COPY evals/vision/ /workspace/evals/vision/
COPY evals/rl/ /workspace/evals/rl/

ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES=all

CMD ["python", "-c", "import torch; print('cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'n/a')"]
