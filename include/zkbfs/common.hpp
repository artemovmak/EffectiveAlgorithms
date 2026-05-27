#pragma once

#include <cstdint>
#include <limits>
#include <chrono>
#include <string>
#include <vector>

namespace zkbfs {

using Vertex   = std::uint32_t;
using Index    = std::uint64_t;
using Weight   = std::uint32_t;

// 32-bit distance is safe whenever k * V < 2^32. The benchmark CLI checks this.
// Define ZKBFS_DIST64 to fall back to 64-bit (needed when k*V can overflow).
#ifdef ZKBFS_DIST64
using Distance = std::uint64_t;
#else
using Distance = std::uint32_t;
#endif

constexpr Distance INF_DIST = std::numeric_limits<Distance>::max();
constexpr Vertex   INVALID  = std::numeric_limits<Vertex>::max();

struct RunStats {
    std::string algorithm;
    std::string graph;
    std::uint64_t V = 0;
    std::uint64_t E = 0;
    std::uint32_t k = 0;
    Vertex source = 0;
    double  seconds = 0.0;
    std::uint64_t relaxations = 0;
    std::uint64_t pushes      = 0;
    std::uint64_t pops        = 0;
    std::uint64_t checksum = 0;
    std::uint64_t reachable = 0;
};

class Timer {
public:
    Timer() { reset(); }
    void reset() { t0_ = std::chrono::steady_clock::now(); }
    double seconds() const {
        auto t1 = std::chrono::steady_clock::now();
        return std::chrono::duration<double>(t1 - t0_).count();
    }
private:
    std::chrono::steady_clock::time_point t0_;
};

}
