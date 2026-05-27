// Dumps a small graph + per-vertex distances as JSON for the Python visualizer.
//
// Usage:
//   zkbfs_dump --graph grid --rows R --cols C --k K --algo dijkstra|bfs01|bfs0k --src V --out file.json

#include "zkbfs/common.hpp"
#include "zkbfs/grid_graph.hpp"
#include "zkbfs/graph_csr.hpp"
#include "zkbfs/generators.hpp"
#include "zkbfs/dijkstra.hpp"
#include "zkbfs/bfs01.hpp"
#include "zkbfs/bfs0k.hpp"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>
#include <unordered_map>
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
    auto it = a.find(key); return it == a.end() ? dflt : it->second;
}
static std::uint64_t getu(const std::unordered_map<std::string,std::string>& a,
                          const std::string& key, std::uint64_t dflt = 0) {
    auto it = a.find(key); return it == a.end() ? dflt : std::stoull(it->second);
}

template <class G>
static void run_and_dump(const G& g, const std::string& algo, std::uint32_t k,
                        Vertex src, std::ostream& os, const std::string& gname) {
    std::vector<Distance> dist;
    RunStats st;
    if      (algo == "dijkstra") st = dijkstra_pq(g, src, dist);
    else if (algo == "bfs01")    st = bfs_01    (g, src, dist);
    else if (algo == "bfs0k")    st = bfs_0k    (g, src, k, dist);
    else throw std::runtime_error("unknown algorithm: " + algo);

    os << "{\n";
    os << "  \"graph\":\"" << gname << "\",\n";
    os << "  \"algorithm\":\"" << algo << "\",\n";
    os << "  \"k\":" << k << ",\n";
    os << "  \"source\":" << src << ",\n";
    os << "  \"V\":" << g.V() << ",\n";
    os << "  \"seconds\":" << st.seconds << ",\n";
    os << "  \"relaxations\":" << st.relaxations << ",\n";
    os << "  \"pushes\":" << st.pushes << ",\n";
    os << "  \"pops\":" << st.pops << ",\n";

    if constexpr (std::is_same_v<G, GridGraph>) {
        os << "  \"rows\":" << g.rows() << ",\n";
        os << "  \"cols\":" << g.cols() << ",\n";
    }

    os << "  \"dist\":[";
    for (std::size_t i = 0; i < dist.size(); ++i) {
        if (i) os << ',';
        if (dist[i] == INF_DIST) os << -1; else os << dist[i];
    }
    os << "],\n";

    if constexpr (!std::is_same_v<G, GridGraph>) {
        os << "  \"edges\":[";
        bool first = true;
        for (std::uint64_t u = 0; u < g.V(); ++u) {
            for (std::uint64_t p = g.deg_begin(static_cast<Vertex>(u));
                 p < g.deg_end(static_cast<Vertex>(u)); ++p) {
                if (!first) os << ',';
                first = false;
                os << '[' << u << ',' << g.head_ptr()[p] << ',' << g.weight_ptr()[p] << ']';
            }
        }
        os << "]\n";
    } else {
        os << "  \"edges\":[]\n";
    }
    os << "}\n";
}

int main(int argc, char** argv) {
    try {
        auto a = parse_args(argc, argv);
        std::string graph = get(a, "graph", "grid");
        std::string algo  = get(a, "algo",  "bfs0k");
        std::uint32_t k   = static_cast<std::uint32_t>(getu(a, "k", 4));
        Vertex src        = static_cast<Vertex>(getu(a, "src", 0));
        std::uint64_t seed= getu(a, "seed", 42);
        std::string out   = get(a, "out", "dump.json");

        std::ofstream os(out);
        if (!os) throw std::runtime_error("cannot open " + out);

        if (graph == "grid") {
            std::uint32_t rows = static_cast<std::uint32_t>(getu(a, "rows", 60));
            std::uint32_t cols = static_cast<std::uint32_t>(getu(a, "cols", 60));
            GridGraph g(rows, cols, k, seed);
            run_and_dump(g, algo, k, src, os, "grid");
        } else if (graph == "er") {
            std::uint32_t n = static_cast<std::uint32_t>(getu(a, "n", 200));
            double p = std::stod(get(a, "p", "0.02"));
            auto g = gen::erdos_renyi(n, p, k, seed);
            run_and_dump(g, algo, k, src, os, "er");
        } else if (graph == "layered") {
            std::uint32_t L = static_cast<std::uint32_t>(getu(a, "layers", 10));
            std::uint32_t W = static_cast<std::uint32_t>(getu(a, "width", 12));
            std::uint32_t F = static_cast<std::uint32_t>(getu(a, "fanout", 3));
            auto g = gen::layered_dag(L, W, F, k, seed);
            run_and_dump(g, algo, k, src, os, "layered");
        } else if (graph == "chain") {
            std::uint32_t n = static_cast<std::uint32_t>(getu(a, "n", 200));
            std::uint32_t c = static_cast<std::uint32_t>(getu(a, "chords", 30));
            auto g = gen::chain_with_chords(n, c, k, seed);
            run_and_dump(g, algo, k, src, os, "chain");
        } else {
            throw std::runtime_error("unknown --graph: " + graph);
        }
        std::cerr << "wrote " << out << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
