/*
 * HexitecTemplatePlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: Christian Angelsen
 */

#include <HexitecTemplatePlugin.h>
#include "version.h"

namespace FrameProcessor
{

  const std::string HexitecTemplatePlugin::CONFIG_IMAGE_WIDTH  = "width";
  const std::string HexitecTemplatePlugin::CONFIG_IMAGE_HEIGHT = "height";
  const std::string HexitecTemplatePlugin::CONFIG_MAX_COLS 		 = "fem_max_cols";
  const std::string HexitecTemplatePlugin::CONFIG_MAX_ROWS 		 = "fem_max_rows";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecTemplatePlugin::HexitecTemplatePlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
	    fem_pixels_per_rows_(80),
	    fem_pixels_per_columns_(80),
	    fem_total_pixels_(fem_pixels_per_rows_ * fem_pixels_per_columns_)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecTemplatePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecTemplatePlugin version " <<
    												this->get_version_long() << " loaded.");

  }

  /**
   * Destructor.
   */
  HexitecTemplatePlugin::~HexitecTemplatePlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecTemplatePlugin destructor.");
  }

  int HexitecTemplatePlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecTemplatePlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecTemplatePlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecTemplatePlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecTemplatePlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - image_width_ 						<=> width
 	 * - image_height_	 					<=> height
	 * - fem_pixels_per_columns_	<=> fem_max_cols
	 * - fem_pixels_per_rows_ 		<=> fem_max_rows
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecTemplatePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecTemplatePlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecTemplatePlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecTemplatePlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecTemplatePlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

    if (config.has_param(HexitecTemplatePlugin::CONFIG_MAX_COLS))
    {
      fem_pixels_per_columns_ = config.get_param<int>(HexitecTemplatePlugin::CONFIG_MAX_COLS);
    }

    if (config.has_param(HexitecTemplatePlugin::CONFIG_MAX_ROWS))
    {
      fem_pixels_per_rows_ = config.get_param<int>(HexitecTemplatePlugin::CONFIG_MAX_ROWS);
    }

    fem_total_pixels_ = fem_pixels_per_columns_ * fem_pixels_per_rows_;
  }

  void HexitecTemplatePlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecTemplatePlugin::CONFIG_IMAGE_WIDTH, image_width_);
    reply.set_param(base_str + HexitecTemplatePlugin::CONFIG_IMAGE_HEIGHT, image_height_);
    reply.set_param(base_str + HexitecTemplatePlugin::CONFIG_MAX_COLS, fem_pixels_per_columns_);
    reply.set_param(base_str + HexitecTemplatePlugin::CONFIG_MAX_ROWS, fem_pixels_per_rows_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecTemplatePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecTemplatePlugin");
    status.set_param(get_name() + "/image_width", image_width_);
    status.set_param(get_name() + "/image_height", image_height_);
    status.set_param(get_name() + "/fem_max_rows", fem_pixels_per_rows_);
    status.set_param(get_name() + "/fem_max_cols", fem_pixels_per_columns_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecTemplatePlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  For a new plugin, amend this
   *  function process data as intended.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecTemplatePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying ... template algorithm???");

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
			LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
 														 " dataset, frame number: " << frame->get_frame_number());
			this->push(frame);
    }
    else if (dataset.compare(std::string("data")) == 0)
    {
			try
			{
				// Check that the pixels are contained within the dimensions of the
				// specified output image, otherwise throw an error
				if (fem_total_pixels_ > image_pixels_)
				{
					std::stringstream msg;
					msg << "Pixel count inferred from FEM (" << fem_total_pixels_
							<< ") will exceed dimensions of output image (" << image_pixels_ << ")";
					throw std::runtime_error(msg.str());
				}

				// Define pointer to the input image data
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				///TODO: This function do not exist; Design it to match requirements
//	        some_function(static_cast<float *>(input_ptr));


				LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
															 " dataset, frame number: " << frame->get_frame_number());
				this->push(frame);

			}
			catch (const std::exception& e)
			{
				std::stringstream ss;
				ss << "HEXITEC frame decode failed: " << e.what();
				LOG4CXX_ERROR(logger_, ss.str());
			}
		}
    else
    {
    	LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }

  }

} /* namespace FrameProcessor */

