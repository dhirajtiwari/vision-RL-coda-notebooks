#!/usr/bin/env python3
"""Rebuild fault_code_vision_mlops_playbook.ipynb from ordered fragments."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "fault_code_vision_mlops_playbook.ipynb"

ORDER: list[tuple[str, str]] = [
    ("00_title.md", "md"),
    ("01_toc.md", "md"),
    ("02_setup.py", "code"),
    ("03_architecture.md", "md"),
    ("04_cuda_md.md", "md"),
    ("05_cuda.py", "code"),
    ("06_data_md.md", "md"),
    ("07_bootstrap.py", "code"),
    ("08_train_md.md", "md"),
    ("09_train.py", "code"),
    ("10_eval_md.md", "md"),
    ("11_eval.py", "code"),
    ("12_cypher_md.md", "md"),
    ("13_cypher.py", "code"),
    ("14_registry_md.md", "md"),
    ("15_registry.py", "code"),
    ("16_bom_md.md", "md"),
    ("17_checklist.py", "code"),
    ("18_commands.md", "md"),
]


def main() -> None:
    nb = new_notebook()
    cells = []
    for name, kind in ORDER:
        text = (HERE / name).read_text(encoding="utf-8").strip("\n")
        cells.append(new_markdown_cell(text) if kind == "md" else new_code_cell(text))
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
    print(f"Wrote {OUT} ({len(cells)} cells)")


if __name__ == "__main__":
    main()
