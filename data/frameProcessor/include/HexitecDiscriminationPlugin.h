/*
 * HexitecDiscriminationPlugin.h
 *
 *  Created on: 08 Aug 2018
 *      Author: Christian Angelsen
 */

#ifndef INCLUDE_HEXITECDISCRIMINATIONPLUGIN_H_
#define INCLUDE_HEXITECDISCRIMINATIONPLUGIN_H_

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
#include <boost/algorithm/string.hpp>
#include <map>

namespace FrameProcessor
{
  typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

  /** Implements Discrimination algorithm on Hexitec Frame objects.
   *
   * If any hit pixel have any neighbour(s) with hits, clear all hit pixels.
   */
  class HexitecDiscriminationPlugin : public FrameProcessorPlugin
  {
  public:
    HexitecDiscriminationPlugin();
    virtual ~HexitecDiscriminationPlugin();

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
    /** Configuration constant for pixel grid size **/
    static const std::string CONFIG_PIXEL_GRID_SIZE;
		/** Configuration constant for Hardware sensors **/
		static const std::string CONFIG_SENSORS_LAYOUT;

    void process_frame(boost::shared_ptr<Frame> frame);

    void prepareChargedSharing(float *inFrame);
    void processDiscrimination(float *extendedFrame, int extendedFrameRows,
                               int startPosn, int endPosn);

    std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
    std::string sensors_layout_str_;
    HexitecSensorLayoutMap sensors_layout_;

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

    int pixel_grid_size_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecDiscriminationPlugin, "HexitecDiscriminationPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECDISCRIMINATIONPLUGIN_H_ */
