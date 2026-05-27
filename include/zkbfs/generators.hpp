#pragma once

#include "common.hpp"
#include "graph_csr.hpp"
#include <random>
#include <tuple>

namespace zkbfs::gen {

inline GraphCSR erdos_renyi(std::uint32_t n, double p, std::uint32_t k, std::uint64_t seed) {
    std::mt19937_64 rng(seed);
    std::uniform_real_distribution<double> ur(0.0, 1.0);
    std::uniform_int_distribution<int>     uk(0, static_cast<int>(k));
    std::vector<std::tuple<Vertex,Vertex,Weight>> edges;
    if (p <= 0.0 || p > 1.0) p = std::min(std::max(p, 0.0), 1.0);
    double logq = std::log(1.0 - p + 1e-300);
    std::int64_t v = 1, w = -1;
    while (v < n) {
        double r = std::log(1.0 - ur(rng));
        w += 1 + static_cast<std::int64_t>(r / logq);
        while (w >= v && v < n) { w -= v; ++v; }
        if (v < n) {
            edges.emplace_back(static_cast<Vertex>(v),
                               static_cast<Vertex>(w),
                               static_cast<Weight>(uk(rng)));
        }
    }
    GraphCSR g;
    g.build_from_edges(n, edges, true);
    return g;
}

inline GraphCSR layered_dag(std::uint32_t L, std::uint32_t W, std::uint32_t fanout,
                            std::uint32_t k, std::uint64_t seed) {
    std::mt19937_64 rng(seed);
    std::uniform_int_distribution<std::uint32_t> uw(0, W - 1);
    std::uniform_int_distribution<int>           uk(0, static_cast<int>(k));
    std::uint64_t V = static_cast<std::uint64_t>(L) * W;
    std::vector<std::tuple<Vertex,Vertex,Weight>> edges;
    edges.reserve(static_cast<std::size_t>(V) * fanout);
    for (std::uint32_t l = 0; l + 1 < L; ++l) {
        for (std::uint32_t i = 0; i < W; ++i) {
            Vertex u = static_cast<Vertex>(static_cast<std::uint64_t>(l) * W + i);
            for (std::uint32_t f = 0; f < fanout; ++f) {
                Vertex v = static_cast<Vertex>(static_cast<std::uint64_t>(l + 1) * W + uw(rng));
                edges.emplace_back(u, v, static_cast<Weight>(uk(rng)));
            }
        }
    }
    GraphCSR g;
    g.build_from_edges(V, edges, false);
    return g;
}

inline GraphCSR chain_with_chords(std::uint32_t n, std::uint32_t chords,
                                  std::uint32_t k, std::uint64_t seed) {
    std::mt19937_64 rng(seed);
    std::uniform_int_distribution<int> uk(0, static_cast<int>(k));
    std::uniform_int_distribution<std::uint32_t> un(0, n - 1);
    std::vector<std::tuple<Vertex,Vertex,Weight>> edges;
    edges.reserve(static_cast<std::size_t>(n - 1) + chords);
    for (std::uint32_t i = 0; i + 1 < n; ++i)
        edges.emplace_back(i, i + 1, static_cast<Weight>(uk(rng)));
    for (std::uint32_t i = 0; i < chords; ++i) {
        Vertex a = un(rng), b = un(rng);
        if (a != b)
            edges.emplace_back(a, b, static_cast<Weight>(uk(rng)));
    }
    GraphCSR g;
    g.build_from_edges(n, edges, true);
    return g;
}

}
