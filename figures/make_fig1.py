"""Figure 1: the test system's pipeline."""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

FONT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else None
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("fig1_pipeline.png")
if FONT_DIR:
    for f in FONT_DIR.glob("Inter-*.ttf"):
        font_manager.fontManager.addfont(str(f))
    plt.rcParams["font.family"] = "Inter"

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#8a8984"
LLM = dict(fc="#eaf2fc", ec="#2a78d6", ls="-")
CODE = dict(fc="#f1f0ec", ec="#6b6a66", ls="-")
INPUT = dict(fc="#ffffff", ec="#b9b8b3", ls="-")
SPLIT = dict(fc="#f1f0ec", ec="#2a78d6", ls=(0, (4, 2.5)))

W, H = 3.3, 2.0
XS = [0.4, 4.5, 8.6, 12.7]
Y_TOP, Y_BOT = 5.0, 1.9

BOXES = {
    "q": (XS[0], Y_TOP, INPUT, "Question", "in plain English"),
    "plan": (XS[1], Y_TOP, LLM, "1. Plan", "which figures to fetch,\nwhat to compute,\nwhat text to search"),
    "check": (XS[2], Y_TOP, CODE, "2. Check the plan", "companies, years and\nsegments must exist"),
    "look": (XS[3], Y_TOP, SPLIT, "3a. Look up figures", "code fetches candidates,\nmodel picks one,\ncode returns the value"),
    "search": (XS[3], Y_BOT, CODE, "3b. Search the text", "keyword and vector\nsearch, per company,\nwhole paragraphs"),
    "compute": (XS[2], Y_BOT, CODE, "4. Compute", "arithmetic and\ncomparisons in Python,\nwith citations"),
    "write": (XS[1], Y_BOT, LLM, "5. Write up", "summarise the workings,\nexplain from the text"),
    "verify": (XS[0], Y_BOT, CODE, "6. Verify", "check numeric\nconsistency; fall back to\nworkings if rejected"),
}

fig = plt.figure(figsize=(12, 6.3), dpi=220, facecolor=SURFACE)
ax = fig.add_axes([0, 0, 1, 1], facecolor=SURFACE)
ax.set_xlim(0, 16.4)
ax.set_ylim(0, 8.6)
ax.axis("off")


def box(x, y, style, w=W, h=H):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.18",
                                fc=style["fc"], ec=style["ec"], lw=1.6, ls=style["ls"], zorder=2))


for key, (x, y, style, title, body) in BOXES.items():
    box(x, y, style)
    ax.text(x + W / 2, y + H - 0.42, title, ha="center", va="center", fontsize=12.5,
            fontweight=700, color=TEXT_PRIMARY, zorder=3)
    ax.text(x + W / 2, y + H / 2 - 0.3, body, ha="center", va="center", fontsize=10,
            color=TEXT_SECONDARY, linespacing=1.45, zorder=3)


def arrow(p, q, **kw):
    style = dict(arrowstyle="-|>", mutation_scale=13, color="#52514e", lw=1.4,
                 shrinkA=0, shrinkB=0, zorder=1)
    style.update(kw)
    ax.add_patch(FancyArrowPatch(p, q, **style))


G = 0.12
for a, b in [("q", "plan"), ("plan", "check"), ("check", "look")]:
    xa, ya = BOXES[a][0] + W, BOXES[a][1] + H / 2
    arrow((xa + G, ya), (BOXES[b][0] - G, ya))
arrow((XS[3] + W / 2, Y_TOP - G), (XS[3] + W / 2, Y_BOT + H + G))
for a, b in [("search", "compute"), ("compute", "write"), ("write", "verify")]:
    ya = BOXES[a][1] + H / 2
    arrow((BOXES[a][0] - G, ya), (BOXES[b][0] + W + G, ya))

# retry loop: check -> plan, above the row
arrow((XS[2] + W / 2, Y_TOP + H + G), (XS[1] + W / 2, Y_TOP + H + G),
      connectionstyle="arc3,rad=0.35", color="#8a8984", lw=1.2, ls=(0, (4, 3)))
ax.text((XS[1] + XS[2] + W) / 2, Y_TOP + H + 1.05, "invalid: retry once with the error",
        ha="center", va="center", fontsize=9.5, color=TEXT_MUTED)

# legend
LEG_Y = 0.55
items = [(LLM, "Language model: judgement"), (CODE, "Deterministic code"),
         (SPLIT, "Split step: model picks from a closed list")]
x = 0.4
for style, label in items:
    box(x, LEG_Y - 0.2, style, w=0.5, h=0.4)
    t = ax.text(x + 0.7, LEG_Y, label, va="center", fontsize=10.5, color=TEXT_PRIMARY)
    fig.canvas.draw()
    bb = t.get_window_extent().transformed(ax.transData.inverted())
    x = bb.x1 + 0.6

fig.savefig(OUT, facecolor=SURFACE)
print(OUT)
