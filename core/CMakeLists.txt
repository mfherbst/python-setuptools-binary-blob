cmake_minimum_required(VERSION 3.2.0)

set(CMAKE_BUILD_TYPE "Release" CACHE STRING "The type of build")
project(core VERSION 0.0.0)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Global include directories for this project:
include_directories(".")
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_library(core SHARED core.cc)
set_target_properties(core PROPERTIES
	POSITION_INDEPENDENT_CODE ON
	LINKER_LANGUAGE "CXX"
	VERSION "${PROJECT_VERSION}"
	NO_SONAME ON
)
if(APPLE)
	set_target_properties(core PROPERTIES
		POSITION_INDEPENDENT_CODE ON
		MACOSX_RPATH ON
		LINKER_LANGUAGE "CXX"
		VERSION "${PROJECT_VERSION}"
		NO_SONAME OFF
	)
endif()

install(TARGETS core
	DESTINATION lib
	COMPONENT library
)

# install the includes:
install(FILES
	core.hh
	DESTINATION "include/core"
	COMPONENT devel
)

# Drop core_config.json for adcc compilation
configure_file(core_config.json.in core_config.json)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/core_config.json
	DESTINATION .
	COMPONENT devel
)
