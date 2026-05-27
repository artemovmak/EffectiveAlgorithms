"""Render a GIF of the BFS / 0-k BFS / Dijkstra wavefront expanding from the
source on a grid dump.

Each frame shows all vertices whose final distance is <= t, with t walking
from 0 to max(dist) in equal steps. Vertices not yet reached are drawn in
dark grey; reached vertices are coloured by their final distance using the
viridis colormap.

Usage:
    python viz/animate.py results/anim_grid.json --out results/anim.gif
"""

import argparse
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--out", default="results/anim.gif")
    ap.add_argument("--frames", type=int, default=120,
                    help="number of frames to render")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--dpi", type=int, default=110)
    args = ap.parse_args()

    with open(args.dump, "r", encoding="utf-8") as f:
        d = json.load(f)
    if d["graph"] != "grid":
        print("only grid dumps are supported", file=sys.stderr); sys.exit(1)

    rows, cols = d["rows"], d["cols"]
    src = d["source"]
    dist = np.array(d["dist"], dtype=np.float64).reshape(rows, cols)
    dist_valid = dist.copy()
    dist_valid[dist_valid < 0] = np.nan
    dmax = float(np.nanmax(dist_valid))
    if dmax <= 0:
        dmax = 1.0

    # Frame thresholds: 0 .. dmax in N steps (slightly past so the final
    # frame holds the complete picture).
    thresholds = np.linspace(0, dmax * 1.05, args.frames)

    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    fig.patch.set_facecolor("white")
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad(color="#202028")

    # Initial frame: only the source visible.
    frame_arr = np.full((rows, cols), np.nan, dtype=np.float64)
    sr, sc = src // cols, src % cols
    frame_arr[sr, sc] = 0.0
    im = ax.imshow(frame_arr, cmap=cmap, origin="upper",
                   vmin=0, vmax=dmax, interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([])
    ax.scatter([sc], [sr], facecolors="none", edgecolors="white",
               s=90, lw=1.8, zorder=3)
    suptitle = fig.suptitle(f"0--k BFS wavefront  ·  grid {rows}x{cols}, k={d['k']}",
                            fontsize=12, color="#111", y=0.97)
    subtitle = ax.set_title("", fontsize=10, pad=4, color="#333")
    cb = plt.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("distance from source", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.94])

    def update(i):
        t = thresholds[i]
        arr = dist_valid.copy()
        arr[arr > t] = np.nan
        im.set_data(arr)
        reached = int(np.count_nonzero(~np.isnan(arr)))
        total = rows * cols
        pct = 100.0 * reached / total
        subtitle.set_text(
            f"d <= {t:5.1f}    reached {reached:>5} / {total}  ({pct:4.1f}%)"
        )
        return [im, subtitle]

    anim = FuncAnimation(fig, update, frames=len(thresholds),
                         interval=1000.0 / args.fps, blit=False)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    writer = PillowWriter(fps=args.fps)
    anim.save(args.out, writer=writer, dpi=args.dpi)
    print(f"wrote {args.out}  ({os.path.getsize(args.out)//1024} KB)")


if __name__ == "__main__":
    main()
