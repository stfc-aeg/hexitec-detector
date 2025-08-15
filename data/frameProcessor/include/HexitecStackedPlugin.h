/*
 * HexitecStackedPlugin.h
 *
 *  Created on: 11 Aug 2025
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_HEXITECSTACKEDPLUGIN_H_
#define INCLUDE_HEXITECSTACKEDPLUGIN_H_

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
//
#include <boost/algorithm/string.hpp>
#include <map>

namespace FrameProcessor
{
  typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

  /** Stacks frame(s) for Hexitec Frame objects.
   *
   * The HexitecStackedPlugin will stack the N frames per trigger into one stacked frame.
   */
  class HexitecStackedPlugin : public FrameProcessorPlugin
  {
    public:
      HexitecStackedPlugin();
      virtual ~HexitecStackedPlugin();

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
      /** Configuration constant for rank index **/
      static const std::string CONFIG_RANK_INDEX;
      /** Configuration constant for rank offset **/
      static const std::string CONFIG_RANK_OFFSET;
      /** Configuration constant for frames per trigger */
      static const std::string CONFIG_FRAMES_PER_TRIGGER;

      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      HexitecSensorLayoutMap sensors_layout_;

      void process_end_of_acquisition();
      void process_frame(boost::shared_ptr<Frame> frame);

      boost::shared_ptr<Frame> stacked_frame_;
      /** Pointer to logger **/
      LoggerPtr logger_;
      /** Image width **/
      int image_width_;
      /** Image height **/
      int image_height_;
      /** Image pixel count **/
      int image_pixels_;
      /** Rank index, differentiate each histogram if multiple frame processors **/
      int rank_index_;
      int rank_offset_;
      uint64_t processed_frame_number_;
      int frames_per_trigger_;

      void reset_frames_numbering();
      void initialise_stacked_frame();
      void stack_current_frame(float *in, float *out);
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecStackedPlugin, "HexitecStackedPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECSTACKEDPLUGIN_H_ */
