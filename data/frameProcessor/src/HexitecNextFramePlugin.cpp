/*
 * HexitecNextFramePlugin.cpp
 *
 *  Created on: 18 Sept 2018
 *      Author: Christian Angelsen
 */

#include <HexitecNextFramePlugin.h>
#include "version.h"

namespace FrameProcessor
{

  const std::string HexitecNextFramePlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecNextFramePlugin::CONFIG_IMAGE_HEIGHT = "height";
  const std::string HexitecNextFramePlugin::CONFIG_MAX_COLS = "fem_max_cols";
  const std::string HexitecNextFramePlugin::CONFIG_MAX_ROWS = "fem_max_rows";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecNextFramePlugin::HexitecNextFramePlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
			last_frame_number_(-1),
			fem_pixels_per_rows_(80),
			fem_pixels_per_columns_(80),
			fem_total_pixels_(fem_pixels_per_rows_ * fem_pixels_per_columns_)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecNextFramePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecNextFramePlugin version " <<
    												this->get_version_long() << " loaded.");

    last_frame_ = (float *) calloc(fem_total_pixels_, sizeof(float));
    ///
    debugFrameCounter = 0;

  }

  /**
   * Destructor.
   */
  HexitecNextFramePlugin::~HexitecNextFramePlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecNextFramePlugin destructor.");
    free(last_frame_);
    last_frame_ = NULL;
  }

  int HexitecNextFramePlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecNextFramePlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecNextFramePlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecNextFramePlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecNextFramePlugin::get_version_long()
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
  void HexitecNextFramePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecNextFramePlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecNextFramePlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecNextFramePlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecNextFramePlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

    if (config.has_param(HexitecNextFramePlugin::CONFIG_MAX_COLS))
    {
      fem_pixels_per_columns_ = config.get_param<int>(HexitecNextFramePlugin::CONFIG_MAX_COLS);
    }

    if (config.has_param(HexitecNextFramePlugin::CONFIG_MAX_ROWS))
    {
      fem_pixels_per_rows_ = config.get_param<int>(HexitecNextFramePlugin::CONFIG_MAX_ROWS);
    }

    fem_total_pixels_ = fem_pixels_per_columns_ * fem_pixels_per_rows_;
  }

  void HexitecNextFramePlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecNextFramePlugin::CONFIG_IMAGE_WIDTH, image_width_);
    reply.set_param(base_str + HexitecNextFramePlugin::CONFIG_IMAGE_HEIGHT, image_height_);
    reply.set_param(base_str + HexitecNextFramePlugin::CONFIG_MAX_COLS, fem_pixels_per_columns_);
    reply.set_param(base_str + HexitecNextFramePlugin::CONFIG_MAX_ROWS, fem_pixels_per_rows_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecNextFramePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecNextFramePlugin");
    status.set_param(get_name() + "/image_width", image_width_);
    status.set_param(get_name() + "/image_height", image_height_);
    status.set_param(get_name() + "/fem_max_rows", fem_pixels_per_rows_);
    status.set_param(get_name() + "/fem_max_cols", fem_pixels_per_columns_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecNextFramePlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  If same pixel hit in current frame as in the previous,
   * 	set pixel in current frame to zero.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecNextFramePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    long long current_frame_number = frame->get_frame_number();

    LOG4CXX_TRACE(logger_, "Applying Next Frame algorithm.");

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
			LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
 														 " dataset, frame number: " << current_frame_number);
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

				// Don't compare current against last frame if not adjacent
				if ((last_frame_number_+1) != current_frame_number)
				{
					LOG4CXX_TRACE(logger_, "Not correcting current frame, because last frame number: " <<
																	last_frame_number_ << " versus current_frame_number: "
																	<< current_frame_number);
				}
				else
				{
					// Compare current frame versus last frame, if same pixel hit in both
					// 	then clear current pixel
					apply_algorithm(static_cast<float *>(input_ptr));
				}

				LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
															 " dataset, frame number: " << current_frame_number);

				last_frame_number_ = current_frame_number;

				// Copy current frame into last frame's place - regardless of any correection
				//	taking place, as we'll always need the current frame to compare against
				// 	the previous frame
				// 		Will this work (static_cast'ing..) ???
				memcpy(last_frame_, static_cast<float *>(input_ptr), fem_total_pixels_ * sizeof(float));

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

  /**
   * Compare current against last frame, zero Pixel in current frame if hit
   * 		in the last frame.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to the allocated memory for the corrected image.
   *
   */
  void HexitecNextFramePlugin::apply_algorithm(float *in)
  {
    for (int i=0; i<fem_total_pixels_; i++)
    {
    	// If pixel in last frame is nonzero, clear it from current frame
    	// 	(whether hit or not), otherwise don't clear pixel frame current frame
    	if (last_frame_[i] > 0.0)
    	{
    		in[i] = 0.0;
    	}
    }

  }

  //// Debug function: Takes a file prefix and frame, and writes all nonzero pixels to a file
	void HexitecNextFramePlugin::writeFile(std::string filePrefix, float *frame)
	{
    std::ostringstream hitPixelsStream;
    hitPixelsStream << "-------------- frame " << debugFrameCounter << " --------------\n";
		for (int i = 0; i < fem_total_pixels_; i++ )
		{
			if(frame[i] > 0)
				hitPixelsStream << "Cal[" << i << "] = " << frame[i] << "\n";
		}
		std::string hitPixelsString  = hitPixelsStream.str();
		std::string fname = filePrefix //+ boost::to_string(debugFrameCounter)
			 + std::string("_ODIN_Cal_detailed.txt");
		outFile.open(fname.c_str(), std::ofstream::app);
		outFile.write((const char *)hitPixelsString.c_str(), hitPixelsString.length() * sizeof(char));
		outFile.close();
	}

} /* namespace FrameProcessor */

