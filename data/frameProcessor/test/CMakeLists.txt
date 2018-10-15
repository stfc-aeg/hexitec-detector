
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)
ADD_DEFINITIONS(-DBUILD_DIR="${CMAKE_BINARY_DIR}")

include_directories(${FRAMEPROCESSOR_DIR}/include ${ODINDATA_INCLUDE_DIRS} 
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Build list of test source files from current dir
file(GLOB TEST_SOURCES *.cpp)

# Add test and project source files to executable
add_executable(hexitecFrameProcessorTest ${TEST_SOURCES})

if ( ${CMAKE_SYSTEM_NAME} MATCHES Linux )
# librt required for timing functions
find_library(REALTIME_LIBRARY 
		NAMES rt)
target_link_libraries( hexitecFrameProcessorTest ${REALTIME_LIBRARY} )
endif()

# Define libraries to link against
target_link_libraries(hexitecFrameProcessorTest
	    HexitecReorderPlugin
		${ODINDATA_LIBRARIES} 
		${Boost_LIBRARIES}
		${LOG4CXX_LIBRARIES}
		${ZEROMQ_LIBRARIES}) 
