#pragma once

#include "common.hpp"
#include <ostream>
#include <string>

namespace zkbfs {

inline void write_run_json(std::ostream& os, const RunStats& s) {
    os << "{"
       << "\"algorithm\":\"" << s.algorithm << "\","
       << "\"graph\":\""     << s.graph     << "\","
       << "\"V\":"           << s.V         << ","
       << "\"E\":"           << s.E         << ","
       << "\"k\":"           << s.k         << ","
       << "\"source\":"      << s.source    << ","
       << "\"seconds\":"     << s.seconds   << ","
       << "\"relaxations\":" << s.relaxations << ","
       << "\"pushes\":"      << s.pushes    << ","
       << "\"pops\":"        << s.pops      << ","
       << "\"reachable\":"   << s.reachable << ","
       << "\"checksum\":"    << s.checksum
       << "}";
}

}
