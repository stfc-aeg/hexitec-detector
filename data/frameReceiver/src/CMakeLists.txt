
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBUILD_DIR="${CMAKE_BINARY_DIR}")

include_directories(${FRAMERECEIVER_DIR}/include ${ODINDATA_INCLUDE_DIRS} 
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Add library for Hexitec frame decoder
add_library(HexitecFrameDecoder SHARED HexitecFrameDecoder.cpp HexitecFrameDecoderLib.cpp)

install(TARGETS HexitecFrameDecoder LIBRARY DESTINATION lib)