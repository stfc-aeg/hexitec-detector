/*
 * HexitecProcessPlugin.h
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#ifndef INCLUDE_HEXITECPROCESSPLUGIN_H_
#define INCLUDE_HEXITECPROCESSPLUGIN_H_

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;


#include "FrameProcessorPlugin.h"
#include "HexitecDefinitions.h"
#include "ClassLoader.h"

#define FEM_PIXELS_PER_ROW 80
#define FEM_PIXELS_PER_COLUMN 80
#define FEM_TOTAL_PIXELS (FEM_PIXELS_PER_ROW * FEM_PIXELS_PER_COLUMN)

namespace FrameProcessor
{

  /** Processing of Hexitec Frame objects.
   *
   * The HexitecProcessPlugin class receives a raw data Frame object,
   * reorders the pixels and stores the data as an array of floats.
   */
  class HexitecProcessPlugin : public FrameProcessorPlugin
  {
  public:
    HexitecProcessPlugin();
    virtual ~HexitecProcessPlugin();
    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);

  private:
    /** Configuration constant for clearing out dropped packet counters **/
    static const std::string CONFIG_DROPPED_PACKETS;
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;

    void process_lost_packets(boost::shared_ptr<Frame> frame);
    void process_frame(boost::shared_ptr<Frame> frame);
    // Float type array version currently used:
    void reorder_pixels(unsigned short* in, float* out);
    // Convert pixel data from unsigned short to float data type
    void convert_pixels_to_float(unsigned short* in, float* out);

    std::size_t reordered_image_size();

    void initialisePixelMap();
    uint16_t pixelMap[6400];
    bool pixelMapInitialised;

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

    /* DEVELOPMENT SPACE - for the other plug-ins' functionalities */


  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecProcessPlugin, "HexitecProcessPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECPROCESSPLUGIN_H_ */
