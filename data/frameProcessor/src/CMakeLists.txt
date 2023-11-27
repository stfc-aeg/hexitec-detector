
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)

include_directories(${FRAMEPROCESSOR_DIR}/include ${ODINDATA_INCLUDE_DIRS}
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Add library for hexitec plugin
add_library(HexitecReorderPlugin SHARED HexitecReorderPlugin.cpp)
add_library(HexitecThresholdPlugin SHARED HexitecThresholdPlugin.cpp)
add_library(HexitecAdditionPlugin SHARED HexitecAdditionPlugin.cpp)
add_library(HexitecDiscriminationPlugin SHARED HexitecDiscriminationPlugin.cpp)
add_library(HexitecHistogramPlugin SHARED HexitecHistogramPlugin.cpp)
add_library(HexitecCalibrationPlugin SHARED HexitecCalibrationPlugin.cpp)
add_library(HexitecSummedImagePlugin SHARED HexitecSummedImagePlugin.cpp)

install(TARGETS HexitecReorderPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecThresholdPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecAdditionPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecDiscriminationPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecHistogramPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecCalibrationPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecSummedImagePlugin LIBRARY DESTINATION lib)
