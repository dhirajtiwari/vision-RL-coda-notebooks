"""Conditional diffusion for synthetic fault-code display images.

Upgrade path over DCGAN/cGAN for higher-fidelity claim-photo corpora.
Theory + client showcase: notebooks/fault_code_diffusion_playbook.ipynb
"""

from ml.fault_code_diffusion.device import device_report, pick_device

__all__ = ["device_report", "pick_device"]
