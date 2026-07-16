"""CUDA / MPS / CPU device selection and environment report."""

from __future__ import annotations

from typing import Any

import torch


def pick_device() -> torch.device:
    """Prefer CUDA (client train target), then Apple MPS, then CPU."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def device_report() -> dict[str, Any]:
    """Human-readable / JSON-serializable environment facts for MLOps logs."""
    report: dict[str, Any] = {
        "torch_version": torch.__version__,
        "cuda_compiled": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_selected": str(pick_device()),
    }
    if torch.cuda.is_available():
        idx = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(idx)
        report.update(
            {
                "cuda_device_count": torch.cuda.device_count(),
                "cuda_device_name": torch.cuda.get_device_name(idx),
                "cuda_total_memory_gb": round(props.total_memory / (1024**3), 2),
                "cudnn_enabled": torch.backends.cudnn.enabled,
            }
        )
    mps = getattr(torch.backends, "mps", None)
    report["mps_available"] = bool(mps and mps.is_available())
    return report


def assert_cuda_for_client_train(*, allow_cpu_fallback: bool = True) -> torch.device:
    """
    Client train jobs should prefer CUDA. Local demos may fall back to MPS/CPU.

    Set allow_cpu_fallback=False in GPU CI / production train entrypoints.
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    if not allow_cpu_fallback:
        raise RuntimeError(
            "CUDA required for this train job but torch.cuda.is_available() is False. "
            "Install NVIDIA drivers + CUDA toolkit + matching PyTorch GPU wheels."
        )
    return pick_device()
