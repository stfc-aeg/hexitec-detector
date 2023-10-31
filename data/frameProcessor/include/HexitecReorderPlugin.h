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
#include <boost/algorithm/string.hpp>
#include <fstream>
#include <map>

const std::string default_fem_port_map = "61651:0";

namespace FrameProcessor
{
  typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

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
      /** Configuration constant for Hardware sensors **/
      static const std::string CONFIG_SENSORS_LAYOUT;
      /** Configuration constant for setting frame number **/
      static const std::string CONFIG_FRAME_NUMBER;
      /** Configuration constant for resetting frame number **/
      static const std::string CONFIG_RESET_FRAME_NUMBER;

      void process_lost_packets(boost::shared_ptr<Frame>& frame);
      void process_frame(boost::shared_ptr<Frame> frame);

      // Float type array version currently used:
      void reorder_pixels(unsigned short *in, float *out);
      // Convert pixels from unsigned short to float type without reordering
      void convert_pixels_without_reordering(unsigned short *in,
                                            float *out);
      void copy_pixels_without_reordering(unsigned short *in, unsigned short *out);

      std::size_t reordered_image_size();
      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      HexitecSensorLayoutMap sensors_layout_;
      // sensors_config_ map number of sensors to frame and packet structures,
      // see HexitecDefinitions.h for more details
      bool set_sensors_config(int sensor_rows, int sensor_columns);

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
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecReorderPlugin, "HexitecReorderPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECREORDERPLUGIN_H_ */
