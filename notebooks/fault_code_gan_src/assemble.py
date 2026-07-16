#!/usr/bin/env python3
"""Assemble fault_code_gan_synthetic_images.ipynb from ordered source fragments."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "fault_code_gan_synthetic_images.ipynb"

# Ordered cells: (filename, type) where type is md|code
ORDER: list[tuple[str, str]] = [
    ("00_title.md", "md"),
    ("01_setup_md.md", "md"),
    ("02_setup.py", "code"),
    ("03_catalog_md.md", "md"),
    ("04_catalog.py", "code"),
    ("05_theory.md", "md"),
    ("06_seed_md.md", "md"),
    ("07_seed_render.py", "code"),
    ("08_seed_corpus.py", "code"),
    ("09_aug_md.md", "md"),
    ("10_aug.py", "code"),
    ("11_dataset.py", "code"),
    ("12_dcgan_md.md", "md"),
    ("13_dcgan_models.py", "code"),
    ("14_dcgan_train.py", "code"),
    ("15_dcgan_plot.py", "code"),
    ("16_cgan_md.md", "md"),
    ("17_cgan_models.py", "code"),
    ("18_cgan_train.py", "code"),
    ("19_cgan_plot.py", "code"),
    ("20_corpus_md.md", "md"),
    ("21_corpus.py", "code"),
    ("22_ocr_md.md", "md"),
    ("23_ocr.py", "code"),
    ("24_cypher_md.md", "md"),
    ("25_cypher.py", "code"),
    ("26_live_neo4j.py", "code"),
    ("27_integration.md", "md"),
    ("28_refs.md", "md"),
]


def main() -> None:
    nb = new_notebook()
    cells = []
    for name, kind in ORDER:
        text = (HERE / name).read_text(encoding="utf-8").strip("\n")
        if kind == "md":
            cells.append(new_markdown_cell(text))
        else:
            cells.append(new_code_cell(text))
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    nbf.write(nb, OUT)
    n_code = sum(1 for _, k in ORDER if k == "code")
    n_md = sum(1 for _, k in ORDER if k == "md")
    print(f"Wrote {OUT}")
    print(f"  {len(ORDER)} cells ({n_md} markdown, {n_code} code)")


if __name__ == "__main__":
    main()
