/*
 * HexitecTemplatePlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecTemplatePlugin.h>
#include "version.h"

namespace FrameProcessor
{

  const std::string HexitecTemplatePlugin::CONFIG_IMAGE_WIDTH  = "width";
  const std::string HexitecTemplatePlugin::CONFIG_IMAGE_HEIGHT = "height";
  const std::string HexitecTemplatePlugin::CONFIG_MAX_COLS 		 = "max_cols";
  const std::string HexitecTemplatePlugin::CONFIG_MAX_ROWS 		 = "max_rows";

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
	 * - fem_pixels_per_columns_	<=> max_cols
	 * - fem_pixels_per_rows_ 		<=> max_rows
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

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecTemplatePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecTemplatePlugin");
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

    // Determine the size of the output reordered image
    const std::size_t output_image_size = reordered_image_size();

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data()));

    // Check dataset; Which set determines how to proceed..
    const std::string& dataset = frame->get_dataset_name();
    if (dataset.compare(std::string("raw_frames")) == 0)
    {
			LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
 														 " dataset, frame number: " << frame->get_frame_number());
			this->push(frame);
    }
    else if (dataset.compare(std::string("data")) == 0)
    {
			// Pointers to reordered image buffer - will be allocated on demand
			void* reordered_image = NULL;

			try
			{

				// Check that the pixels are contained within the dimensions of the
				// specified output image, otherwise throw an error
				if (FEM_TOTAL_PIXELS > image_pixels_)
				{
					std::stringstream msg;
					msg << "Pixel count inferred from FEM ("
							<< FEM_TOTAL_PIXELS
							<< ") will exceed dimensions of output image (" << image_pixels_ << ")";
					throw std::runtime_error(msg.str());
				}

				// Allocate buffer to receive proccessed image
				reordered_image = (void*)calloc(image_pixels_, sizeof(float));
				if (reordered_image == NULL)
				{
					throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
				}

				// Define pointer to the input image data
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				///TODO: This function do not exist; Design it to match requirements
//	        reorder_pixels(static_cast<float *>(input_ptr),
//	                             static_cast<float *>(reordered_image));


				// Set the frame image to the reordered image buffer if appropriate
				if (reordered_image)
				{
					// Setup the frame dimensions
					dimensions_t dims(2);
					dims[0] = image_height_;
					dims[1] = image_width_;

					boost::shared_ptr<Frame> data_frame;
					data_frame = boost::shared_ptr<Frame>(new Frame(dataset));

					data_frame->set_frame_number(frame->get_frame_number());

					data_frame->set_dimensions(dims);
					data_frame->copy_data(reordered_image, output_image_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
		 														 " dataset, frame number: " << frame->get_frame_number());
					this->push(data_frame);

					free(reordered_image);
					reordered_image = NULL;
				}
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

  /**
   * Determine the size of a processed image.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t HexitecTemplatePlugin::reordered_image_size() {

    return image_width_ * image_height_ * sizeof(float);
  }

} /* namespace FrameProcessor */

