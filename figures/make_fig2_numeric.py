"""Figure 2: required figures found by question type, held-out test. Scored by code, no LLM grader.

Numbers: mean of eval.run.score()["numeric"] per arm and type over v2/eval/heldout/results/*.json."""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

FONT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else None
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("fig2_figures_found_by_type.png")

if FONT_DIR:
    for f in FONT_DIR.glob("Inter-*.ttf"):
        font_manager.fontManager.addfont(str(f))
    plt.rcParams["font.family"] = "Inter"

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#8a8984"
GRID = "#e6e5e1"
SERIES = [  # validated categorical slots 1-3 (light)
    ("Test system", "#2a78d6"),
    ("Naive RAG, matched budget", "#eb6834"),
    ("Naive RAG, doubled budget", "#1baf7a"),
]

# (label, test system, naive matched, naive doubled): mean share of required figures found, percent
OVERALL = ("All questions with figures", 94, 43, 60)
ROWS = [
    ("Two companies compared", 100, 14, 14),
    ("A single figure", 100, 14, 57),
    ("Losses and negative figures", 98, 26, 26),
    ("Figures from two statements", 95, 26, 45),
    ("Comparison written in text*", 75, 50, 63),
    ("Segment figures", 81, 43, 86),
    ("This year vs last year", 100, 52, 57),
    ("Calculation plus explanation", 100, 57, 71),
    ("Written text only*", 100, 89, 100),
    ("Multi-step", 86, 86, 100),
]
ROWS.sort(key=lambda r: r[1] - r[2], reverse=True)  # largest gap over the matched baseline first

rows = [OVERALL] + ROWS
BAR_H = 0.22
GAP = 0.03
GROUP = 3 * BAR_H + 2 * GAP
STEP = GROUP + 0.42
DIVIDER_EXTRA = 0.35

fig = plt.figure(figsize=(9, 10.4), dpi=220, facecolor=SURFACE)
ax = fig.add_axes([0.335, 0.075, 0.6, 0.8], facecolor=SURFACE)

y_centers = []
y = 0.0
for i, row in enumerate(rows):
    if i == 1:
        y += DIVIDER_EXTRA
    y_centers.append(y)
    for s, (name, color) in enumerate(SERIES):
        value = row[1 + s]
        top = y - GROUP / 2 + s * (BAR_H + GAP)
        ax.barh(top + BAR_H / 2, value, height=BAR_H, color=color, linewidth=0, zorder=3)
        ax.text(value + 1.2, top + BAR_H / 2, f"{value}%", va="center", ha="left",
                fontsize=8.2, color=TEXT_SECONDARY, zorder=4)
    y += STEP

# divider between the overall row and the per-type rows
div_y = (y_centers[0] + y_centers[1]) / 2
ax.axhline(div_y, xmin=-0.49, xmax=1.0, color="#cfcec9", linewidth=0.9, clip_on=False, zorder=2)

ax.set_ylim(y - STEP + GROUP / 2 + 0.25, -GROUP / 2 - 0.25)
ax.set_xlim(0, 108)
ax.set_yticks(y_centers)
ax.set_yticklabels([r[0] for r in rows], fontsize=10.5, color=TEXT_PRIMARY)
ax.get_yticklabels()[0].set_fontweight(600)
ax.tick_params(axis="y", length=0, pad=10)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9, color=TEXT_MUTED)
ax.tick_params(axis="x", length=0, pad=6)
ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
ax.axvline(0, color="#b9b8b3", linewidth=1, zorder=2)
for spine in ax.spines.values():
    spine.set_visible(False)

fig.text(0.04, 0.955, "Required figures found, by question type", fontsize=17, fontweight=700, color=TEXT_PRIMARY)
fig.text(0.04, 0.928, "Scored by code, with no LLM grader. "
         "Types sorted by the test system's lead over matched naive RAG.",
         fontsize=9.6, color=TEXT_SECONDARY)

handles = [Patch(facecolor=c, edgecolor="none", label=n) for n, c in SERIES]
fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.033, 0.912), ncol=3,
           frameon=False, fontsize=9.6, handlelength=1.0, handleheight=1.0,
           handletextpad=0.5, columnspacing=1.6, labelcolor=TEXT_PRIMARY)

fig.text(0.04, 0.036, "63 held-out questions with required figures, 3 runs each: 21 answers per bar, 189 in the top row. "
         "*12 and 9 answers.",
         fontsize=8.4, color=TEXT_MUTED)
fig.text(0.04, 0.018, "Unanswerable questions have no required figures and are omitted; all three systems declined all of them. "
         "Image by author.", fontsize=8.4, color=TEXT_MUTED)

fig.savefig(OUT, facecolor=SURFACE)
print(OUT)
