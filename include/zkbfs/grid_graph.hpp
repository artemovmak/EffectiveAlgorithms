#pragma once

#include "common.hpp"
#include <cstdint>
#include <vector>
#include <random>
#include <stdexcept>

namespace zkbfs {

class GridGraph {
public:
    GridGraph(std::uint32_t rows, std::uint32_t cols, std::uint32_t k, std::uint64_t seed)
        : rows_(rows), cols_(cols), k_(k)
    {
        if (static_cast<std::uint64_t>(rows) * cols > std::numeric_limits<Vertex>::max())
            throw std::runtime_error("grid too large for uint32 vertex id");
        terrain_.resize(static_cast<std::size_t>(rows) * cols);
        std::mt19937_64 rng(seed);
        std::uniform_int_distribution<int> d(0, static_cast<int>(k));
        for (auto& t : terrain_) t = static_cast<std::uint8_t>(d(rng));
    }

    std::uint64_t V() const { return static_cast<std::uint64_t>(rows_) * cols_; }
    std::uint64_t E() const {
        std::uint64_t e = 0;
        if (cols_ > 1) e += 2ull * rows_ * (cols_ - 1);
        if (rows_ > 1) e += 2ull * (rows_ - 1) * cols_;
        return e;
    }
    std::uint32_t k() const { return k_; }
    std::uint32_t rows() const { return rows_; }
    std::uint32_t cols() const { return cols_; }

    inline Vertex id(std::uint32_t r, std::uint32_t c) const {
        return static_cast<Vertex>(r) * cols_ + c;
    }

    template <class F>
    inline void for_each_neighbour(Vertex u, F&& fn) const {
        std::uint32_t r = u / cols_;
        std::uint32_t c = u - static_cast<std::uint64_t>(r) * cols_;
        std::uint32_t kp1 = k_ + 1;
        std::uint8_t  tu = terrain_[u];
        if (c + 1 < cols_) { Vertex v = u + 1;     fn(v, static_cast<Weight>((tu + terrain_[v]) % kp1)); }
        if (c > 0)         { Vertex v = u - 1;     fn(v, static_cast<Weight>((tu + terrain_[v]) % kp1)); }
        if (r + 1 < rows_) { Vertex v = u + cols_; fn(v, static_cast<Weight>((tu + terrain_[v]) % kp1)); }
        if (r > 0)         { Vertex v = u - cols_; fn(v, static_cast<Weight>((tu + terrain_[v]) % kp1)); }
    }

    std::uint64_t bytes() const { return terrain_.capacity(); }

private:
    std::uint32_t rows_;
    std::uint32_t cols_;
    std::uint32_t k_;
    std::vector<std::uint8_t> terrain_;
};

}
