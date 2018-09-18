/*
 * HexitecTemplatePlugin.h
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#ifndef INCLUDE_HEXITECTEMPLATEPLUGIN_H_
#define INCLUDE_HEXITECTEMPLATEPLUGIN_H_

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

  /** Template for future Hexitec Frame objects.
   *
   * This service of the template for all of the remaining hexitec plug-ins to be written.
   */
  class HexitecTemplatePlugin : public FrameProcessorPlugin
  {
  public:
    HexitecTemplatePlugin();
    virtual ~HexitecTemplatePlugin();
    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);

  private:
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;

    void process_frame(boost::shared_ptr<Frame> frame);
    std::size_t reordered_image_size();

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Image width **/
    int image_width_;
    /** Image height **/
    int image_height_;
    /** Image pixel count **/
    int image_pixels_;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecTemplatePlugin, "HexitecTemplatePlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECTEMPLATEPLUGIN_H_ */
