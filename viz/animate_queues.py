"""Animate the 0-k BFS algorithm on a small grid, showing both the
grid state and the contents of the k+1 circular FIFO queues over time.

Reads:
    <prefix>.events.jsonl  (push / pop / relax / skip / advance events)
    <prefix>.meta.json     (rows, cols, k, source, V)

Renders an MP4 or GIF.

Usage:
    python viz/animate_queues.py results/trace_10x10 --out results/report_figs/queues.gif
"""

import argparse
import json
import os
import sys
from collections import deque

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, PillowWriter


BUCKET_COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52",
                 "#8172B2", "#937860", "#DA8BC3", "#8C8C8C"]


def load(prefix):
    with open(prefix + ".meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    events = []
    with open(prefix + ".events.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return meta, events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix",
                    help="trace prefix; reads <prefix>.events.jsonl + .meta.json")
    ap.add_argument("--out", default="results/report_figs/queues.gif")
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--max-frames", type=int, default=0,
                    help="truncate history to this many frames (0 = no limit)")
    args = ap.parse_args()

    meta, events = load(args.prefix)
    rows, cols, k = meta["rows"], meta["cols"], meta["k"]
    M = k + 1
    src = meta["source"]
    V = rows * cols
    dist_final = np.array(meta["final_dist"], dtype=np.float64)
    dist_final[dist_final < 0] = np.nan
    dmax = float(np.nanmax(dist_final)) if np.any(~np.isnan(dist_final)) else 1.0

    queues = [deque() for _ in range(M)]
    dist = [None] * V
    in_queue_bucket = [None] * V
    finalized = [False] * V
    cur = 0
    history = []

    pending_advance = False
    for ev in events:
        t = ev["type"]
        if t == "push":
            u = ev["u"]; b = ev["bucket"]; d = ev["new"]
            queues[b].append(u)
            dist[u] = d
            in_queue_bucket[u] = b
        elif t == "advance":
            cur = ev["cur"]
            pending_advance = True
            continue
        elif t == "pop":
            u = ev["u"]; b = ev["bucket"]; cur = ev["cur"]
            if queues[b] and queues[b][0] == u:
                queues[b].popleft()
            else:
                try: queues[b].remove(u)
                except ValueError: pass
            finalized[u] = True
            in_queue_bucket[u] = None
        elif t == "skip":
            u = ev["u"]
            for b in range(M):
                if queues[b] and queues[b][0] == u:
                    queues[b].popleft(); break
            else:
                for b in range(M):
                    if u in queues[b]:
                        queues[b].remove(u); break
        elif t == "relax":
            u = ev["u"]; v = ev["v"]; b = ev["bucket"]; d = ev["new"]
            queues[b].append(v)
            dist[v] = d
            in_queue_bucket[v] = b

        history.append({
            "queues": [list(q) for q in queues],
            "dist":   list(dist),
            "in_q":   list(in_queue_bucket),
            "final":  list(finalized),
            "cur":    cur,
            "event":  ev,
        })

    if args.max_frames and len(history) > args.max_frames:
        history = history[:args.max_frames]

    fig = plt.figure(figsize=(10.5, 5.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.05], wspace=0.18)
    ax_grid  = fig.add_subplot(gs[0, 0])
    ax_q     = fig.add_subplot(gs[0, 1])
    fig.patch.set_facecolor("white")

    ax_grid.set_xlim(-0.5, cols - 0.5)
    ax_grid.set_ylim(rows - 0.5, -0.5)
    ax_grid.set_aspect("equal")
    ax_grid.set_xticks([]); ax_grid.set_yticks([])
    ax_grid.set_title("grid  ·  vertex id labels  ·  colour = current bucket",
                      fontsize=10, color="#222", pad=4)
    cell_patches = []
    cell_texts = []
    for r in range(rows):
        for c in range(cols):
            p = mpatches.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                   facecolor="#202028", edgecolor="#555",
                                   linewidth=0.4)
            ax_grid.add_patch(p)
            cell_patches.append(p)
            t = ax_grid.text(c, r, "", ha="center", va="center",
                             fontsize=7, color="#ddd")
            cell_texts.append(t)
    sr, sc = src // cols, src % cols
    ax_grid.add_patch(mpatches.Rectangle(
        (sc - 0.5, sr - 0.5), 1, 1, facecolor="none",
        edgecolor="white", linewidth=2.0, zorder=4))

    ax_q.set_xlim(0, 1.0)
    ax_q.set_ylim(M, 0)
    ax_q.set_xticks([]); ax_q.set_yticks([])
    ax_q.set_title("circular FIFO queues  Q[0..k]  ·  cur points to active",
                   fontsize=10, color="#222", pad=4)
    for b in range(M):
        ax_q.text(-0.01, b + 0.5, f"Q[{b}]", ha="right", va="center",
                  fontsize=10, color=BUCKET_COLORS[b % len(BUCKET_COLORS)])
        ax_q.add_patch(mpatches.Rectangle(
            (0, b), 1, 1, facecolor="#f6f6f8", edgecolor="#bbb",
            linewidth=0.6))

    arrow = ax_q.annotate(" cur", xy=(1.0, 0.5), xytext=(1.04, 0.5),
                          ha="left", va="center", fontsize=10, color="#c0392b",
                          arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.4),
                          annotation_clip=False)

    status = fig.text(0.5, 0.02, "", ha="center", va="bottom",
                      fontsize=10, color="#222")
    fig.suptitle(f"0-k BFS step-by-step  ·  grid {rows}x{cols}, k={k}",
                 fontsize=12, color="#111", y=0.97)

    QUEUE_CAPACITY = max(8, max(max(len(q) for q in snap["queues"]) for snap in history))
    cell_w = 1.0 / QUEUE_CAPACITY
    q_rects = [[] for _ in range(M)]
    q_texts = [[] for _ in range(M)]
    for b in range(M):
        for i in range(QUEUE_CAPACITY):
            rect = mpatches.Rectangle(
                (i * cell_w, b + 0.08), cell_w, 0.84,
                facecolor="white", edgecolor="#999", linewidth=0.4,
                visible=False)
            ax_q.add_patch(rect)
            q_rects[b].append(rect)
            t = ax_q.text(i * cell_w + cell_w / 2, b + 0.5, "",
                          ha="center", va="center", fontsize=8, color="#111")
            q_texts[b].append(t)

    def update(i):
        snap = history[i]
        for v in range(V):
            patch = cell_patches[v]
            txt = cell_texts[v]
            if snap["final"][v]:
                d = snap["dist"][v] if snap["dist"][v] is not None else 0
                patch.set_facecolor("#cdebc4")
                patch.set_edgecolor("#7aa466")
                txt.set_text(f"{d}")
                txt.set_color("#1d3b14")
            elif snap["in_q"][v] is not None:
                b = snap["in_q"][v]
                patch.set_facecolor(BUCKET_COLORS[b % len(BUCKET_COLORS)])
                patch.set_edgecolor("#222")
                txt.set_text(f"{v}")
                txt.set_color("white")
            else:
                patch.set_facecolor("#202028")
                patch.set_edgecolor("#555")
                txt.set_text("")
                txt.set_color("#ccc")
        cur = snap["cur"]
        active_b = cur % M
        for b in range(M):
            q = snap["queues"][b]
            for i_cell in range(QUEUE_CAPACITY):
                rect = q_rects[b][i_cell]
                txt = q_texts[b][i_cell]
                if i_cell < len(q):
                    rect.set_visible(True)
                    rect.set_facecolor(BUCKET_COLORS[b % len(BUCKET_COLORS)])
                    rect.set_alpha(0.7 if b == active_b else 0.35)
                    rect.set_edgecolor("#222" if b == active_b else "#999")
                    txt.set_text(str(q[i_cell]))
                    txt.set_color("white")
                else:
                    rect.set_visible(False)
                    txt.set_text("")
        arrow.xy = (1.0, active_b + 0.5)
        arrow.set_position((1.04, active_b + 0.5))
        ev = snap["event"]
        et = ev["type"]
        if et == "pop":
            msg = f"step {ev['step']}: pop u={ev['u']} from Q[{ev['bucket']}] (cur={ev['cur']})"
        elif et == "relax":
            msg = (f"step {ev['step']}: relax {ev['u']} -> {ev['v']} (w={ev['w']}),  "
                   f"new dist={ev['new']} -> Q[{ev['bucket']}]")
        elif et == "advance":
            msg = f"advance cur -> {ev['cur']}"
        elif et == "skip":
            msg = f"step {ev['step']}: skip stale u={ev['u']}"
        elif et == "push":
            msg = f"init: push source u={ev['u']} -> Q[0]"
        else:
            msg = et
        status.set_text(msg)
        return []

    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    anim = FuncAnimation(fig, update, frames=len(history),
                         interval=1000.0 / args.fps, blit=False)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    writer = PillowWriter(fps=args.fps)
    anim.save(args.out, writer=writer, dpi=args.dpi)
    print(f"wrote {args.out}  ({os.path.getsize(args.out)//1024} KB)")


if __name__ == "__main__":
    main()
