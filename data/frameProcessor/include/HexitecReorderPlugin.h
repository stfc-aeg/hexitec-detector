/*
 * HexitecReorderPlugin.h
 *
 *  Created on: 11 Jul 2018
 *      Author: Christian Angelsen
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
#include "DataBlockFrame.h"
///
#include <fstream>
#include <sstream>
#include <map>

#define ILLEGAL_FEM_IDX -1

const std::string default_fem_port_map = "61651:0";
const std::string default_sensors_layout_map = "1x1";

namespace FrameProcessor
{

  typedef struct HexitecSensorLayoutMapEntry
  {
    int sensor_rows_;
    int sensor_columns_;

    HexitecSensorLayoutMapEntry(int sensor_rows=ILLEGAL_FEM_IDX, int sensor_columns=ILLEGAL_FEM_IDX) :
      sensor_rows_(sensor_rows),
      sensor_columns_(sensor_columns)
    {};
  } HexitecSensorLayoutMapEntry;

  typedef std::map<int, HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;
//
//  typedef struct HexitecReorderSensorMapEntry
//  {
//    unsigned int sensor_rows_;
//    unsigned int sensor_columns_;
//
//    HexitecReorderSensorMapEntry(int sensor_rows=ILLEGAL_FEM_IDX, int sensor_columns=ILLEGAL_FEM_IDX) :
//      sensor_rows_(sensor_rows),
//      sensor_columns_(sensor_columns)
//    {};
//  } HexitecReorderSensorMapEntry;
//
//  typedef std::map<int, HexitecReorderSensorMapEntry> HexitecReorderSensorMap;

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

    int get_version_major();
    int get_version_minor();
    int get_version_patch();
    std::string get_version_short();
    std::string get_version_long();

    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void requestConfiguration(OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);
    bool reset_statistics();

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
		/** Configuration constant for Hardware sensors **/
		static const std::string CONFIG_SENSORS_LAYOUT;

    void process_lost_packets(boost::shared_ptr<Frame>& frame);
    void process_frame(boost::shared_ptr<Frame> frame);
    // Float type array version currently used:
    void reorder_pixels(unsigned short *in, float *out);
    // Convert pixels from unsigned short to float type without reordering
    void convert_pixels_without_reordering(unsigned short *in,
														 							 float *out);

    std::size_t reordered_image_size();
    std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
    std::string sensors_layout_str_;
    HexitecSensorLayoutMap sensors_layout_;

    void initialisePixelMap();
    uint16_t pixelMap[6400];
    bool pixelMapInitialised;
    bool reorder_pixels_;
    bool write_raw_data_;

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Config of sensor(s) **/
    int sensors_config_;
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
