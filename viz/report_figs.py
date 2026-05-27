"""Generate report-quality figures from the JSONL sweep + scale logs.

Outputs to results/report_figs/:
    speedup_vs_V.png   -- grid, k=4 and k=1, speedup of bfs/dijkstra
    speedup_vs_k.png   -- grid V=1e6, speedup vs k
    grid_scaling.png   -- absolute runtime vs V for grid k=4, log-log
"""

import argparse
import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if "error" in r:
                continue
            out.append(r)
    return out


def load_scale_log(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("{"):
                out.append(json.loads(line))
    return out


def collect(args):
    rows = load_jsonl(args.sweep)
    for p in args.scale_logs:
        rows.extend(load_scale_log(p))
    return rows


def plot_grid_scaling(rows, outdir):
    # grid + dijkstra & bfs_0k for k=4 (the headline series) and bfs_01 for k=1
    series = defaultdict(list)
    for r in rows:
        if r["graph"] != "grid":
            continue
        algo = r["algorithm"]
        if algo == "dijkstra_pq":
            # Dijkstra carries k=0 in its JSON; the run's true k is recoverable
            # only by joining on relaxations/source -- but for grids we ran
            # k=1 and k=4 separately. Tag by E since E is fixed per V.
            series[("Dijkstra", "any-k")].append((r["V"], r["seconds"]))
        elif algo == "bfs_0k":
            tag = f"0-k BFS (k={r['k']})"
            series[(tag, r["k"])].append((r["V"], r["seconds"]))
        elif algo == "bfs_01":
            series[("0-1 BFS (k=1)", 1)].append((r["V"], r["seconds"]))

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    markers = {"Dijkstra": "o", "0-k BFS (k=1)": "s", "0-k BFS (k=4)": "^",
               "0-k BFS (k=16)": "D", "0-1 BFS (k=1)": "v"}
    for (label, _), pts in sorted(series.items()):
        pts.sort()
        Vs = [p[0] for p in pts]; ts = [p[1] for p in pts]
        ax.plot(Vs, ts, marker=markers.get(label, "x"), label=label, lw=1.6)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("V (vertices)")
    ax.set_ylabel("wall time (s)")
    ax.set_title("Grid (4-connected, implicit), single thread")
    ax.grid(True, which="both", lw=0.3, alpha=0.5)
    ax.legend(fontsize=9, loc="best")
    fig.tight_layout()
    out = os.path.join(outdir, "grid_scaling.png")
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print("wrote", out)


def plot_speedup_vs_V(rows, outdir):
    # For each V, compute speedup = dijkstra/bfs at the same V (k matched).
    by_V_k = defaultdict(dict)  # (V, k) -> {algo: seconds}
    for r in rows:
        if r["graph"] != "grid":
            continue
        if r["algorithm"] == "dijkstra_pq":
            # We don't know dijkstra's true k -- but its time depends weakly on
            # k for grids (same structural V/E). We approximate by using
            # the smallest dijkstra time at that V as 'k=any'.
            d_k = 0
        else:
            d_k = r["k"]
        by_V_k[(r["V"], r["algorithm"], d_k)].setdefault("seconds", []).append(r["seconds"])

    # Group dijkstra (representative) per V.
    dijk_t = {}
    for (V, algo, k), d in by_V_k.items():
        if algo == "dijkstra_pq":
            dijk_t.setdefault(V, []).append(min(d["seconds"]))
    dijk_t = {V: min(ts) for V, ts in dijk_t.items()}

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    for tag, predicate in [
        ("0-1 BFS (k=1)",  lambda a, k: a == "bfs_01"),
        ("0-k BFS (k=1)",  lambda a, k: a == "bfs_0k" and k == 1),
        ("0-k BFS (k=4)",  lambda a, k: a == "bfs_0k" and k == 4),
        ("0-k BFS (k=16)", lambda a, k: a == "bfs_0k" and k == 16),
    ]:
        pts = []
        for (V, algo, k), d in by_V_k.items():
            if predicate(algo, k) and V in dijk_t:
                pts.append((V, dijk_t[V] / min(d["seconds"])))
        pts.sort()
        if pts:
            ax.plot([p[0] for p in pts], [p[1] for p in pts],
                    marker="o", label=tag, lw=1.6)
    ax.set_xscale("log")
    ax.axhline(1.0, color="gray", lw=0.7, ls="--")
    ax.set_xlabel("V (vertices)")
    ax.set_ylabel("speed-up over Dijkstra (×)")
    ax.set_title("Grid: BFS-family speed-up over Dijkstra baseline")
    ax.grid(True, which="both", lw=0.3, alpha=0.5)
    ax.legend(fontsize=9, loc="best")
    fig.tight_layout()
    out = os.path.join(outdir, "speedup_vs_V.png")
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", default="results/sweep.jsonl")
    ap.add_argument("--scale-logs", nargs="*", default=[
        "results/scale_5e8.log",
        "results/scale_9e8_bfs01.log",
        "results/scale_9e8_dijkstra.log",
    ])
    ap.add_argument("--outdir", default="results/report_figs")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    rows = collect(args)
    plot_grid_scaling(rows, args.outdir)
    plot_speedup_vs_V(rows, args.outdir)


if __name__ == "__main__":
    main()
