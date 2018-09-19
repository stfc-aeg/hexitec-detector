
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)

include_directories(${FRAMEPROCESSOR_DIR}/include ${ODINDATA_INCLUDE_DIRS}
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Add library for hexitec plugin
add_library(HexitecProcessPlugin SHARED HexitecProcessPlugin.cpp)
add_library(HexitecTemplatePlugin SHARED HexitecTemplatePlugin.cpp)
add_library(HexitecThresholdPlugin SHARED HexitecThresholdPlugin.cpp)
add_library(HexitecAdditionPlugin SHARED HexitecAdditionPlugin.cpp)
add_library(HexitecDiscriminationPlugin SHARED HexitecDiscriminationPlugin.cpp)
add_library(HexitecHistogramPlugin SHARED HexitecHistogramPlugin.cpp)
add_library(HexitecNextFramePlugin SHARED HexitecNextFramePlugin.cpp)

install(TARGETS HexitecProcessPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecTemplatePlugin LIBRARY DESTINATION Lib)
install(TARGETS HexitecThresholdPlugin LIBRARY DESTINATION Lib)
install(TARGETS HexitecAdditionPlugin LIBRARY DESTINATION Lib)
install(TARGETS HexitecDiscriminationPlugin LIBRARY DESTINATION Lib)
install(TARGETS HexitecHistogramPlugin LIBRARY DESTINATION Lib)
install(TARGETS HexitecNextFramePlugin LIBRARY DESTINATION Lib)
