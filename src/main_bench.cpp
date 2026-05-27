// Benchmark runner.
//
// Usage:
//   zkbfs_bench --graph grid       --rows R --cols C --k K --algo dijkstra|bfs01|bfs0k [--src V] [--seed S]
//   zkbfs_bench --graph er         --n N --p P --k K --algo ... [--src V] [--seed S]
//   zkbfs_bench --graph layered    --layers L --width W --fanout F --k K --algo ...
//   zkbfs_bench --graph chain      --n N --chords C --k K --algo ...
//
// Prints one JSON line per run to stdout.

#include "zkbfs/common.hpp"
#include "zkbfs/grid_graph.hpp"
#include "zkbfs/graph_csr.hpp"
#include "zkbfs/generators.hpp"
#include "zkbfs/dijkstra.hpp"
#include "zkbfs/bfs01.hpp"
#include "zkbfs/bfs0k.hpp"
#include "zkbfs/json_out.hpp"

#include <iostream>
#include <string>
#include <unordered_map>
#include <cstdlib>
#include <stdexcept>
#include <cstring>

using namespace zkbfs;

static std::unordered_map<std::string,std::string> parse_args(int argc, char** argv) {
    std::unordered_map<std::string,std::string> a;
    for (int i = 1; i + 1 < argc; i += 2) {
        if (std::strncmp(argv[i], "--", 2) != 0)
            throw std::runtime_error(std::string("expected --flag at ") + argv[i]);
        a[argv[i] + 2] = argv[i + 1];
    }
    return a;
}

static std::string get(const std::unordered_map<std::string,std::string>& a,
                       const std::string& key, const std::string& dflt = "") {
    auto it = a.find(key);
    return it == a.end() ? dflt : it->second;
}

static std::uint64_t getu(const std::unordered_map<std::string,std::string>& a,
                          const std::string& key, std::uint64_t dflt = 0) {
    auto it = a.find(key);
    return it == a.end() ? dflt : std::stoull(it->second);
}

template <class G>
static RunStats dispatch(const G& g, const std::string& algo, std::uint32_t k,
                         Vertex src, std::vector<Distance>& dist) {
    if (algo == "dijkstra") return dijkstra_pq(g, src, dist);
    if (algo == "bfs01")    return bfs_01    (g, src, dist);
    if (algo == "bfs0k")    return bfs_0k    (g, src, k, dist);
    throw std::runtime_error("unknown algorithm: " + algo);
}

int main(int argc, char** argv) {
    try {
        auto a = parse_args(argc, argv);
        std::string graph = get(a, "graph", "grid");
        std::string algo  = get(a, "algo",  "dijkstra");
        std::uint32_t k   = static_cast<std::uint32_t>(getu(a, "k", 4));
        Vertex src        = static_cast<Vertex>(getu(a, "src", 0));
        std::uint64_t seed= getu(a, "seed", 42);

        std::vector<Distance> dist;
        RunStats st;

        if (graph == "grid") {
            std::uint32_t rows = static_cast<std::uint32_t>(getu(a, "rows", 1000));
            std::uint32_t cols = static_cast<std::uint32_t>(getu(a, "cols", 1000));
            GridGraph g(rows, cols, k, seed);
            st = dispatch(g, algo, k, src, dist);
            st.graph = "grid";
            st.E = g.E();
        } else if (graph == "er") {
            std::uint32_t n = static_cast<std::uint32_t>(getu(a, "n", 100000));
            double p = std::stod(get(a, "p", "0.0001"));
            auto g = gen::erdos_renyi(n, p, k, seed);
            st = dispatch(g, algo, k, src, dist);
            st.graph = "er";
            st.E = g.E();
        } else if (graph == "layered") {
            std::uint32_t L = static_cast<std::uint32_t>(getu(a, "layers", 100));
            std::uint32_t W = static_cast<std::uint32_t>(getu(a, "width", 1000));
            std::uint32_t F = static_cast<std::uint32_t>(getu(a, "fanout", 4));
            auto g = gen::layered_dag(L, W, F, k, seed);
            st = dispatch(g, algo, k, src, dist);
            st.graph = "layered";
            st.E = g.E();
        } else if (graph == "chain") {
            std::uint32_t n = static_cast<std::uint32_t>(getu(a, "n", 100000));
            std::uint32_t c = static_cast<std::uint32_t>(getu(a, "chords", 1000));
            auto g = gen::chain_with_chords(n, c, k, seed);
            st = dispatch(g, algo, k, src, dist);
            st.graph = "chain";
            st.E = g.E();
        } else {
            throw std::runtime_error("unknown --graph: " + graph);
        }

        write_run_json(std::cout, st);
        std::cout << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
