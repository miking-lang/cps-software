cmake_minimum_required(VERSION 3.15)

project(SpiderRobot VERSION 1.0)

set(CPS_LIBRARY_DIR "../../lib")

# CPS DXL Servo library
add_library(cps_dxl STATIC
	"${CPS_LIBRARY_DIR}/dxl/dxl.c")
target_link_libraries(cps_dxl PUBLIC
	dxl_x64_c
)

# CPS Accelerometer library
add_library(cps_accel STATIC
	"${CPS_LIBRARY_DIR}/accel/accel.c")
target_link_libraries(cps_accel PUBLIC
	m
	i2c
)

# Spider controller
add_executable(spider
	src/main.c
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
	"${CPS_LIBRARY_DIR}/accel/"
)
target_link_directories(cps_dxl PUBLIC
	# This is where DynamixelSDK's libraries end up by default
	/usr/local/lib/
)
target_link_libraries(spider PUBLIC
	cps_dxl
	cps_accel
)
