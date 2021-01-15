#ifndef FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H
#define FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H

#include "FrameSimulatorOption.h"
#include <string>

namespace FrameSimulator {

    static const std::string default_image_pattern_path = "";

    static const FrameSimulatorOption<std::string> opt_image_pattern_json("pattern-path", "Path to the json file that defines the pattern for simulated frames");

    static const FrameSimulatorOption<std::string> opt_sensors_layout("sensors_layout", "Sensors' layout, such as 2x2 or 2x6");
}

#endif // FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H