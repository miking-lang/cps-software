cmake_minimum_required(VERSION 3.15)

project(CPSLib VERSION 1.0)
set(CMAKE_BUILD_TYPE Debug)

# common interface (compile/include/etc)
add_library(common INTERFACE)
target_compile_options(common INTERFACE
	-Wall -Wextra -g
)

## LIBRARIES ##

# CPS Common library
add_library(cps_com STATIC
	"cps/cps.c"
)
target_include_directories(cps_com PUBLIC
	"cps/"
)
target_link_libraries(cps_com PUBLIC common)

# CPS DXL Servo library
add_library(cps_dxl STATIC
	"dxl/dxl.c"
)
target_link_libraries(cps_dxl PUBLIC
	common
	cps_com
	dxl_sbc_c
)
set_target_properties(cps_dxl PROPERTIES
	EXCLUDE_FROM_ALL TRUE
)

# CPS Accelerometer library
add_library(cps_accel STATIC
	"accel/accel.c"
)
target_link_libraries(cps_accel PUBLIC
	common
	cps_com
	m
	i2c
)
set_target_properties(cps_accel PROPERTIES
	EXCLUDE_FROM_ALL TRUE
)

# CPS Distance library
add_library(cps_dist STATIC
	"dist/dist.c"
)
target_link_libraries(cps_dist PUBLIC
	common
	cps_com
	pigpio
)
set_target_properties(cps_dist PROPERTIES
	EXCLUDE_FROM_ALL TRUE
)

## EXAMPLES ##

# CPS DynamixelSDK example
add_executable(dxl-example EXCLUDE_FROM_ALL
	"examples/dxl.c"
)
target_compile_definitions(dxl-example PUBLIC
	LINUX _GNU_SOURCE
)
target_include_directories(dxl-example PUBLIC
	"dxl/"
)
target_link_libraries(dxl-example PUBLIC
	common
	cps_dxl
)

# CPS Accelerometer example
add_executable(accel-example EXCLUDE_FROM_ALL
	"examples/accel.c"
)
target_compile_definitions(accel-example PUBLIC
	LINUX _GNU_SOURCE
)
target_include_directories(accel-example PUBLIC
	"accel/"
)
target_link_libraries(accel-example PUBLIC
	common
	cps_accel
)

# CPS Distance example
add_executable(dist-example EXCLUDE_FROM_ALL
	"examples/dist.c"
)
target_compile_definitions(dist-example PUBLIC
	LINUX _GNU_SOURCE
)
target_include_directories(dist-example PUBLIC
	"dist/"
)
target_link_libraries(dist-example PUBLIC
	common
	cps_dist
)
