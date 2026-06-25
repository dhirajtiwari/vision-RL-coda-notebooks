"""Generate Neo4j knowledge graph diagrams for documentation."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def _box(ax, x, y, w, h, text, color, fontsize=8):
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.2,
        edgecolor="#333333",
        facecolor=color,
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, wrap=True)


def _arrow(ax, x1, y1, x2, y2, label="", color="#555555"):
    arr = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.2,
        color=color,
        connectionstyle="arc3,rad=0.12",
    )
    ax.add_patch(arr)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.15, label, ha="center", va="bottom", fontsize=7, color="#1F4E79")


def draw_full_knowledge_graph():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_title(
        "Washing Machine (wm-001) — Full Neo4j Knowledge Graph",
        fontsize=14,
        fontweight="bold",
        color="#1F4E79",
        pad=16,
    )

    _box(ax, 7, 9.0, 4.8, 0.9, "Product: Front Load Washing Machine 8kg\nwm-001 · AquaHome · Laundry", "#D5E8F0", 9)

    symptoms = [
        (2.0, 7.0, "wm-s01\nDoes not spin\n[high]", "#FFF2CC"),
        (5.0, 7.0, "wm-s02\nVibration/noise\n[medium]", "#F2F2F2"),
        (8.0, 7.0, "wm-s03\nWater in drum\n[high]", "#FFF2CC"),
        (11.0, 7.0, "wm-s04\nError E21\n[medium]", "#F2F2F2"),
    ]
    for x, y, t, c in symptoms:
        _box(ax, x, y, 2.3, 1.1, t, c, 8)
        _arrow(ax, 7, 8.55, x, y + 0.55, "HAS_SYMPTOM")

    failures = [
        (3.5, 4.5, "wm-fm01\nWorn Drive Belt\n45 min repair", "#E2F0D9"),
        (7.0, 4.5, "wm-fm02\nFailed Drain Pump\n60 min repair", "#E2F0D9"),
        (10.5, 4.5, "wm-fm03\nLoad Sensor Fault\n90 min repair", "#E2F0D9"),
    ]
    for x, y, t, c in failures:
        _box(ax, x, y, 2.6, 1.2, t, c, 8)
        _arrow(ax, 7, 8.55, x, y + 0.6, "CAN_HAVE", "#888888")

    _arrow(ax, 2.0, 6.45, 3.5, 5.1, "INDICATES\n0.92", "#2E75B6")
    _arrow(ax, 8.0, 6.45, 7.0, 5.1, "INDICATES\n0.88", "#2E75B6")
    _arrow(ax, 5.0, 6.45, 10.5, 5.1, "INDICATES\n0.85", "#2E75B6")
    _arrow(ax, 11.0, 6.45, 7.0, 5.1, "INDICATES\n0.70", "#2E75B6")
    _arrow(ax, 11.0, 6.45, 3.5, 5.1, "INDICATES\n0.55", "#2E75B6")

    steps = [
        (2.5, 1.8, "1. Run empty spin cycle"),
        (5.5, 1.8, "2. Inspect drive belt"),
        (8.5, 1.8, "3. Check drain filter"),
        (11.5, 1.8, "4. Inspect suspension"),
    ]
    for x, y, t in steps:
        _box(ax, x, y, 2.4, 0.8, t, "#EDE7F6", 7)
        _arrow(ax, 7, 8.55, x, y + 0.4, "HAS_DIAGNOSTIC_STEP", "#888888")

    _box(ax, 7, 0.6, 5.5, 0.7, "HistoricalResolution: Replaced drive belt (2025-11-12) → CONFIRMED → wm-fm01", "#FCE4D6", 8)
    _arrow(ax, 3.5, 3.9, 7, 0.95, "CONFIRMED", "#C55A11")

    legend = [
        mpatches.Patch(color="#D5E8F0", label="Product"),
        mpatches.Patch(color="#FFF2CC", label="Symptom (matched in walkthrough)"),
        mpatches.Patch(color="#E2F0D9", label="FailureMode"),
        mpatches.Patch(color="#EDE7F6", label="DiagnosticStep"),
        mpatches.Patch(color="#FCE4D6", label="HistoricalResolution"),
    ]
    ax.legend(handles=legend, loc="lower left", fontsize=8, frameon=True)

    fig.tight_layout()
    fig.savefig(OUT / "wm-001-full-knowledge-graph.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_query_flow():
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_title(
        "Cypher Query Flow — Customer Message to Diagnosis",
        fontsize=14,
        fontweight="bold",
        color="#1F4E79",
        pad=16,
    )

    steps = [
        (6, 9.2, "Customer: \"My washing machine won't spin\nand water stays in the drum\"", "#D5E8F0"),
        (6, 8.0, "Step 1: detect_product\nPython keywords → wm-001", "#FFFFFF"),
        (6, 6.9, "Cypher #1: list_products()\nMATCH (p:Product) RETURN ...", "#E2EFDA"),
        (6, 5.8, "Step 2a: match_symptoms\nCypher #2: HAS_SYMPTOM → Symptom nodes", "#E2EFDA"),
        (6, 4.7, "Python: word overlap\nMatch wm-s01 + wm-s03", "#FFF2CC"),
        (6, 3.6, "Step 2b: rank_failure_modes\nCypher #3: INDICATES confidence sum", "#E2EFDA"),
        (6, 2.5, "Top: Worn Drive Belt (46% confidence)\nEscalate: below 65% threshold", "#FCE4D6"),
        (3, 1.3, "Cypher #4\nDiagnostic Steps", "#EDE7F6"),
        (6, 1.3, "Cypher #5\nPast Resolutions", "#EDE7F6"),
        (9, 1.3, "Python\nEscalation + Format", "#FFFFFF"),
        (6, 0.3, "Human Agent Dashboard\n(case dossier saved)", "#F8CBAD"),
    ]

    sizes = [1.0, 0.8, 0.9, 0.9, 0.8, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8]
    for (x, y, text, color), h in zip(steps, sizes):
        _box(ax, x, y, 5.2, h, text, color, 8)

    for y1, y2 in [(9.2, 8.4), (8.0, 7.25), (6.9, 6.25), (5.8, 5.15), (4.7, 4.05), (3.6, 2.95), (2.5, 1.7)]:
        _arrow(ax, 6, y1 - 0.5, 6, y2 + 0.4, color="#2E75B6")

    _arrow(ax, 6, 2.05, 3, 1.7, color="#666666")
    _arrow(ax, 6, 2.05, 6, 1.7, color="#666666")
    _arrow(ax, 6, 2.05, 9, 1.7, color="#666666")
    _arrow(ax, 6, 0.9, 6, 0.65, color="#C55A11")

    fig.tight_layout()
    fig.savefig(OUT / "cypher-query-flow.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_matched_path():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title(
        "Matched Path for This Message (wm-s01 + wm-s03 highlighted)",
        fontsize=13,
        fontweight="bold",
        color="#1F4E79",
    )

    _box(ax, 6, 6.2, 5.0, 0.8, "wm-001 Front Load Washing Machine", "#D5E8F0", 9)
    _box(ax, 2.5, 4.5, 2.8, 1.0, "wm-s01\nDoes not spin\nMATCHED", "#FFE699")
    _box(ax, 9.5, 4.5, 2.8, 1.0, "wm-s03\nWater in drum\nMATCHED", "#FFE699")
    _box(ax, 2.5, 2.2, 2.8, 1.0, "Worn Drive Belt\nscore 0.92 → 46%", "#C6E0B4")
    _box(ax, 9.5, 2.2, 2.8, 1.0, "Failed Drain Pump\nscore 0.88 → 44%", "#C6E0B4")

    _arrow(ax, 6, 5.8, 2.5, 5.0, "HAS_SYMPTOM", "#333")
    _arrow(ax, 6, 5.8, 9.5, 5.0, "HAS_SYMPTOM", "#333")
    _arrow(ax, 2.5, 4.0, 2.5, 2.7, "INDICATES 0.92", "#2E75B6")
    _arrow(ax, 9.5, 4.0, 9.5, 2.7, "INDICATES 0.88", "#2E75B6")
    _arrow(ax, 6, 5.8, 2.5, 2.7, "CAN_HAVE", "#999")
    _arrow(ax, 6, 5.8, 9.5, 2.7, "CAN_HAVE", "#999")

    _box(ax, 6, 0.7, 8.5, 0.9, "Winner: Worn Drive Belt · Confidence 46% · ESCALATE (below 65% threshold)", "#FCE4D6", 9)

    fig.tight_layout()
    fig.savefig(OUT / "wm-001-matched-path.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    draw_full_knowledge_graph()
    draw_query_flow()
    draw_matched_path()
    print(f"Diagrams saved to {OUT}")