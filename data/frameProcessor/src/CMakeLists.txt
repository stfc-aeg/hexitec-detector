
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
add_library(HexitecStackedPlugin SHARED HexitecStackedPlugin.cpp)

install(TARGETS HexitecReorderPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecThresholdPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecAdditionPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecDiscriminationPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecHistogramPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecCalibrationPlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecSummedImagePlugin LIBRARY DESTINATION lib)
install(TARGETS HexitecStackedPlugin LIBRARY DESTINATION lib)

if ((${KAFKA_FOUND}) AND (${FLATBUFFERS_FOUND}))
	message("Found Kafka and flatbuffers, building HexitecKafkaPvaPlugin")
    include_directories(${KAFKA_INCLUDE_DIR} ${FLATBUFFERS_INCLUDE_DIR}
        ${FRAMEPROCESSOR_DIR}/include/pva )
    # Add library for HexitecKafkaPvaPlugin plugin
    add_library(HexitecKafkaPvaPlugin SHARED HexitecKafkaPvaPlugin.cpp
        pva/PvaFrameBufferBuilder.cpp
    )
    target_link_libraries(HexitecKafkaPvaPlugin ${KAFKA_LIBRARIES} ${FLATBUFFERS_LIBRARIES})
    install(TARGETS HexitecKafkaPvaPlugin DESTINATION lib)
endif()
