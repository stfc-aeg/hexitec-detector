/*
 * HexitecReorderPlugin.h
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#ifndef INCLUDE_HEXITECREORDERPLUGIN_H_
#define INCLUDE_HEXITECREORDERPLUGIN_H_

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;


#include "FrameProcessorPlugin.h"
#include "HexitecDefinitions.h"
#include "ClassLoader.h"
///
#include <fstream>
#include <sstream>

#define FEM_PIXELS_PER_ROW 80
#define FEM_PIXELS_PER_COLUMN 80
#define FEM_TOTAL_PIXELS (FEM_PIXELS_PER_ROW * FEM_PIXELS_PER_COLUMN)

namespace FrameProcessor
{

  /** Reorder pixels within Hexitec Frame objects.
   *
   * The HexitecReorderPlugin class receives a raw data Frame object,
   * reorders the pixels and stores the data as an array of floats.
   */
  class HexitecReorderPlugin : public FrameProcessorPlugin
  {
  public:
    HexitecReorderPlugin();
    virtual ~HexitecReorderPlugin();
    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);

  private:
    /** Configuration constant for clearing out dropped packet counters **/
    static const std::string CONFIG_DROPPED_PACKETS;
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;
    /** Configuration constant for enable reorder(ing) **/
		static const std::string CONFIG_ENABLE_REORDER;
    /** Configuration constant for writing raw data (or not) **/
		static const std::string CONFIG_RAW_DATA;
    /** Configuration constant for maximum columns **/
    static const std::string CONFIG_MAX_COLS;
    /** Configuration constant for maximum rows **/
		static const std::string CONFIG_MAX_ROWS;

    void process_lost_packets(boost::shared_ptr<Frame> frame);
    void process_frame(boost::shared_ptr<Frame> frame);
    // Float type array version currently used:
    void reorder_pixels(unsigned short* in, float* out);
    // Convert pixels from unsigned short to float type without reordering
    void convert_pixels_without_reordering(unsigned short* in,
														 							 float* out);

    std::size_t reordered_image_size();

    void initialisePixelMap();
    uint16_t pixelMap[6400];
    bool pixelMapInitialised;
    bool reorder_pixels_;
    bool write_raw_data_;

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

    int fem_pixels_per_rows_;
    int fem_pixels_per_columns_;
    int fem_total_pixels_;

    /// DEBUGGING:
    int debugFrameCounter;
    std::ofstream outFile;
  	void writeFile(std::string filePrefix, float *frame);

  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecReorderPlugin, "HexitecReorderPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECREORDERPLUGIN_H_ */
