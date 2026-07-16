from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure repo root is on path whether kernel cwd is repo root or notebooks/
ROOT = Path(".").resolve()
if not (ROOT / "ml").is_dir():
    if (ROOT.parent / "ml").is_dir():
        ROOT = ROOT.parent
    elif (ROOT / "notebooks").is_dir() is False and (ROOT.parent.parent / "ml").is_dir():
        ROOT = ROOT.parent.parent
sys.path.insert(0, str(ROOT))

import torch
from PIL import Image
import matplotlib.pyplot as plt

from ml.fault_code_vision.device import device_report, pick_device, assert_cuda_for_client_train
from ml.fault_code_vision.catalog import FAULT_CATALOG, N_CLASSES, catalog_codes
from ml.fault_code_vision.pipeline import bootstrap_demo_dataset, mlops_checklist
from ml.fault_code_vision.dataset import load_manifest
from ml.fault_code_vision.cypher_bridge import cypher_for_extracted_code, diagnose_payload_from_ocr
from ml.fault_code_vision.infer import FaultCodeReader, user_message_for_graph_rag

ART = ROOT / "notebooks" / "fault_code_gan_artifacts" / "mlops_playbook"
ART.mkdir(parents=True, exist_ok=True)
CKPT_DIR = ART / "checkpoints"
CKPT_DIR.mkdir(exist_ok=True)

print("REPO ROOT:", ROOT)
print("Artifacts:", ART)
print(f"Catalog size: {N_CLASSES} codes ->", ", ".join(catalog_codes()))
