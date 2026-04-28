# Project name
project(HEXITEC)

# Require CMake version >=2.8.12
cmake_minimum_required(VERSION 2.8.12)

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_CONFIG_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/test_config)

# Set the common directory
set(COMMON_DIR ${HEXITEC_SOURCE_DIR}/common)

# Set the frameReceiver directory
set(FRAMERECEIVER_DIR ${HEXITEC_SOURCE_DIR}/frameReceiver)

# Set the frameProcessor directory
set(FRAMEPROCESSOR_DIR ${HEXITEC_SOURCE_DIR}/frameProcessor)

# Set the frameSimulator directory
set(FRAMESIMULATOR_DIR ${HEXITEC_SOURCE_DIR}/frameSimulator)

# Set the integrationTest directory
set(TEST_DIR ${HEXITEC_SOURCE_DIR}/test)

# Appends the cmake/modules path inside the MAKE_MODULE_PATH variable which stores the
# directories of additional CMake modules (ie. MacroOutOfSourceBuild.cmake):
set(CMAKE_MODULE_PATH ${HEXITEC_SOURCE_DIR}/cmake ${CMAKE_MODULE_PATH})

# If the odin-data root installation directory has been specified add the cmake path to allow
# installed cmake finders to be used
if (DEFINED ODINDATA_ROOT_DIR)
        set(CMAKE_MODULE_PATH ${ODINDATA_ROOT_DIR}/cmake ${CMAKE_MODULE_PATH})
endif()

# Allow macOS shared (dynamic) libraries to link with undefined symbols
if (APPLE)
	message("Allowing undefined symbols in macOS shared library linking")
    set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -undefined dynamic_lookup")
endif(APPLE)

# Find and add external packages required for application and test
find_package( Boost 1.41.0
	      REQUIRED
	      COMPONENTS program_options system filesystem unit_test_framework date_time thread)
find_package(LOG4CXX 0.10.0 REQUIRED)
find_package(ZEROMQ 3.2.4 REQUIRED)
find_package(ODINDATA REQUIRED)
find_package(Kafka)
find_package(Flatbuffers)


# Check if Boost version has placeholders and set definition accordingly
message("\nChecking Boost version placeholder support")
if (NOT DEFINED Boost_VERSION_STRING)
  set(Boost_VERSION_STRING "${Boost_MAJOR_VERSION}.${Boost_MINOR_VERSION}.${Boost_SUBMINOR_VERSION}")
endif ()
if ((Boost_VERSION_STRING EQUAL 1.60.0) OR (Boost_VERSION_STRING GREATER 1.60.0))
  message(STATUS "Boost version ${Boost_VERSION_STRING} has placeholders")
  ADD_DEFINITIONS(-DBOOST_HAS_PLACEHOLDERS)
else ()
  message(STATUS "Boost version ${Boost_VERSION_STRING} does not have placeholders")
endif ()

message("Determining hexitec-detector version")
include(GetGitRevisionDescription)
git_describe(GIT_DESC_STR)

string(REGEX REPLACE "^([0-9]+)[\\.-].*" "\\1" VERSION_MAJOR "${GIT_DESC_STR}")
string(REGEX REPLACE "^[0-9]+[\\.-]([0-9]+).*" "\\1" VERSION_MINOR "${GIT_DESC_STR}")
string(REGEX REPLACE "^[0-9]+[\\.-][0-9]+[\\.-]([0-9]+).*" "\\1" VERSION_PATCH "${GIT_DESC_STR}")
string(REGEX REPLACE "^[0-9]+[\\.-][0-9]+[\\.-][0-9]+-[0-9]+-(.*)" "\\1" VERSION_SHA1 "${GIT_DESC_STR}")

set(VERSION_SHORT "${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH}")
set(VERSION_STR ${GIT_DESC_STR})
message("-- Git describe version: ${GIT_DESC_STR}")
message("-- major:${VERSION_MAJOR} minor:${VERSION_MINOR} patch:${VERSION_PATCH} sha1:${VERSION_SHA1}")
message("-- short version: ${VERSION_SHORT}")

configure_file(${COMMON_DIR}/include/version.h.in "${CMAKE_BINARY_DIR}/include/version.h")
include_directories(${CMAKE_BINARY_DIR}/include)

# Add common/include directory to include path
include_directories(${COMMON_DIR}/include)

# Add the frameReceiver subdirectory
add_subdirectory(${FRAMERECEIVER_DIR})

# Add the frameProcessor subdirectory
add_subdirectory(${FRAMEPROCESSOR_DIR})

# Add the frameSimulator subdirectory
add_subdirectory(${FRAMESIMULATOR_DIR})

# Add the integrationTest subdirectory
add_subdirectory(${TEST_DIR})

# Add the doc subdirectory
#add_subdirectory(doc)

# Add the config subdirectory (config files used for integration testing)
add_subdirectory(config)

