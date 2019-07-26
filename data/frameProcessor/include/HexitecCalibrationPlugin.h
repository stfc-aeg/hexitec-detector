/*
 * HexitecCalibrationPlugin.h
 *
 *  Created on: 24 Sept 2018
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_HEXITECCALIBRATIONPLUGIN_H_
#define INCLUDE_HEXITECCALIBRATIONPLUGIN_H_

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;


#include "FrameProcessorPlugin.h"
#include "HexitecDefinitions.h"
#include "ClassLoader.h"

#include <iostream>
#include <fstream>
///
#include <fstream>
#include <sstream>
#include <string.h>
#include <boost/algorithm/string.hpp>
#include <map>

namespace FrameProcessor
{

  typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

  /** Calibration of Hexitec Frame objects.
   *
   * This plugin takes a gradients and an intercepts file and calibrates each pixel.
   */
  class HexitecCalibrationPlugin : public FrameProcessorPlugin
  {
  public:
    HexitecCalibrationPlugin();
    virtual ~HexitecCalibrationPlugin();

    int get_version_major();
    int get_version_minor();
    int get_version_patch();
    std::string get_version_short();
    std::string get_version_long();

    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void requestConfiguration(OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);
    bool reset_statistics(void);

  private:
    /** Configuration constant for Gradients **/
    static const std::string CONFIG_GRADIENTS_FILE;
    /** Configuration constant for Intercepts **/
    static const std::string CONFIG_INTERCEPTS_FILE;
		/** Configuration constant for Hardware sensors **/
		static const std::string CONFIG_SENSORS_LAYOUT;

    std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
    std::string sensors_layout_str_;
    HexitecSensorLayoutMap sensors_layout_;

    void process_frame(boost::shared_ptr<Frame> frame);
    void calibrate_pixels(float *image);

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Image width **/
    int image_width_;
    /** Image height **/
    int image_height_;
    /** Image pixel count **/
    int image_pixels_;

    bool gradients_status_;
    bool intercepts_status_;
    float *gradient_values_;
    float *intercept_values_;
    void setGradients(const char *gradientFilename);
    void setIntercepts(const char *interceptFilename);
    bool getData(const char *filename, float *dataValue, float defaultValue);

    std::string gradients_filename_;
    std::string intercepts_filename_;

    void reset_calibration_values();

    // DEBUGGING functions:
    int debugFrameCounter;
    std::ofstream outFile;
  	void writeFile(std::string filePrefix, float *frame);
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecCalibrationPlugin, "HexitecCalibrationPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECCALIBRATIONPLUGIN_H_ */
