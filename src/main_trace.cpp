// Runs the traced 0-k BFS on a small grid and writes:
//   - <out>.events.jsonl : one event per line (push/pop/relax/skip/advance)
//   - <out>.meta.json    : grid metadata (rows, cols, k, source, V)
//
// Usage:
//   zkbfs_trace --rows R --cols C --k K --src V --seed S --out file

#include "zkbfs/common.hpp"
#include "zkbfs/grid_graph.hpp"
#include "zkbfs/bfs0k_trace.hpp"

#include <fstream>
#include <iostream>
#include <unordered_map>
#include <cstring>
#include <stdexcept>

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

int main(int argc, char** argv) {
    try {
        auto a = parse_args(argc, argv);
        std::uint32_t rows = static_cast<std::uint32_t>(getu(a, "rows", 8));
        std::uint32_t cols = static_cast<std::uint32_t>(getu(a, "cols", 8));
        std::uint32_t k    = static_cast<std::uint32_t>(getu(a, "k", 3));
        Vertex src         = static_cast<Vertex>(getu(a, "src", 0));
        std::uint64_t seed = getu(a, "seed", 7);
        std::string out    = get(a, "out", "trace");

        GridGraph g(rows, cols, k, seed);

        std::ofstream ev(out + ".events.jsonl");
        if (!ev) throw std::runtime_error("cannot open events file");

        std::vector<Distance> dist;
        auto st = bfs_0k_trace(g, src, k, dist, ev);

        std::ofstream meta(out + ".meta.json");
        meta << "{\n";
        meta << "  \"graph\":\"grid\",\n";
        meta << "  \"rows\":" << rows << ",\n";
        meta << "  \"cols\":" << cols << ",\n";
        meta << "  \"k\":" << k << ",\n";
        meta << "  \"source\":" << src << ",\n";
        meta << "  \"V\":" << g.V() << ",\n";
        meta << "  \"E\":" << g.E() << ",\n";
        meta << "  \"final_dist\":[";
        for (std::size_t i = 0; i < dist.size(); ++i) {
            if (i) meta << ',';
            if (dist[i] == INF_DIST) meta << -1; else meta << dist[i];
        }
        meta << "],\n";
        meta << "  \"pushes\":"   << st.pushes      << ",\n";
        meta << "  \"pops\":"     << st.pops        << ",\n";
        meta << "  \"checksum\":" << st.checksum    << ",\n";
        meta << "  \"reachable\":"<< st.reachable   << "\n";
        meta << "}\n";

        std::cerr << "wrote " << out << ".events.jsonl and "
                  << out << ".meta.json\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
