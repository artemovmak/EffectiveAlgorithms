#pragma once

#include "common.hpp"
#include <deque>
#include <vector>

namespace zkbfs {

template <class G>
RunStats bfs_01(const G& g, Vertex src, std::vector<Distance>& dist) {
    RunStats st;
    st.algorithm = "bfs_01";
    st.V = g.V();
    st.source = src;
    st.k = 1;

    dist.assign(static_cast<std::size_t>(g.V()), INF_DIST);
    dist[src] = 0;

    std::deque<Vertex> dq;
    dq.push_back(src);
    ++st.pushes;

    Timer tm;
    while (!dq.empty()) {
        Vertex u = dq.front(); dq.pop_front();
        ++st.pops;
        Distance du = dist[u];
        g.for_each_neighbour(u, [&](Vertex v, Weight w) {
            ++st.relaxations;
            Distance nd = du + w;
            if (nd < dist[v]) {
                dist[v] = nd;
                if (w == 0) dq.push_front(v);
                else        dq.push_back(v);
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
