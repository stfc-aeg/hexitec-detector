
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)

include_directories(${FRAMESIMULATOR_DIR}/include ${ODINDATA_INCLUDE_DIRS}
	${BOOST_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS} ${PCAP_INCLUDE_DIR})

file(GLOB LIB_SOURCES HexitecFrameSimulatorPlugin.cpp HexitecFrame.cpp)

# Add library for Hexitec plugin
add_library(HexitecFrameSimulatorPlugin SHARED ${LIB_SOURCES})

target_link_libraries(HexitecFrameSimulatorPlugin ${PCAP_LIBRARY})

install(TARGETS HexitecFrameSimulatorPlugin LIBRARY DESTINATION lib)
