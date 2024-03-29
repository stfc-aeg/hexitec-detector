/*
 * HexitecNextFramePlugin.h
 *
 *  Created on: 18 Sept 2018
 *      Author: Christian Angelsen
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
#include <boost/algorithm/string.hpp>
#include <map>

namespace FrameProcessor
{
  typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

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
      /** Configuration constant for Hardware sensors **/
      static const std::string CONFIG_SENSORS_LAYOUT;

      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      HexitecSensorLayoutMap sensors_layout_;

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
      void reset_last_frame_values();
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecNextFramePlugin, "HexitecNextFramePlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECNEXTFRAMEPLUGIN_H_ */
