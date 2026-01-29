/*
 * HexitecSummedImagePlugin.h
 *
 *  Created on: 11 Jan 2021
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_HEXITECSUMMEDIMAGEPLUGIN_H_
#define INCLUDE_HEXITECSUMMEDIMAGEPLUGIN_H_

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

  /** Calculate hit pixels across collected frames.
   *
   * The class sums pixels falling between lower, upper thresholds
   * across the collected images.
   */
  class HexitecSummedImagePlugin : public FrameProcessorPlugin
  {
    public:
      HexitecSummedImagePlugin();
      virtual ~HexitecSummedImagePlugin();

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
      static const std::string CONFIG_THRESHOLD_LOWER;
      static const std::string CONFIG_THRESHOLD_UPPER;
      static const std::string CONFIG_IMAGE_FREQUENCY;
      static const std::string CONFIG_FRAMES_PROCESSED;
      static const std::string CONFIG_RESET_IMAGE;
      static const std::string CONFIG_RANK_INDEX;
      static const std::string CONFIG_RANK_OFFSET;

      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      HexitecSensorLayoutMap sensors_layout_;

      void process_end_of_acquisition();
      void process_frame(boost::shared_ptr<Frame> frame);
      void apply_summed_image_algorithm(float *in, uint32_t *out);

      boost::shared_ptr<Frame> summed_image_;
      /** Pointer to logger **/
      LoggerPtr logger_;
      /** Image width **/
      int image_width_;
      /** Image height **/
      int image_height_;
      /** Image pixel count **/
      int image_pixels_;
      /** Count number of frames processed **/
      int frames_processed_;

      // uint32_t *summed_image_;
      int threshold_lower_;
      int threshold_upper_;
      int image_frequency_;
      int reset_image_;
      int rank_index_;
      int rank_offset_;
      uint64_t processed_frame_number_;
      int frames_per_trigger_;
      bool start_of_acquisition_;

      void reset_frames_numbering();
      void initialise_summed_image();
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecSummedImagePlugin, "HexitecSummedImagePlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECSUMMEDIMAGEPLUGIN_H_ */
