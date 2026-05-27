#pragma once

#include "common.hpp"
#include <queue>
#include <vector>

namespace zkbfs {

// Baseline: Dijkstra with std::priority_queue. Lazy-decrease-key (push duplicates).
// G must provide:
//   uint64_t V()
//   for_each_neighbour(Vertex u, F fn)  ->  fn(Vertex v, Weight w)
template <class G>
RunStats dijkstra_pq(const G& g, Vertex src, std::vector<Distance>& dist) {
    RunStats st;
    st.algorithm = "dijkstra_pq";
    st.V = g.V();
    st.source = src;

    dist.assign(static_cast<std::size_t>(g.V()), INF_DIST);
    dist[src] = 0;

    using QE = std::pair<Distance, Vertex>;
    std::priority_queue<QE, std::vector<QE>, std::greater<QE>> pq;
    pq.emplace(0, src);
    ++st.pushes;

    Timer tm;
    while (!pq.empty()) {
        auto [du, u] = pq.top(); pq.pop();
        ++st.pops;
        if (du != dist[u]) continue;
        g.for_each_neighbour(u, [&](Vertex v, Weight w) {
            ++st.relaxations;
            Distance nd = du + w;
            if (nd < dist[v]) {
                dist[v] = nd;
                pq.emplace(nd, v);
                ++st.pushes;
            }
        });
    }
    st.seconds = tm.seconds();

    std::uint64_t checksum = 0;
    std::uint64_t reached = 0;
    for (auto d : dist) if (d != INF_DIST) { checksum += static_cast<std::uint64_t>(d); ++reached; }
    st.checksum  = checksum;
    st.reachable = reached;
    return st;
}

}
