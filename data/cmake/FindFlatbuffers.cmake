message("\nLooking for flatbuffers headers and libraries")

if (FLATBUFFERS_ROOT_DIR)
    message (STATUS "Flatbuffers Root Dir: ${FLATBUFFERS_ROOT_DIR}")
endif ()

if (FLATBUFFERS_ROOT_DIR)
    find_path(
        FLATBUFFERS_INCLUDE_DIR flatbuffers
        PATHS ${FLATBUFFERS_ROOT_DIR}/include
        NO_DEFAULT_PATH
    )
else()
    find_path(FLATBUFFERS_INCLUDE_DIR flatbuffers)
endif()

if (FLATBUFFERS_ROOT_DIR)
    find_library(
        FLATBUFFERS_LIBRARIES NAMES flatbuffers
        PATHS ${FLATBUFFERS_ROOT_DIR}/lib
        NO_DEFAULT_PATH
    )
else()
    find_library(FLATBUFFERS_LIBRARIES NAMES flatbuffers)
endif()

if (FLATBUFFERS_LIBRARIES AND FLATBUFFERS_INCLUDE_DIR)
    set(FLATBUFFERS_FOUND TRUE)
else()
    set(FLATBUFFERS_FOUND FALSE)
endif()
if (${FLATBUFFERS_FOUND})
    message(STATUS "Found Flatbuffers: ${FLATBUFFERS_LIBRARIES}")
else()
    message(STATUS "Could not find the Flatbuffers library.")
endif()
