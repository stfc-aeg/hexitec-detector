#ifndef FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H
#define FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H

#include "FrameSimulatorOption.h"
#include <string>

namespace FrameSimulator {

    static const std::string default_image_pattern_path = "";
    static const std::string default_hdf_file_path = "";
    static const std::string default_hdf_dataset = "/data";

    static const FrameSimulatorOption<std::string> opt_image_pattern_json("pattern-path", "Path to the json file that defines the pattern for simulated frames");
    static const FrameSimulatorOption<std::string> opt_hdf_file_path("hdf-path", "Path to the HDF5 file containing HEXITEC frames");
    static const FrameSimulatorOption<std::string> opt_hdf_dataset("hdf-dataset", "Dataset within the HDF5 file containing HEXITEC frames");
    static const FrameSimulatorOption<unsigned int> opt_hdf_frames("hdf-frames", "Number of frames to read from the HDF5 dataset (default: all frames)");
    static const FrameSimulatorOption<std::string> opt_sensor_layout("sensor-layout", "Sensor layout, such as 2x2 or 2x6");
}

#endif // FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H
