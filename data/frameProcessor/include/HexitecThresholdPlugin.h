/*
 * HexitecThresholdPlugin.h
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#ifndef INCLUDE_HEXITECTHRESHOLDPLUGIN_H_
#define INCLUDE_HEXITECTHRESHOLDPLUGIN_H_

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

  /** Processing of Hexitec Frame objects.
   *
   * The HexitecThresholdPlugin class is currently responsible for receiving a raw data
   * Frame object and reordering the data into valid Hexitec frames according to the selected
   * bit depth.
   */
  class HexitecThresholdPlugin : public FrameProcessorPlugin
  {
  public:
    HexitecThresholdPlugin();
    virtual ~HexitecThresholdPlugin();
    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);

  private:
    /** Configuration constant for clearing out dropped packet counters **/
    static const std::string CONFIG_DROPPED_PACKETS;
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;

    void process_frame(boost::shared_ptr<Frame> frame);
    std::size_t thresholded_image_size();

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Image width **/
    int image_width_;
    /** Image height **/
    int image_height_;
    /** Image pixel count **/
    int image_pixels_;
    /** Packet loss counter **/
    int packets_lost_;

    void processThresholdValue(unsigned short* in, unsigned short* out);
    void processThresholdFile(unsigned short* in, unsigned short* out);
    bool getData(const char *filename, uint16_t defaultValue);
    bool setThresholdPerPixel(const char * thresholdFilename);

    // Member variables:
    bool bThresholdsFromFile;
    unsigned int thresholdValue;
    uint16_t *thresholdPerPixel;
    bool thresholdsStatus;


  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecThresholdPlugin, "HexitecThresholdPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECTHRESHOLDPLUGIN_H_ */
