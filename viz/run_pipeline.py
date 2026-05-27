"""Pipeline: run zkbfs_bench across a grid of (graph, V, k, algo) configurations
and write results as JSONL.

Usage:
    python viz/run_pipeline.py --bench build/zkbfs_bench --out results/all.jsonl
"""

import argparse
import json
import os
import subprocess
import sys
from itertools import product


def cfg_grid():
    # (graph, params dict, algos, ks, sizes)
    configs = []

    # ---- Grid: scales to V=10^9 (implicit graph, only distance array in memory)
    grid_sizes = [
        (1000, 1000),     # 1e6
        (3162, 3162),     # 1e7
        (10000, 10000),   # 1e8  -- needs ~0.4 GB for distances
        # (31623, 31623), # 1e9  -- ~4 GB, enable on big machines
    ]
    for rows, cols in grid_sizes:
        for k in [1, 4, 16]:
            for algo in ["dijkstra", "bfs0k"] + (["bfs01"] if k == 1 else []):
                configs.append(("grid",
                                {"rows": rows, "cols": cols, "k": k},
                                algo))

    # ---- Erdos-Renyi
    er_sizes = [
        (100_000, 0.0002),
        (1_000_000, 0.00002),
        (10_000_000, 0.000002),
    ]
    for n, p in er_sizes:
        for k in [1, 4, 16]:
            for algo in ["dijkstra", "bfs0k"] + (["bfs01"] if k == 1 else []):
                configs.append(("er",
                                {"n": n, "p": p, "k": k},
                                algo))

    # ---- Layered DAG
    for L, W in [(100, 1000), (1000, 1000), (1000, 10000)]:
        for k in [1, 4, 16]:
            for algo in ["dijkstra", "bfs0k"] + (["bfs01"] if k == 1 else []):
                configs.append(("layered",
                                {"layers": L, "width": W, "fanout": 4, "k": k},
                                algo))

    # ---- Chain with chords (adversarial)
    for n in [100_000, 1_000_000]:
        for k in [1, 4]:
            for algo in ["dijkstra", "bfs0k"] + (["bfs01"] if k == 1 else []):
                configs.append(("chain",
                                {"n": n, "chords": n // 10, "k": k},
                                algo))

    return configs


def run_one(bench, graph, params, algo, src=0, seed=42, timeout=600):
    cmd = [bench, "--graph", graph, "--algo", algo,
           "--src", str(src), "--seed", str(seed)]
    for k, v in params.items():
        cmd += [f"--{k}", str(v)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "graph": graph, "algo": algo, "params": params}
    if r.returncode != 0:
        return {"error": r.stderr.strip(), "graph": graph, "algo": algo, "params": params}
    line = r.stdout.strip().splitlines()[-1]
    return json.loads(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True, help="path to zkbfs_bench executable")
    ap.add_argument("--out",   default="results/all.jsonl")
    ap.add_argument("--quick", action="store_true",
                    help="skip large configurations (V > 1e7) for a fast smoke test")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    configs = cfg_grid()
    if args.quick:
        def small(p):
            v = p.get("rows", 0) * p.get("cols", 1) + p.get("n", 0) \
                + p.get("layers", 0) * p.get("width", 1)
            return v <= 1_000_000
        configs = [c for c in configs if small(c[1])]

    n = len(configs)
    with open(args.out, "w", encoding="utf-8") as f:
        for i, (graph, params, algo) in enumerate(configs, 1):
            sys.stderr.write(f"[{i}/{n}] {graph} {params} {algo}\n")
            res = run_one(args.bench, graph, params, algo)
            f.write(json.dumps(res) + "\n"); f.flush()
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
