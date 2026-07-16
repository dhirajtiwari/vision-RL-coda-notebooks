"""CUDA / MPS / CPU helpers — shared pattern with vision package."""

from __future__ import annotations

# Reuse vision device stack so client CUDA story is identical across ML workstreams.
from ml.fault_code_vision.device import (  # noqa: F401
    assert_cuda_for_client_train,
    device_report,
    pick_device,
)
