#!/usr/bin/env python3
from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "fault_code_diffusion_playbook.ipynb"
ORDER = [
    ("00_title.md", "md"),
    ("01_theory.md", "md"),
    ("02_setup.py", "code"),
    ("03_forward_md.md", "md"),
    ("04_forward.py", "code"),
    ("05_train_md.md", "md"),
    ("06_train.py", "code"),
    ("07_sample_md.md", "md"),
    ("08_sample.py", "code"),
    ("09_prod_md.md", "md"),
    ("10_checklist.py", "code"),
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
    print("Wrote", OUT, len(cells))


if __name__ == "__main__":
    main()
