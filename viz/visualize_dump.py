"""Visualize a JSON dump produced by zkbfs_dump.

For grid graphs: draws a heatmap of distances.
For general graphs: draws a node-link diagram with distance colouring.

Usage:
    python viz/visualize_dump.py path/to/dump.json [--out fig.png]
"""

import argparse
import json
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_grid(d, ax):
    rows, cols = d["rows"], d["cols"]
    arr = np.array(d["dist"], dtype=np.float64).reshape(rows, cols)
    arr[arr < 0] = np.nan
    im = ax.imshow(arr, cmap="viridis", origin="upper")
    ax.set_title(
        f'{d["graph"]} {rows}x{cols}  k={d["k"]}  '
        f'src={d["source"]}  algo={d["algorithm"]}  '
        f't={d["seconds"]*1000:.1f} ms'
    )
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, shrink=0.8, label="distance")


def plot_general(d, ax):
    V = d["V"]
    edges = d["edges"]
    dist = np.array(d["dist"], dtype=np.float64)
    dist[dist < 0] = np.nan

    # Layout: if 'layered' use layered grid layout, else circular.
    if d["graph"] == "layered":
        # Heuristic: width = sqrt(V), layers = V/width
        L = int(math.sqrt(V))
        W = max(1, V // L)
        xs = np.array([i % W for i in range(V)], dtype=np.float64)
        ys = np.array([-(i // W) for i in range(V)], dtype=np.float64)
    else:
        theta = np.linspace(0, 2 * np.pi, V, endpoint=False)
        xs = np.cos(theta); ys = np.sin(theta)

    # Edges (skip drawing very dense graphs)
    if len(edges) <= 4000:
        for (u, v, w) in edges:
            ax.plot([xs[u], xs[v]], [ys[u], ys[v]],
                    color="#bbbbbb", lw=0.4 if w == 0 else 0.8, zorder=1)
    finite = ~np.isnan(dist)
    sc = ax.scatter(xs[finite], ys[finite], c=dist[finite],
                    cmap="viridis", s=18, zorder=2)
    if (~finite).any():
        ax.scatter(xs[~finite], ys[~finite], c="lightgray", s=12, zorder=2)
    ax.set_title(
        f'{d["graph"]}  V={V}  k={d["k"]}  '
        f'src={d["source"]}  algo={d["algorithm"]}  '
        f't={d["seconds"]*1000:.1f} ms'
    )
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(sc, ax=ax, shrink=0.8, label="distance")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    with open(args.dump, "r", encoding="utf-8") as f:
        d = json.load(f)

    fig, ax = plt.subplots(figsize=(7, 6))
    if d["graph"] == "grid":
        plot_grid(d, ax)
    else:
        plot_general(d, ax)

    out = args.out or os.path.splitext(args.dump)[0] + ".png"
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
