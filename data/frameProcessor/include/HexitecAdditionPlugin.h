/*
 * HexitecAdditionPlugin.h
 *
 *  Created on: 08 Aug 2018
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_HEXITECADDITIONPLUGIN_H_
#define INCLUDE_HEXITECADDITIONPLUGIN_H_

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
#include <string.h>
#include <boost/algorithm/string.hpp>
#include <map>

namespace FrameProcessor
{
  typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

  /** Applies the Charged Sharing algorithm to a Hexitec frame.
   *
   * The HexitecAdditionPlugin examines surrounding neighbouring pixels
   * moving any event shared across multiple pixels onto the pixel containing
   * the biggest portion of that event.
   */
  class HexitecAdditionPlugin : public FrameProcessorPlugin
  {
    public:
      HexitecAdditionPlugin();
      virtual ~HexitecAdditionPlugin();

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
      /** Configuration constant for pixel_grid_size **/
      static const std::string CONFIG_PIXEL_GRID_SIZE;
      /** Configuration constant for Hardware sensors **/
      static const std::string CONFIG_SENSORS_LAYOUT;

      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      HexitecSensorLayoutMap sensors_layout_;

      void process_frame(boost::shared_ptr<Frame> frame);

      void prepare_charged_sharing(float *input_frame);
      void process_addition(float *extended_frame, int extended_frame_rows,
                            int start_position, int end_position);

      int directional_distance_;
      int number_rows_;
      int number_columns_;

      /** Pointer to logger **/
      LoggerPtr logger_;
      /** Image width **/
      int image_width_;
      /** Image height **/
      int image_height_;
      /** Image pixel count **/
      int image_pixels_;

      /** Pixel grid size */
      int pixel_grid_size_;

      // DEBUGGING functions:
      void print_nonzero_pixels(float *in, int numberRows, int numberColumns);
      void check_memory(float *float_pointer, int offset);
      void print_last_row(float *in, int numberRows, int numberCols);
      int debugFrameCounter;
      std::ofstream outFile;
      void writeFile(std::string filePrefix, float *frame);
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecAdditionPlugin, "HexitecAdditionPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECADDITIONPLUGIN_H_ */
