# 0–k BFS — Stage 1 report

**Authors.** Artemov Makar, Mark Shkut · Skoltech Algorithms 2026
**Date.** 2026-05-21
**Repository root.** `c:\Users\user\Desktop\Skoltech\Algo2026`
**Language.** C++17 (g++ 15.2 / mingw-w64-ucrt), Python 3.11 (visualization)

## 1. Scope

The goal of Stage 1 is to build and benchmark a C++ implementation of the
0–k BFS family of shortest-path algorithms and to compare it against a
Dijkstra baseline, scaling the input to the largest vertex count a commodity
workstation can handle — our concrete target was $V$ approaching $10^9$. At
that scale **explicit edge storage is infeasible** (a CSR with $E=4V$ and
32-bit ids/weights costs $\approx 20$ GB at $V=10^9$), so the project
distinguishes two graph backends:

| backend       | representation                              | max V on a 32 GB workstation |
|---------------|---------------------------------------------|------------------------------|
| `GridGraph`   | implicit 4-neighbour grid + per-vertex byte | up to $V \approx 10^9$       |
| `GraphCSR`    | classical CSR (offset + head + weight)      | up to $V \approx 10^8$       |

The grid backend never materializes edges; `for_each_neighbour(u)` computes
them in $O(1)$. The distance array is the dominant memory cost
($8V$ bytes for `uint64_t`).

## 2. Deliverables

| item                                                            | status      |
|-----------------------------------------------------------------|-------------|
| Dataset analysis and generators                                 | done        |
| Visualization of algorithm output                               | done        |
| Pipeline that runs algorithms across configurations             | done        |
| **Baseline algorithm** (Dijkstra)                               | done        |
| **Main algorithm** (0-1 BFS + 0-k BFS)                          | done        |

Everything has been built, executed and cross-validated (every algorithm's
distance checksum is verified against Dijkstra on the same input).

## 3. Repository layout

```
Algo2026/
├── CMakeLists.txt          # CMake build
├── Makefile                # alternative: GNU make + g++
├── include/zkbfs/
│   ├── common.hpp          # Vertex/Weight/Distance typedefs, RunStats, Timer
│   ├── graph_csr.hpp       # CSR graph with for_each_neighbour
│   ├── grid_graph.hpp      # implicit 4-conn grid (no edge storage)
│   ├── generators.hpp      # erdos_renyi / layered_dag / chain_with_chords
│   ├── dijkstra.hpp        # baseline: std::priority_queue
│   ├── bfs01.hpp           # 0-1 BFS via std::deque
│   ├── bfs0k.hpp           # 0-k BFS with k+1 circular FIFO queues
│   └── json_out.hpp        # JSON serialization for stats
├── src/
│   ├── main_bench.cpp      # CLI benchmark runner -> JSON to stdout
│   └── main_dump.cpp       # dumps graph + distances to JSON for viz
├── viz/
│   ├── run_pipeline.py     # drives the sweep, collects JSONL
│   ├── visualize_dump.py   # grid heatmap / node-link diagram
│   └── plot_benchmarks.py  # time-vs-V and time-vs-k plots
└── results/                # JSON dumps, PNGs, sweep.jsonl, scale_*.log
```

## 4. Datasets

We use synthetic generators (seeded `std::mt19937_64`) — no external dataset
is required at this stage, but the CSR backend can be loaded from any DIMACS
file later because it accepts a vector of `(u, v, w)` edges directly.

| family    | parameters                                | why it is interesting                                                 |
|-----------|-------------------------------------------|------------------------------------------------------------------------|
| `grid`    | `rows`, `cols`, `k`                       | implicit-edge: stresses the algorithm, not memory; reaches $V=10^9$    |
| `er`      | $G(n,p)$, weights $\in \{0..k\}$          | dense, "average-case" — exposes the asymptotic gap with Dijkstra       |
| `layered` | $L$ layers of $W$ vertices, fanout $F$    | DAG — distances grow monotonically, queues stay shallow                |
| `chain`   | path of $n$ vertices + $c$ random chords  | adversarial: many vertices reachable through cheap chord + chain      |

For each family the weights are drawn uniformly from $\{0, 1, \dots, k\}$.
The grid additionally assigns each vertex a "terrain" byte and defines
$w(u,v) = (\mathrm{terrain}[u] + \mathrm{terrain}[v]) \bmod (k{+}1)$
so weights are bounded **and** structured (creates "mountains" + "valleys"
visible in the heatmap).

## 5. Algorithms implemented

1. **`dijkstra_pq` (baseline).** `std::priority_queue<pair<Distance,Vertex>>`
   with lazy decrease-key (re-push and skip-on-pop). Complexity
   $O((V+E)\log V)$, memory $O(V+E)$.
2. **`bfs_01`.** Standard `std::deque`: weight 0 → `push_front`, weight 1 →
   `push_back`. Complexity $O(V+E)$.
3. **`bfs_0k`.** $k+1$ circular FIFO queues. The current processing distance
   `cur` walks forward; vertex $v$ relaxed to distance $d$ is enqueued in
   `Q[d mod (k+1)]`. Stale entries (the same vertex relaxed twice) are
   skipped on pop. Complexity $O(kV+E)$, memory $O(k+E)$ for the queues
   plus $O(V)$ for distances.

The three algorithms are templated over the graph adapter, so the same code
runs on `GridGraph` and `GraphCSR`.

## 6. Visualization

Two visual layers; both produced from JSON dumped by `zkbfs_dump`:

- **Per-graph distance field.** Grid → 2-D heatmap of `dist[r,c]` (see
  `results/grid_80_bfs0k.png`); general graph → node-link diagram with a
  circular or layered layout, vertex colour = distance from source (see
  `results/er_150_bfs0k.png`, `results/layered_bfs0k.png`). Unreachable
  vertices are drawn grey.
- **Benchmark plots.** `viz/plot_benchmarks.py` consumes the JSONL emitted
  by `run_pipeline.py` and renders log-log plots of seconds vs $V$ and
  seconds vs $k$ for every `(graph, algorithm)` combination
  (`results/figs/time_vs_V.png`, `time_vs_k.png`).

## 7. Headline measurements

All checksums of distance arrays matched across algorithms on every
input — correctness sanity check holds.

**Grid scaling, $k=4$, single thread, Windows 11, 32 GB RAM.**

| $V$            | Dijkstra | 0-k BFS | speed-up |
|----------------|----------|---------|----------|
| $10^6$         | 187 ms   |  70 ms  | 2.67×    |
| $10^7$         | 1.98 s   |  0.52 s | 3.81×    |
| $10^8$         | 24.45 s  |  7.77 s | 3.15×    |
| $4.84\cdot10^8$| 432.9 s  | 451.4 s | 0.96×    |

**At V≈10⁹ (k=1, grid 30000×30000 = 9·10⁸ vertices), single thread:**

| algorithm  | wall time | speed-up vs Dijkstra |
|------------|-----------|----------------------|
| Dijkstra   | 619.9 s   | 1.00×                |
| 0-1 BFS    | 121.2 s   | **5.12×**            |

Both produce the same distance-sum checksum 1 703 472 107 894 — correctness
holds at the billion-vertex scale. 3.6·10⁹ edge relaxations were performed
in either case; all 900 million vertices were reached.

A single-source shortest-path search on a graph with 0.9 billion vertices
therefore completes in about two minutes in pure single-threaded C++, well
within commodity-RAM budgets thanks to (i) the implicit grid (no edge
storage) and (ii) `uint32_t` distances, valid whenever $k \cdot V < 2^{32}$.
The 5.12× speed-up over Dijkstra at this scale confirms that the asymptotic
advantage of 0–1 BFS persists even at the billion-vertex frontier (provided
the working set fits in RAM — see §8).

**Grid scaling, $k=1$, $V=10^6$.** Dijkstra 133 ms, 0-1 BFS 24 ms (~5.6×),
0-k BFS 34 ms (~3.9×).

**Erdős–Rényi $V=10^5$, $E\approx 10^6$, $k=4$.** Dijkstra 49 ms,
0-k BFS 13 ms (~3.7×).

The full sweep is in `results/sweep.jsonl` (45 runs) with plots under
`results/figs/`.

## 8. Limitations seen so far

- The pure 0-k BFS *does not* asymptotically beat Dijkstra once
  $k = \omega(\log V)$. In the $V=10^6$ grid the speed-up over Dijkstra
  shrinks from 5.6× ($k=1$) to 2.7× ($k=4$) and falls further at $k=16$.
- **Memory-bandwidth ceiling.** At $V=4.84\cdot10^8$ both algorithms become
  memory-bound: the queues alone are multi-gigabyte structures (peak push
  count ≈ $6\cdot10^8$), so the algorithmic advantage of 0-k BFS over a
  cache-aware Dijkstra essentially disappears (0.96×). Above this scale the
  bottleneck is RAM bandwidth, not the priority queue. We applied a 32-bit
  `Distance` specialisation (halves the distance array to 3.6 GB at
  $V=9\cdot10^8$) which keeps the working set within physical memory.
- The lazy-decrease-key Dijkstra reinserts entries — a small overhead, but
  it keeps the baseline portable. An indexed $d$-ary heap is on the list
  for Week 2.

## 9. Next steps (Week 2)

1. 32-bit-distance variant + a real $V=10^9$ run (single-source on a
   $\sim 31{,}600 \times 31{,}600$ grid).
2. Indexed 4-ary heap Dijkstra; compare against the `priority_queue` baseline.
3. Add a road-network loader (DIMACS USA, weights quantised to $k=8$).
4. Optional: parallel front via $\Delta$-stepping for context.

## 10. How to reproduce

```bat
:: Windows / MSYS2 (ucrt64)
set PATH=C:\msys64\ucrt64\bin;%PATH%
g++ -std=c++17 -O3 -march=native -Iinclude src\main_bench.cpp -o build\zkbfs_bench.exe
g++ -std=c++17 -O3 -march=native -Iinclude src\main_dump.cpp  -o build\zkbfs_dump.exe

build\zkbfs_bench.exe --graph grid --rows 10000 --cols 10000 --k 4 --algo bfs0k
python viz\run_pipeline.py --bench build\zkbfs_bench.exe --out results\sweep.jsonl --quick
python viz\plot_benchmarks.py results\sweep.jsonl --outdir results\figs

build\zkbfs_dump.exe --graph grid --rows 80 --cols 80 --k 4 --algo bfs0k --out results\demo.json
python viz\visualize_dump.py results\demo.json
```
