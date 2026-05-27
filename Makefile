CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O3 -march=native -Wall -Wextra -Wno-unused-parameter -Iinclude
LDFLAGS  ?=

BIN := build
TARGETS := $(BIN)/zkbfs_bench $(BIN)/zkbfs_dump

all: $(TARGETS)

$(BIN):
	@mkdir -p $(BIN)

$(BIN)/zkbfs_bench: src/main_bench.cpp $(wildcard include/zkbfs/*.hpp) | $(BIN)
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

$(BIN)/zkbfs_dump:  src/main_dump.cpp  $(wildcard include/zkbfs/*.hpp) | $(BIN)
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

clean:
	rm -rf $(BIN)

.PHONY: all clean
