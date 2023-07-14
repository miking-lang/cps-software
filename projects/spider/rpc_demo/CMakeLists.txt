cmake_minimum_required(VERSION 3.15)

project(SpiderRobot VERSION 1.0)

set(CPS_LIBRARY_DIR "../../../lib")

add_subdirectory("${CPS_LIBRARY_DIR}/" "cps")

# Spider controller with only servos
add_executable(spider
    src/main.c
    src/ctrl.c
)
target_compile_options(spider PUBLIC
    -Wall -Wextra -g
)
target_compile_definitions(spider PUBLIC
    LINUX _GNU_SOURCE
)
target_include_directories(spider PUBLIC
    src/
    "${CPS_LIBRARY_DIR}/dxl/"
    # RPC
    "${CPS_LIBRARY_DIR}/rpc/"
)
target_link_libraries(spider PUBLIC
    cps_rpcclient
)

# Spider controller with sensors and servos
add_executable(spider-sensors
    src/main_sensors.c
    src/ctrl.c
)
target_compile_options(spider-sensors PUBLIC
    -Wall -Wextra -g
)
target_compile_definitions(spider-sensors PUBLIC
    LINUX _GNU_SOURCE
)
target_include_directories(spider-sensors PUBLIC
    src/
    "${CPS_LIBRARY_DIR}/dxl/"
    "${CPS_LIBRARY_DIR}/accel/"
    "${CPS_LIBRARY_DIR}/dist/"
    # RPC
    "${CPS_LIBRARY_DIR}/rpc/"
)
target_link_libraries(spider-sensors PUBLIC
    cps_rpcclient
)