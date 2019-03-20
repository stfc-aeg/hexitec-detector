/*
 * HexitecAdditionPlugin.h
 *
 *  Created on: 08 Aug 2018
 *      Author: ckd27546
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

namespace FrameProcessor
{

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
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;
    /** Configuration constant for pixel_grid_size **/
    static const std::string CONFIG_PIXEL_GRID_SIZE;
    /** Configuration constant for maximum columns **/
    static const std::string CONFIG_MAX_COLS;
    /** Configuration constant for maximum rows **/
		static const std::string CONFIG_MAX_ROWS;

    void process_frame(boost::shared_ptr<Frame> frame);
    std::size_t processed_image_size();

    void prepare_charged_sharing(float *input_frame, float *output_frame);
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
    int fem_pixels_per_rows_;
    int fem_pixels_per_columns_;
    int fem_total_pixels_;

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
