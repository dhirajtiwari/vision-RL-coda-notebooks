"""How diffusion fits the fault-code data factory + upgrade path notes."""

from __future__ import annotations

from typing import Any


def diffusion_vs_gan() -> list[dict[str, str]]:
    return [
        {
            "aspect": "Training stability",
            "gan": "Adversarial min-max; mode collapse risk",
            "diffusion": "Simple denoising MSE; stable",
        },
        {
            "aspect": "Sample quality (glyphs)",
            "gan": "OK at 64px with long train",
            "diffusion": "Usually sharper / more diverse",
        },
        {
            "aspect": "Speed (inference)",
            "gan": "1 forward pass",
            "diffusion": "Many steps (use DDIM / latent for speed)",
        },
        {
            "aspect": "Client GPU",
            "gan": "Useful",
            "diffusion": "Strongly recommended for train + sample",
        },
        {
            "aspect": "Our product role",
            "gan": "Offline synthetic corpus (lab)",
            "diffusion": "Same — better OCR train data factory",
        },
    ]


def modern_stack_notes() -> dict[str, Any]:
    return {
        "this_notebook": "From-scratch class-conditional DDPM (Ho 2020) on 64×64 LCD seeds",
        "production_upgrade": [
            "Hugging Face Diffusers UNet2DConditionModel + DDPMScheduler",
            "Latent Diffusion / SD-Turbo / SDXL-Lightning for photo realism + ControlNet edges",
            "DDIM / DPM-Solver++ for 10–50 step sampling",
            "Classifier-free guidance for stronger class conditioning",
        ],
        "not_on_hot_path": "Diffusion generates training/test images offline; diagnose still GraphRAG",
        "cuda": "docker/Dockerfile.ml + --require-cuda for client trains",
    }
