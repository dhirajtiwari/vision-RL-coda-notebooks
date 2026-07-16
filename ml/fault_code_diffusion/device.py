"""CUDA / MPS / CPU — same pattern as vision + RL packages."""

from __future__ import annotations

from ml.fault_code_vision.device import (  # noqa: F401
    assert_cuda_for_client_train,
    device_report,
    pick_device,
)
