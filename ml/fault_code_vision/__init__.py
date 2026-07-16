"""Fault-code vision: synthetic generation support, OCR train/infer, GraphRAG bridge.

Production diagnose remains GraphRAG (Neo4j). This package is the vision
ingress + offline training factory. See notebooks/fault_code_vision_mlops_playbook.ipynb.
"""

from ml.fault_code_vision.catalog import CODE_TO_IDX, FAULT_CATALOG, IDX_TO_CODE, N_CLASSES
from ml.fault_code_vision.device import device_report, pick_device

__all__ = [
    "FAULT_CATALOG",
    "CODE_TO_IDX",
    "IDX_TO_CODE",
    "N_CLASSES",
    "pick_device",
    "device_report",
]
