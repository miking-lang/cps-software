# minimum required version of cmake
cmake_minimum_required(VERSION 3.15)

project(CraneDemo VERSION 1.0)

set(CPS_LIBRARY_DIR "../../../lib")

add_subdirectory("${CPS_LIBRARY_DIR}/" "cps")

# Spider controller with only servos
add_executable(demo
    demo.c
)

target_compile_options(demo PUBLIC
    -Wall -Wextra -g
)
target_compile_definitions(demo PUBLIC
    LINUX _GNU_SOURCE
)
target_include_directories(demo PUBLIC
    "${CPS_LIBRARY_DIR}/dxl/"
    "${CPS_LIBRARY_DIR}/accel/"
)
target_link_directories(cps_dxl PUBLIC
    # This is where DynamixelSDK's libraries end up by default
    /usr/local/lib/
)
target_link_libraries(demo PUBLIC
    cps_accel
    cps_dxl
    i2c
    ncurses
)
