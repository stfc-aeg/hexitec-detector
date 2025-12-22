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

  typedef struct
  {
    uint64_t trigger_number;
    std::set<uint64_t> frames_received;
    boost::shared_ptr<Frame> stacked_frame_;
  } TriggerObject;

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

      bool first_frame_of_trigger(int target);
      bool trigger_already_processed(int target);
      bool frame_already_received(TriggerObject* trigger_object, int frame_number);
      int get_number_of_frames_received(TriggerObject* trigger_object);
      TriggerObject* get_trigger_object(int trigger_number);
      bool erase_trigger_object(int trigger_number);
      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      HexitecSensorLayoutMap sensors_layout_;

      void process_end_of_acquisition();
      void process_frame(boost::shared_ptr<Frame> frame);

      /** Pointer to logger **/
      LoggerPtr logger_;
      int image_width_;
      int image_height_;
      int image_pixels_;
      /** Rank index, differentiate each histogram if multiple frame processors **/
      int rank_index_;
      int rank_offset_;
      int frames_per_trigger_;
      uint64_t frames_processed_;

      void initialise_stacked_frame(TriggerObject* trigger_object);
      void stack_current_frame(float *in, float *out);
      // Arrays to track triggers received, processed and incomplete
      rapidjson::Value triggers_received_;
      rapidjson::Value triggers_processed_;
      rapidjson::Value triggers_incomplete_;
      rapidjson::Value::AllocatorType triggers_received_allocator_;
      rapidjson::Value::AllocatorType triggers_processed_allocator_;
      rapidjson::Value::AllocatorType triggers_incomplete_allocator_;
      std::vector<TriggerObject> trigger_objects_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecStackedPlugin, "HexitecStackedPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECSTACKEDPLUGIN_H_ */
