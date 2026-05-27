# 0–k BFS: Bounded Integer Weights Shortest Path Problem

C++17 implementation and benchmarks of the 0–k BFS family of shortest-path
algorithms, compared against a Dijkstra baseline. Skoltech Algorithms 2026
course project — Artemov Makar, Mark Shkut.

Headline result: on a 30 000 × 30 000 implicit grid (V = 9·10⁸, E = 3.6·10⁹),
single-threaded 0-1 BFS finishes in **121 s** vs Dijkstra's 620 s — a 5.12×
speed-up with byte-identical checksums.

## Layout

```
include/zkbfs/   header-only algorithms and graph types
  common.hpp     Vertex / Weight / Distance, RunStats, Timer
  graph_csr.hpp  classical CSR graph
  grid_graph.hpp implicit 4-neighbour grid (no edge storage)
  generators.hpp ER, layered DAG, chain-with-chords
  dijkstra.hpp   priority_queue baseline
  bfs01.hpp      0-1 BFS via std::deque
  bfs0k.hpp      0-k BFS via k+1 circular queues
  json_out.hpp   stats serialization
src/
  main_bench.cpp CLI benchmark runner (one JSON line per run)
  main_dump.cpp  dumps a graph + distances to JSON for viz
viz/
  run_pipeline.py    drives a parameter sweep
  visualize_dump.py  grid heatmap / node-link diagram
  plot_benchmarks.py time-vs-V / time-vs-k plots
  report_figs.py     report-quality plots
results/
  logs/         raw run logs (sweep.jsonl, scale_*, grid_headline)
  report_figs/  PNG figures used in the report
stage1_report.pdf   compiled Stage 1 report
project_plan.pdf    project plan
```

## Build (MSYS2 / ucrt64, g++ 15)

```bat
set PATH=C:\msys64\ucrt64\bin;%PATH%
g++ -std=c++17 -O3 -march=native -Iinclude src\main_bench.cpp -o build\zkbfs_bench.exe
g++ -std=c++17 -O3 -march=native -Iinclude src\main_dump.cpp  -o build\zkbfs_dump.exe
```

Or via Make: `make`. Or via CMake: `cmake -S . -B build && cmake --build build`.

## Run

```bat
:: 45-config sweep + plots
python viz\run_pipeline.py    --bench build\zkbfs_bench.exe --out results\sweep.jsonl --quick
python viz\plot_benchmarks.py results\sweep.jsonl --outdir results\figs

:: Visualization example
build\zkbfs_dump.exe --graph grid --rows 80 --cols 80 --k 4 --algo bfs0k ^
                     --src 0 --out results\demo.json
python viz\visualize_dump.py results\demo.json

:: Billion-vertex headline
build\zkbfs_bench.exe --graph grid --rows 30000 --cols 30000 --k 1 --algo bfs01
```

See `stage1_report.pdf` for the full Stage 1 writeup with figures.
