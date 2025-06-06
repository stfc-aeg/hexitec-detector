/*
 * HexitecThresholdPlugin.h
 *
 *  Created on: 11 Jul 2018
 *      Author: Christian Angelsen
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
///
#include <boost/algorithm/string.hpp>
#include <map>

namespace FrameProcessor
{
  typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

  enum ThresholdMode {NONE, SINGLE_VALUE, THRESHOLD_FILE};

  /** Processing of Hexitec Frame objects.
   *
   * The HexitecThresholdPlugin class receives Frame objects
   * and reorders the data into valid Hexitec frames.
   */
  class HexitecThresholdPlugin : public FrameProcessorPlugin
  {
    public:
      HexitecThresholdPlugin();
      virtual ~HexitecThresholdPlugin();

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
      /** Configuration constant for threshold mode **/
      static const std::string CONFIG_THRESHOLD_MODE;
      /** Configuration constant for threshold value **/
      static const std::string CONFIG_THRESHOLD_VALUE;
      /** Configuration constant for threshold file **/
      static const std::string CONFIG_THRESHOLD_FILE;
      /** Configuration constant for Hardware sensors **/
      static const std::string CONFIG_SENSORS_LAYOUT;
      /** Configuration constant for Occupancy calculations */
      static const std::string CONFIG_EVENTS_IN_FRAMES;
      static const std::string CONFIG_RESET_OCCUPANCY;
      static const std::string CONFIG_FRAME_OCCUPANCY;

      void process_frame(boost::shared_ptr<Frame> frame);
      std::size_t thresholded_image_size();

      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      HexitecSensorLayoutMap sensors_layout_;

      /** Pointer to logger **/
      LoggerPtr logger_;
      /** Image width **/
      int image_width_;
      /** Image height **/
      int image_height_;
      /** Image pixel count **/
      int image_pixels_;

      void process_threshold_none(float *in);
      void process_threshold_value(float *in);
      void process_threshold_file(float *in);
      bool get_data(const char *filename, uint16_t default_value);
      bool set_threshold_per_pixel(const char *threshold_filename);
      std::string determineThresholdMode(int mode);

      void reset_threshold_values();

      // Member variables:
      unsigned int threshold_value_;
      uint16_t *threshold_per_pixel_;
      bool thresholds_status_;
      ThresholdMode threshold_mode_;
      std::string threshold_filename_;
      uint64_t buffer_events_;
      unsigned long events_in_frames_;
      unsigned long frames_processed_;
      double average_frame_occupancy_;
      unsigned int reset_occupancy_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecThresholdPlugin, "HexitecThresholdPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECTHRESHOLDPLUGIN_H_ */
