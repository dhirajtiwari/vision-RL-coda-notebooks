## Part 2 — CUDA / device readiness

Client “we need CUDA” means a **training environment**, not GPUs on every diagnose pod.

| Claim | Proof |
|-------|--------|
| CUDA ready | `nvidia-smi` green + `torch.cuda.is_available()==True` |
| Image ready | `docker/Dockerfile.ml` builds; `docker run --gpus all ...` |
| Train job | `python -m ml.fault_code_vision.train_ocr --require-cuda ...` |

Local Mac demos may use **MPS**; official client train target is **NVIDIA CUDA**.
