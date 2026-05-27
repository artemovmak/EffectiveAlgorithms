"""Side-by-side animation: 0-k BFS (left) vs Dijkstra (right) on the same grid.

The two panels fill in sync (same wavefront because the algorithms produce
the same distance field), but the titles display the *actual* wall-clock
times measured on this exact input, so the speed gap is visible at a glance.

Usage:
    python viz/animate_compare.py \\
        results/cmp_bfs0k.json results/cmp_dijkstra.json \\
        --bfs-time 0.004 --dijkstra-time 0.0133 \\
        --out results/report_figs/compare.gif
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


def load_grid(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if d["graph"] != "grid":
        print(f"{path} is not a grid dump", file=sys.stderr); sys.exit(1)
    rows, cols = d["rows"], d["cols"]
    dist = np.array(d["dist"], dtype=np.float64).reshape(rows, cols)
    dist[dist < 0] = np.nan
    return d, dist


def fmt_seconds(s):
    if s >= 1.0:    return f"{s:.3f} s"
    if s >= 1e-3:   return f"{s*1e3:.2f} ms"
    return f"{s*1e6:.1f} us"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bfs_dump")
    ap.add_argument("dijkstra_dump")
    ap.add_argument("--bfs-time",      type=float, required=True,
                    help="measured wall-clock seconds of the 0-k BFS run")
    ap.add_argument("--dijkstra-time", type=float, required=True,
                    help="measured wall-clock seconds of the Dijkstra run")
    ap.add_argument("--out",    default="results/report_figs/compare.gif")
    ap.add_argument("--frames", type=int, default=110)
    ap.add_argument("--fps",    type=int, default=22)
    ap.add_argument("--dpi",    type=int, default=110)
    args = ap.parse_args()

    db, db_dist = load_grid(args.bfs_dump)
    dd, dd_dist = load_grid(args.dijkstra_dump)
    if db["rows"] != dd["rows"] or db["cols"] != dd["cols"]:
        print("dumps must come from the same grid size", file=sys.stderr); sys.exit(1)
    if not np.allclose(np.nan_to_num(db_dist, nan=-1),
                       np.nan_to_num(dd_dist, nan=-1)):
        print("warning: distance fields differ between the two dumps",
              file=sys.stderr)
    rows, cols = db["rows"], db["cols"]
    k = db["k"]
    src = db["source"]
    sr, sc = src // cols, src % cols

    dmax = float(max(np.nanmax(db_dist), np.nanmax(dd_dist)))
    if dmax <= 0:
        dmax = 1.0
    thresholds = np.linspace(0, dmax * 1.05, args.frames)

    speedup = args.dijkstra_time / args.bfs_time

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.0, 5.6))
    fig.patch.set_facecolor("white")
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad(color="#202028")

    def init_panel(ax, dist, label, t_secs):
        arr = np.full((rows, cols), np.nan)
        arr[sr, sc] = 0.0
        im = ax.imshow(arr, cmap=cmap, origin="upper",
                       vmin=0, vmax=dmax, interpolation="nearest")
        ax.set_xticks([]); ax.set_yticks([])
        ax.scatter([sc], [sr], facecolors="none", edgecolors="white",
                   s=90, lw=1.8, zorder=3)
        ax.set_title(f"{label}   ·   {fmt_seconds(t_secs)}",
                     fontsize=12, pad=6, color="#111")
        return im

    imL = init_panel(axL, db_dist, "0-k BFS",  args.bfs_time)
    imR = init_panel(axR, dd_dist, "Dijkstra", args.dijkstra_time)

    fig.suptitle(
        f"Same grid ({rows}x{cols}, k={k})   ·   same answer   ·   "
        f"Dijkstra is {speedup:.2f}x slower",
        fontsize=12.5, color="#111", y=0.97)

    subtitle = fig.text(0.5, 0.04,
                        "", ha="center", va="bottom",
                        fontsize=10, color="#333")
    fig.tight_layout(rect=[0, 0.07, 1, 0.93])

    def update(i):
        t = thresholds[i]
        L = db_dist.copy(); L[L > t] = np.nan
        R = dd_dist.copy(); R[R > t] = np.nan
        imL.set_data(L); imR.set_data(R)
        reached = int(np.count_nonzero(~np.isnan(L)))
        total = rows * cols
        subtitle.set_text(
            f"d <= {t:5.1f}    reached {reached:>5} / {total} "
            f"({100.0*reached/total:4.1f}%)"
        )
        return [imL, imR, subtitle]

    anim = FuncAnimation(fig, update, frames=len(thresholds),
                         interval=1000.0 / args.fps, blit=False)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    anim.save(args.out, writer=PillowWriter(fps=args.fps), dpi=args.dpi)
    print(f"wrote {args.out}  ({os.path.getsize(args.out)//1024} KB)")


if __name__ == "__main__":
    main()
