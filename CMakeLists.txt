cmake_minimum_required(VERSION 3.20)
if(POLICY CMP0144)
  cmake_policy(SET CMP0144 OLD)
endif()
if(POLICY CMP0167)
  cmake_policy(SET CMP0167 OLD)
endif()

# SaltsNet Project - Network tools built on Salts
project(
  SaltsNet
  VERSION 0.1.0
  LANGUAGES C CXX)

# Project configuration - output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Normalize install prefix (remove trailing slashes)
get_filename_component(CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}" ABSOLUTE)

# Project description
set(PROJECT_DESCRIPTION "High-performance networking library")
set(PROJECT_HOMEPAGE_URL "https://github.com/qigao/salts-netutils")

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
# Language standards - unified approach
set(CMAKE_CXX_STANDARD 17) # C++17 for compatibility
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(ANDROID)
  add_link_options("LINKER:-z,max-page-size=16384" "LINKER:-z,common-page-size=16384")
endif()

if(MSVC)
  # Align with Salts 2.3: the dash spelling is compatible with the MSVC ccache launcher.
  add_compile_options("$<$<COMPILE_LANGUAGE:C>:-experimental:c11atomics>")
endif()
# Enable folder organization in IDEs
set_property(GLOBAL PROPERTY USE_FOLDERS ON)
set_property(GLOBAL PROPERTY PREDEFINED_TARGETS_FOLDER "cmake")

# CTest owns the canonical BUILD_TESTING switch and test registration.
include(CTest)

include(CMakeOptions.cmake)
if(BUILD_BENCHMARKS)
  enable_testing()
endif()
include(Sanitizers)
include(CmakeUtils)

# The product presets read a restored vcpkg profile without invoking vcpkg.
if(NOT CMAKE_TOOLCHAIN_FILE AND VCPKG_INSTALLED_DIR AND VCPKG_TARGET_TRIPLET)
  set(_saltsnet_vcpkg_prefix "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}")
  if(NOT IS_DIRECTORY "${_saltsnet_vcpkg_prefix}")
    message(FATAL_ERROR "Preinstalled vcpkg triplet directory is missing: ${_saltsnet_vcpkg_prefix}")
  endif()
  list(PREPEND CMAKE_PREFIX_PATH "${_saltsnet_vcpkg_prefix}")
  if(NOT "$ENV{VCPKG_CONFIGURATION_SUBDIR}" STREQUAL "")
    list(PREPEND CMAKE_PREFIX_PATH "${_saltsnet_vcpkg_prefix}/$ENV{VCPKG_CONFIGURATION_SUBDIR}")
  endif()
endif()

include(cmake/SaltsNetDependencies.cmake)
# Additional components
add_subdirectory(tools)
include(FindTools)


add_subdirectory(ice)
add_subdirectory(snmp)
add_subdirectory(ldap)
add_subdirectory(email)
add_subdirectory(internal)
add_subdirectory(lb)
add_subdirectory(tproxy)

if(BUILD_TESTING)
  add_subdirectory(tests)
endif()

# Package Configuration
include(CMakePackageConfigHelpers)

# Generate the config file
configure_package_config_file(
  "${CMAKE_SOURCE_DIR}/cmake/SaltsNetConfig.cmake.in"
  "${CMAKE_BINARY_DIR}/SaltsNetConfig.cmake"
  INSTALL_DESTINATION "lib/cmake/SaltsNet")
configure_file(cmake/SaltsNetDependencies.cmake SaltsNetDependencies.cmake COPYONLY)

# Generate the version file
write_basic_package_version_file(
  "${CMAKE_BINARY_DIR}/SaltsNetConfigVersion.cmake"
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY AnyNewerVersion)

# Install the config files
install(FILES "${CMAKE_BINARY_DIR}/SaltsNetConfig.cmake"
              "${CMAKE_BINARY_DIR}/SaltsNetConfigVersion.cmake"
              "${CMAKE_CURRENT_SOURCE_DIR}/cmake/SaltsNetDependencies.cmake"
        DESTINATION "lib/cmake/SaltsNet")

# Install the export set
export(
  EXPORT SaltsNetTargets
  FILE "${CMAKE_BINARY_DIR}/SaltsNetTargets.cmake"
  NAMESPACE SaltsNet::)

install(
  EXPORT SaltsNetTargets
  FILE SaltsNetTargets.cmake
  NAMESPACE SaltsNet::
  DESTINATION "lib/cmake/SaltsNet")
