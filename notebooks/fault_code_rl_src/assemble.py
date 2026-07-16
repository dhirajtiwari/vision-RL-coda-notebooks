#!/usr/bin/env python3
from pathlib import Path
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "fault_code_rl_playbook.ipynb"
ORDER = [
    ("00_title.md", "md"), ("01_which_rl.md", "md"), ("02_setup.py", "code"),
    ("03_math_mdp.md", "md"), ("04_math_bandit.md", "md"), ("05_sim_md.md", "md"),
    ("06_sim.py", "code"), ("07_bandit_md.md", "md"), ("08_bandit.py", "code"),
    ("09_q_md.md", "md"), ("10_q.py", "code"), ("11_dqn_md.md", "md"),
    ("12_dqn.py", "code"), ("13_offline_md.md", "md"), ("14_offline.py", "code"),
    ("15_eval_md.md", "md"), ("16_eval.py", "code"), ("17_mlops_md.md", "md"),
    ("18_checklist.py", "code"), ("19_refs.md", "md"),
]

def main():
    nb = new_notebook()
    cells = []
    for name, kind in ORDER:
        text = (HERE / name).read_text(encoding="utf-8").strip("\n")
        cells.append(new_markdown_cell(text) if kind == "md" else new_code_cell(text))
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    nbf.write(nb, OUT)
    print("Wrote", OUT, len(cells))

if __name__ == "__main__":
    main()
