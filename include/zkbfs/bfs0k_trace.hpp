#pragma once

// Instrumented 0-k BFS that writes a per-step trace to a std::ostream.
// Use only on small inputs -- the trace can be much larger than the graph.
//
// Event format: one JSON object per line.
//   {"type":"pop","step":S,"u":U,"bucket":B,"cur":D}
//   {"type":"relax","step":S,"u":U,"v":V,"w":W,"new":D,"bucket":B}
//   {"type":"skip","step":S,"u":U,"reason":"stale"}
//   {"type":"advance","step":S,"cur":D}

#include "common.hpp"
#include <iostream>
#include <vector>
#include <queue>

namespace zkbfs {

template <class G>
RunStats bfs_0k_trace(const G& g, Vertex src, std::uint32_t k,
                      std::vector<Distance>& dist, std::ostream& trace) {
    RunStats st;
    st.algorithm = "bfs_0k_trace";
    st.V = g.V();
    st.source = src;
    st.k = k;

    dist.assign(static_cast<std::size_t>(g.V()), INF_DIST);
    dist[src] = 0;

    const std::uint32_t M = k + 1;
    std::vector<std::queue<Vertex>> Q(M);
    Q[0].push(src);
    ++st.pushes;
    std::uint64_t live = 1;
    std::uint64_t step = 0;

    trace << "{\"type\":\"push\",\"step\":" << step << ",\"u\":" << src
          << ",\"bucket\":0,\"new\":0}\n";

    Distance cur = 0;
    Timer tm;
    while (live > 0) {
        std::uint32_t idx = static_cast<std::uint32_t>(cur % M);
        std::uint32_t scanned = 0;
        while (Q[idx].empty() && scanned < M) {
            ++cur;
            idx = static_cast<std::uint32_t>(cur % M);
            ++scanned;
            trace << "{\"type\":\"advance\",\"step\":" << step
                  << ",\"cur\":" << cur << "}\n";
        }
        if (Q[idx].empty()) break;

        Vertex u = Q[idx].front(); Q[idx].pop();
        ++st.pops;
        --live;
        ++step;
        if (dist[u] != cur) {
            trace << "{\"type\":\"skip\",\"step\":" << step
                  << ",\"u\":" << u << ",\"reason\":\"stale\"}\n";
            continue;
        }
        trace << "{\"type\":\"pop\",\"step\":" << step << ",\"u\":" << u
              << ",\"bucket\":" << idx << ",\"cur\":" << cur << "}\n";

        Distance du = cur;
        g.for_each_neighbour(u, [&](Vertex v, Weight w) {
            ++st.relaxations;
            Distance nd = du + w;
            if (nd < dist[v]) {
                dist[v] = nd;
                std::uint32_t bidx = static_cast<std::uint32_t>(nd % M);
                Q[bidx].push(v);
                ++st.pushes;
                ++live;
                trace << "{\"type\":\"relax\",\"step\":" << step
                      << ",\"u\":" << u << ",\"v\":" << v
                      << ",\"w\":" << w << ",\"new\":" << nd
                      << ",\"bucket\":" << bidx << "}\n";
            }
        });
    }
    st.seconds = tm.seconds();

    std::uint64_t checksum = 0, reached = 0;
    for (auto d : dist) if (d != INF_DIST) { checksum += static_cast<std::uint64_t>(d); ++reached; }
    st.checksum  = checksum;
    st.reachable = reached;
    return st;
}

}
