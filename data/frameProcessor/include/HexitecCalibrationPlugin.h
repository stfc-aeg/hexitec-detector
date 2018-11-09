/*
 * HexitecCalibrationPlugin.h
 *
 *  Created on: 24 Sept 2018
 *      Author: ckd27546
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

#define FEM_PIXELS_PER_ROW 80
#define FEM_PIXELS_PER_COLUMN 80
#define FEM_TOTAL_PIXELS (FEM_PIXELS_PER_ROW * FEM_PIXELS_PER_COLUMN)

namespace FrameProcessor
{

  /** Calibration of Hexitec Frame objects.
   *
   * This plugin takes a gradients and an intercepts file and calibrates each pixel.
   */
  class HexitecCalibrationPlugin : public FrameProcessorPlugin
  {
  public:
    HexitecCalibrationPlugin();
    virtual ~HexitecCalibrationPlugin();
    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);

  private:
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;
    /** Configuration constant for Gradients **/
    static const std::string CONFIG_GRADIENTS_FILE;
    /** Configuration constant for Intercepts **/
    static const std::string CONFIG_INTERCEPTS_FILE;
    /** Configuration constant for maximum columns **/
    static const std::string CONFIG_MAX_COLS;
    /** Configuration constant for maximum rows **/
		static const std::string CONFIG_MAX_ROWS;

    void process_frame(boost::shared_ptr<Frame> frame);
    void calibrate_pixels(float* in, float* out);

    std::size_t calibrated_image_size();

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Image width **/
    int image_width_;
    /** Image height **/
    int image_height_;
    /** Image pixel count **/
    int image_pixels_;

    int frameSize;
    bool gradientsStatus;
    bool interceptsStatus;
    float *gradientValue;
    float *interceptValue;
    void setGradients(const char *gradientFilename);
    void setIntercepts(const char *interceptFilename);
    bool getData(const char *filename, float *dataValue, float defaultValue);

    int fem_pixels_per_rows_;
    int fem_pixels_per_columns_;
    int fem_total_pixels_;

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
