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

#define FEM_PIXELS_PER_ROW 80
#define FEM_PIXELS_PER_COLUMN 80
#define FEM_TOTAL_PIXELS (FEM_PIXELS_PER_ROW * FEM_PIXELS_PER_COLUMN)

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
    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);

  private:
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;
    /** Configuration constant for pixel_grid_size **/
    static const std::string CONFIG_PIXEL_GRID_SIZE;

    void process_frame(boost::shared_ptr<Frame> frame);
    std::size_t processed_image_size();

    void prepareChargedSharing(float *inFrame, float *outFrame);
    void processAddition(float *extendedFrame, int extendedFrameRows,
    										 int startPosn, int endPosn);

    int directionalDistance;
    int nRows;
    int nCols;

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Image width **/
    int image_width_;
    /** Image height **/
    int image_height_;
    /** Image pixel count **/
    int image_pixels_;

    /** Pixel grid size */
    int pixelGridSize;

    // DEBUGGING functions:
    void print_nonzero_pixels(float *in, int numberRows, int numberColumns);
    void check_memory(float *float_pointer, int offset);
    void print_last_row(float *in, int numberRows, int numberCols);

  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecAdditionPlugin, "HexitecAdditionPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECADDITIONPLUGIN_H_ */
