cmake_minimum_required(VERSION 3.16)
project(zkbfs LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    add_compile_options(-O3 -march=native -Wall -Wextra -Wno-unused-parameter)
elseif(MSVC)
    add_compile_options(/O2 /W3 /permissive- /Zc:__cplusplus)
endif()

include_directories(${CMAKE_SOURCE_DIR}/include)

add_executable(zkbfs_bench
    src/main_bench.cpp
)

add_executable(zkbfs_dump
    src/main_dump.cpp
)

add_executable(zkbfs_trace
    src/main_trace.cpp
)
