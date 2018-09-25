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

#define FEM_PIXELS_PER_ROW 80
#define FEM_PIXELS_PER_COLUMN 80
#define FEM_TOTAL_PIXELS (FEM_PIXELS_PER_ROW * FEM_PIXELS_PER_COLUMN)

namespace FrameProcessor
{

  /** Calibration of Hexitec Frame objects.
   *
   * This service of the template for all of the remaining hexitec plug-ins to be written.
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

  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecCalibrationPlugin, "HexitecCalibrationPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECCALIBRATIONPLUGIN_H_ */
