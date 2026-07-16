from __future__ import annotations

import os
import random
import re
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from torchvision.utils import make_grid, save_image

# Reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


DEVICE = pick_device()
print(f"torch {torch.__version__} | device = {DEVICE}")

ROOT = Path(".").resolve()
# Notebook may be launched from repo root or notebooks/
if (ROOT / "notebooks").is_dir() and not (ROOT / "fault_code_gan_artifacts").is_dir():
    ART = ROOT / "notebooks" / "fault_code_gan_artifacts"
elif (ROOT / "fault_code_gan_artifacts").is_dir() or ROOT.name == "notebooks":
    ART = ROOT / "fault_code_gan_artifacts"
else:
    ART = ROOT / "notebooks" / "fault_code_gan_artifacts"
ART.mkdir(parents=True, exist_ok=True)
(SEED_DIR := ART / "seed_lcd").mkdir(exist_ok=True)
(AUG_DIR := ART / "augmented").mkdir(exist_ok=True)
(GEN_DIR := ART / "generated").mkdir(exist_ok=True)
(CKPT_DIR := ART / "checkpoints").mkdir(exist_ok=True)
print(f"Artifacts -> {ART}")
