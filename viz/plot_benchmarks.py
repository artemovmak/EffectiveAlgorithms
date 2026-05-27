"""Aggregate JSONL benchmark results (one JSON object per line) into plots.

Produces:
  - time_vs_V.png  : runtime vs V for each (graph, algo) pair, grouped by k
  - time_vs_k.png  : runtime vs k for a fixed (graph, V), grouped by algo

Usage:
    python viz/plot_benchmarks.py results/all.jsonl --outdir results/figs
"""

import argparse
import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def plot_time_vs_V(rows, outdir):
    by = defaultdict(list)
    for r in rows:
        by[(r["graph"], r["algorithm"], r["k"])].append((r["V"], r["seconds"]))
    if not by:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    for (graph, algo, k), pts in sorted(by.items()):
        pts.sort()
        Vs = [p[0] for p in pts]
        ts = [p[1] for p in pts]
        ax.plot(Vs, ts, marker="o", label=f"{graph}/{algo}/k={k}")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("V"); ax.set_ylabel("seconds")
    ax.set_title("Runtime vs V")
    ax.grid(True, which="both", lw=0.3)
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    out = os.path.join(outdir, "time_vs_V.png")
    fig.savefig(out, dpi=140)
    print("wrote", out)


def plot_time_vs_k(rows, outdir):
    by = defaultdict(list)
    for r in rows:
        by[(r["graph"], r["algorithm"], r["V"])].append((r["k"], r["seconds"]))
    if not by:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    for (graph, algo, V), pts in sorted(by.items()):
        pts.sort()
        ks = [p[0] for p in pts]
        ts = [p[1] for p in pts]
        ax.plot(ks, ts, marker="o", label=f"{graph}/{algo}/V={V}")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("k"); ax.set_ylabel("seconds")
    ax.set_title("Runtime vs k")
    ax.grid(True, which="both", lw=0.3)
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    out = os.path.join(outdir, "time_vs_k.png")
    fig.savefig(out, dpi=140)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--outdir", default="results/figs")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    rows = load(args.jsonl)
    plot_time_vs_V(rows, args.outdir)
    plot_time_vs_k(rows, args.outdir)


if __name__ == "__main__":
    main()
