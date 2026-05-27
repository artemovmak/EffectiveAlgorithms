#pragma once

#include "common.hpp"
#include <vector>
#include <queue>

namespace zkbfs {

template <class G>
RunStats bfs_0k(const G& g, Vertex src, std::uint32_t k, std::vector<Distance>& dist) {
    RunStats st;
    st.algorithm = "bfs_0k";
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

    Distance cur = 0;
    Timer tm;
    while (live > 0) {
        std::uint32_t idx = static_cast<std::uint32_t>(cur % M);
        std::uint32_t scanned = 0;
        while (Q[idx].empty() && scanned < M) {
            ++cur;
            idx = static_cast<std::uint32_t>(cur % M);
            ++scanned;
        }
        if (Q[idx].empty()) break;

        Vertex u = Q[idx].front(); Q[idx].pop();
        ++st.pops;
        --live;
        if (dist[u] != cur) continue;
        Distance du = cur;
        g.for_each_neighbour(u, [&](Vertex v, Weight w) {
            ++st.relaxations;
            Distance nd = du + w;
            if (nd < dist[v]) {
                dist[v] = nd;
                Q[static_cast<std::uint32_t>(nd % M)].push(v);
                ++st.pushes;
                ++live;
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
