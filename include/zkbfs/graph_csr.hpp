#pragma once

#include "common.hpp"
#include <vector>
#include <cstdint>
#include <stdexcept>

namespace zkbfs {

// Compressed sparse row graph. Vertex count fits in uint32_t, edge count in uint64_t.
// Memory: 8*(V+1) + 8*E bytes (offset + (to,w) packed into uint64_t when w<=k<2^32).
class GraphCSR {
public:
    GraphCSR() = default;

    void build_from_edges(std::uint64_t V,
                          std::vector<std::tuple<Vertex,Vertex,Weight>>& edges,
                          bool symmetrize)
    {
        V_ = V;
        offset_.assign(V_ + 1, 0);
        if (symmetrize) {
            std::size_t old = edges.size();
            edges.reserve(old * 2);
            for (std::size_t i = 0; i < old; ++i) {
                auto [u, v, w] = edges[i];
                edges.emplace_back(v, u, w);
            }
        }
        for (auto& [u, v, w] : edges) {
            if (u >= V_) throw std::runtime_error("edge u out of range");
            ++offset_[u + 1];
        }
        for (std::uint64_t i = 1; i <= V_; ++i) offset_[i] += offset_[i - 1];
        E_ = offset_[V_];
        head_.resize(E_);
        weight_.resize(E_);
        std::vector<std::uint64_t> cursor = offset_;
        for (auto& [u, v, w] : edges) {
            auto p = cursor[u]++;
            head_[p]   = v;
            weight_[p] = w;
        }
    }

    std::uint64_t V() const { return V_; }
    std::uint64_t E() const { return E_; }
    const std::uint64_t* offset_ptr() const { return offset_.data(); }
    const Vertex*        head_ptr()   const { return head_.data(); }
    const Weight*        weight_ptr() const { return weight_.data(); }

    // Range of outgoing edges of u: [offset[u], offset[u+1]).
    std::uint64_t deg_begin(Vertex u) const { return offset_[u]; }
    std::uint64_t deg_end  (Vertex u) const { return offset_[u + 1]; }

    template <class F>
    inline void for_each_neighbour(Vertex u, F&& fn) const {
        std::uint64_t b = offset_[u], e = offset_[u + 1];
        for (std::uint64_t p = b; p < e; ++p) fn(head_[p], weight_[p]);
    }

    std::uint64_t bytes() const {
        return offset_.capacity() * sizeof(std::uint64_t)
             + head_.capacity()   * sizeof(Vertex)
             + weight_.capacity() * sizeof(Weight);
    }

private:
    std::uint64_t V_ = 0;
    std::uint64_t E_ = 0;
    std::vector<std::uint64_t> offset_;
    std::vector<Vertex>        head_;
    std::vector<Weight>        weight_;
};

}
