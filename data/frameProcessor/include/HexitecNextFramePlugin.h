/*
 * HexitecNextFramePlugin.h
 *
 *  Created on: 18 Sept 2018
 *      Author: ckd27546
 */

#ifndef INCLUDE_HEXITECNEXTFRAMEPLUGIN_H_
#define INCLUDE_HEXITECNEXTFRAMEPLUGIN_H_

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;

#include <string>

#include "FrameProcessorPlugin.h"
#include "HexitecDefinitions.h"
#include "ClassLoader.h"
///
#include <fstream>
#include <sstream>
#include <string.h>

namespace FrameProcessor
{

  /** NextFrame Corrector for future Hexitec Frame objects.
   *
   * If the same pixel is hit in previous, current frames, clear pixel in current frame.
   */
  class HexitecNextFramePlugin : public FrameProcessorPlugin
  {
  public:
    HexitecNextFramePlugin();
    virtual ~HexitecNextFramePlugin();

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
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;
    /** Configuration constant for maximum columns **/
    static const std::string CONFIG_MAX_COLS;
    /** Configuration constant for maximum rows **/
		static const std::string CONFIG_MAX_ROWS;

    void process_frame(boost::shared_ptr<Frame> frame);
    void apply_algorithm(float *in);

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Image width **/
    int image_width_;
    /** Image height **/
    int image_height_;
    /** Image pixel count **/
    int image_pixels_;
    /** Keep a copy of previous data frame **/
    float *last_frame_;

    long long last_frame_number_;
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
  REGISTER(FrameProcessorPlugin, HexitecNextFramePlugin, "HexitecNextFramePlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECNEXTFRAMEPLUGIN_H_ */
