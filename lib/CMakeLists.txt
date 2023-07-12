cmake_minimum_required(VERSION 3.15)

project(CPSLib VERSION 1.0)
set(CMAKE_BUILD_TYPE Debug)

# CPS Common library
add_library(cps_com STATIC
	"cps/cps.c"
)
target_compile_options(cps_com PUBLIC
	-Wall -Wextra -g
)
target_include_directories(cps_com PUBLIC
	"cps/"
)

# CPS DXL Servo library
add_library(cps_dxl STATIC
	"dxl/dxl.c"
)
target_compile_options(cps_dxl PUBLIC
	-Wall -Wextra -g
)
target_link_libraries(cps_dxl PUBLIC
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
target_compile_options(cps_accel PUBLIC
	-Wall -Wextra -g
)
target_link_libraries(cps_accel PUBLIC
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
target_compile_options(cps_dist PUBLIC
	-Wall -Wextra -g
)
target_link_libraries(cps_dist PUBLIC
	cps_com
	pigpio
)
set_target_properties(cps_dist PROPERTIES
	EXCLUDE_FROM_ALL TRUE
)

#CPS MG90S library
add_library(cps_mg90s STATIC
	"mg90s/mg90s.c"
)
target_compile_options(cps_mg90s PUBLIC
	-Wall -Wextra -g
)
target_link_libraries(cps_mg90s PUBLIC
	cps_com
	i2c
)
set_target_properties(cps_mg90s PROPERTIES
	EXCLUDE_FROM_ALL TRUE
)

# CPS DynamixelSDK example
add_executable(dxl-example EXCLUDE_FROM_ALL
	"examples/dxl.c"
)
target_compile_options(dxl-example PUBLIC
	-Wall -Wextra -g
)
target_compile_definitions(dxl-example PUBLIC
	LINUX _GNU_SOURCE
)
target_include_directories(dxl-example PUBLIC
	"dxl/"
)
target_link_libraries(dxl-example PUBLIC
	cps_dxl
)

# CPS Accelerometer example
add_executable(accel-example EXCLUDE_FROM_ALL
	"examples/accel.c"
)
target_compile_options(accel-example PUBLIC
	-Wall -Wextra -g
)
target_compile_definitions(accel-example PUBLIC
	LINUX _GNU_SOURCE
)
target_include_directories(accel-example PUBLIC
	"accel/"
)
target_link_libraries(accel-example PUBLIC
	cps_accel
)

# CPS Distance example
add_executable(dist-example EXCLUDE_FROM_ALL
	"examples/dist.c"
)
target_compile_options(dist-example PUBLIC
	-Wall -Wextra -g
)
target_compile_definitions(dist-example PUBLIC
	LINUX _GNU_SOURCE
)
target_include_directories(dist-example PUBLIC
	"dist/"
)
target_link_libraries(dist-example PUBLIC
	cps_dist
)

# CPS Distance example
add_executable(mg90s-example EXCLUDE_FROM_ALL
	"examples/mg90s.c"
)
target_compile_options(mg90s-example PUBLIC
	-Wall -Wextra -g
)
target_compile_definitions(mg90s-example PUBLIC
	LINUX _GNU_SOURCE
)
target_include_directories(mg90s-example PUBLIC
	"mg90s/"
)
target_link_libraries(mg90s-example PUBLIC
	cps_mg90s
)