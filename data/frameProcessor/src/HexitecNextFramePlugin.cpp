/*
 * HexitecNextFramePlugin.cpp
 *
 *  Created on: 18 Sept 2018
 *      Author: ckd27546
 */

#include <HexitecNextFramePlugin.h>

namespace FrameProcessor
{

  const std::string HexitecNextFramePlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecNextFramePlugin::CONFIG_IMAGE_HEIGHT = "height";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecNextFramePlugin::HexitecNextFramePlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
			last_frame_number_(-1)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecNextFramePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecNextFramePlugin constructor.");

    last_frame_ = (float *) malloc(FEM_TOTAL_PIXELS * sizeof(float));
    memset(last_frame_, 0, FEM_TOTAL_PIXELS * sizeof(float));
    ///
    debugFrameCounter = 0;

  }

  /**
   * Destructor.
   */
  HexitecNextFramePlugin::~HexitecNextFramePlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecNextFramePlugin destructor.");
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - bitdepth
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[out] reply - Reference to the reply IpcMessage object.
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
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecNextFramePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecNextFramePlugin");
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecNextFramePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    long long current_frame_number = frame->get_frame_number();

    LOG4CXX_TRACE(logger_, "Applying Next Frame algorithm.");

    // Determine the size of the output image
    const std::size_t output_image_size = reordered_image_size();

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data()));

    // Check dataset; Which set determines how to proceed..
    const std::string& dataset = frame->get_dataset_name();
    if (dataset.compare(std::string("raw_frames")) == 0)
    {
			LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
 														 " dataset, frame number: " << current_frame_number);
			this->push(frame);
    }
    else if (dataset.compare(std::string("data")) == 0)
    {
			// Pointer to corrected image buffer - will be allocated on demand
			void* corrected_image = NULL;

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

				// Allocate buffer to receive reordered image.
				corrected_image = (void *)calloc(image_width_ * image_height_, sizeof(float));
				if (corrected_image == NULL)
				{
					throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
				}

				// Pointer to the input image
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
					// Compare current frame versus last frame, if same pixel hit in both then clear both pixels
					apply_algorithm(static_cast<float *>(input_ptr),
																 static_cast<float *>(corrected_image));
				}
		    ///
//				writeFile("All_540_frames_", static_cast<float *>(corrected_image));
//				debugFrameCounter += 1;
		    ///

				// Set the frame image to the corrected image buffer if appropriate
				if (corrected_image)
				{
					// Setup the frame dimensions
					dimensions_t dims(2);
					dims[0] = image_height_;
					dims[1] = image_width_;

					boost::shared_ptr<Frame> data_frame;
					data_frame = boost::shared_ptr<Frame>(new Frame(dataset));

					data_frame->set_frame_number(current_frame_number);

					data_frame->set_dimensions(dims);
					data_frame->copy_data(corrected_image, output_image_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
																 " dataset, frame number: " << current_frame_number);
					this->push(data_frame);

					last_frame_number_ = current_frame_number;

					// Copy current (corrected) frame into last frame's place
					memcpy(last_frame_, corrected_image, FEM_TOTAL_PIXELS * sizeof(float));
					free(corrected_image);
					corrected_image = NULL;
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
   * Determine the size of a reordered image size based on the counter depth.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t HexitecNextFramePlugin::reordered_image_size() {

    return image_width_ * image_height_ * sizeof(float);
  }

  /**
   * Compare current against last frame, zero Pixel in current frame if hit
   * 		in the last frame.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory for the corrected image.
   *
   */
  void HexitecNextFramePlugin::apply_algorithm(float* in, float* out)
  {
//  	LOG4CXX_TRACE(logger_, " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-");
    for (int i=0; i<FEM_TOTAL_PIXELS; i++)
    {
    	// If pixel in last frame is nonzero, clear it from current frame
    	// 	(whether hit or not), otherwise don't clear pixel frame current frame
    	if (last_frame_[i] > 0.0)
    	{
    		;//out[i] = 0.0;		// Redundant (*out calloc'd..)
    	}
    	else
    	{
    		out[i] = in[i];
    	}
    }
    // Copy current frame so it can be compared against the following frame
    memcpy(last_frame_, in, FEM_TOTAL_PIXELS * sizeof(float));
  }

  //// Debug function: Takes a file prefix, frame and writes all nonzero pixels to a file
	void HexitecNextFramePlugin::writeFile(std::string filePrefix, float *frame)
	{
    std::ostringstream hitPixelsStream;
    hitPixelsStream << "-------------- frame " << debugFrameCounter << " --------------\n";
		for (int i = 0; i < FEM_TOTAL_PIXELS; i++ )
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

