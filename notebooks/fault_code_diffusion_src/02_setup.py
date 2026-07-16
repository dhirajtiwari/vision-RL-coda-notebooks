from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image
import torch
from torchvision import transforms
from torchvision.utils import make_grid

ROOT = Path(".").resolve()
if not (ROOT / "ml").is_dir() and (ROOT.parent / "ml").is_dir():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))


from ml.fault_code_diffusion.device import device_report, pick_device
from ml.fault_code_diffusion.pipeline import diffusion_vs_gan, modern_stack_notes
from ml.fault_code_diffusion.ddpm import DDPMConfig, train_ddpm, generate_codes, p_sample_loop
from ml.fault_code_diffusion.schedule import DiffusionSchedule
from ml.fault_code_vision.pipeline import bootstrap_demo_dataset
from ml.fault_code_vision.catalog import FAULT_CATALOG, N_CLASSES, IDX_TO_CODE

ART = ROOT / "notebooks" / "fault_code_diffusion_artifacts"
ART.mkdir(parents=True, exist_ok=True)

print("device_report:", json.dumps(device_report(), indent=2))
print("device:", pick_device())
print("classes:", N_CLASSES, list(IDX_TO_CODE.values())[:8], "...")

import pandas as pd
print(pd.DataFrame(diffusion_vs_gan()).to_string(index=False))
print("\nUpgrade notes:")
print(json.dumps(modern_stack_notes(), indent=2))
