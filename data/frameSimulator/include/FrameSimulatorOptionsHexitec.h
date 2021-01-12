#ifndef FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H
#define FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H

#include "FrameSimulatorOption.h"
#include <string>

namespace FrameSimulator {

    static const std::string default_image_pattern_path = "";

    static const FrameSimulatorOption<std::string> opt_image_pattern_json("pattern-path", "Path to the json file that defines the pattern for simulated frames");
}

#endif // FRAMESIMULATOR_FRAMESIMULATOROPTIONHEXITEC_H