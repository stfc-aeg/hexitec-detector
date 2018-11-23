/*
 * HexitecThresholdPlugin.cpp
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecThresholdPlugin.h>
#include "version.h"

namespace FrameProcessor
{

  const std::string HexitecThresholdPlugin::CONFIG_IMAGE_WIDTH 		 = "width";
  const std::string HexitecThresholdPlugin::CONFIG_IMAGE_HEIGHT 	 = "height";
  const std::string HexitecThresholdPlugin::CONFIG_THRESHOLD_MODE  = "threshold_mode";
  const std::string HexitecThresholdPlugin::CONFIG_THRESHOLD_VALUE = "threshold_value";
  const std::string HexitecThresholdPlugin::CONFIG_THRESHOLD_FILE  = "threshold_file";
  const std::string HexitecThresholdPlugin::CONFIG_MAX_COLS 			 = "max_cols";
  const std::string HexitecThresholdPlugin::CONFIG_MAX_ROWS 			 = "max_rows";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecThresholdPlugin::HexitecThresholdPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
	    fem_pixels_per_rows_(80),
	    fem_pixels_per_columns_(80),
	    fem_total_pixels_(fem_pixels_per_rows_ * fem_pixels_per_columns_)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecThresholdPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecThresholdPlugin version " <<
    												this->get_version_long() << " loaded.");

    thresholds_status_		= false;
    threshold_value_ 			= 0;
    threshold_per_pixel_	= (uint16_t *) calloc(FEM_TOTAL_PIXELS, sizeof(uint16_t));
    /// Set threshold mode to none (initially; 0=none, 1=value ,2=file)
    threshold_mode_ = (ThresholdMode)0;

  }

  /**
   * Destructor.
   */
  HexitecThresholdPlugin::~HexitecThresholdPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecThresholdPlugin destructor.");

    free(threshold_per_pixel_);
  }

  int HexitecThresholdPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecThresholdPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecThresholdPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecThresholdPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecThresholdPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - image_width_ 						<=> width
 	 * - image_height_	 					<=> height
   * - max_frames_received_			<=> max_frames_received
   * - threshold_mode_					<=> threshold_mode
   * - threshold_value_					<=> threshold_value
   * - threshold_file_					<=> threshold_file
	 * - fem_pixels_per_columns_	<=> max_cols
	 * - fem_pixels_per_rows_ 		<=> max_rows
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecThresholdPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecThresholdPlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecThresholdPlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecThresholdPlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecThresholdPlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

    if (config.has_param(HexitecThresholdPlugin::CONFIG_THRESHOLD_MODE))
		{
	    std::string threshold_mode = config.get_param<std::string>(
	    		HexitecThresholdPlugin::CONFIG_THRESHOLD_MODE);
	    /// Which threshold mode selected?
	    if (threshold_mode.compare(std::string("none")) == 0)
	    {
	    	threshold_mode_ = (ThresholdMode)0;
	    	LOG4CXX_TRACE(logger_, "User selected threshold mode: none");
	    }
	    else if (threshold_mode.compare(std::string("value")) == 0)
	    {
	    	threshold_mode_ = (ThresholdMode)1;
	    	LOG4CXX_TRACE(logger_, "User selected threshold mode: value");
	    }
	    else if (threshold_mode.compare(std::string("file")) == 0)
	    {
	    	threshold_mode_ = (ThresholdMode)2;
	    	LOG4CXX_TRACE(logger_, "User selected threshold mode: file");
	    }
	    /// Setup threshold value(s) accordingly
	    switch (threshold_mode_)
	    {
	    	case 0:
	    	{
	    		// Threshold mode None means no need to read in threshold value/file this time
	    		break;
	    	}
	    	case 1:
	    	{
	    		// Setup threshold using provided value
	        if (config.has_param(HexitecThresholdPlugin::CONFIG_THRESHOLD_VALUE))
	    		{
	    	    threshold_value_ = config.get_param<int>(
	    	    		HexitecThresholdPlugin::CONFIG_THRESHOLD_VALUE);
	    			LOG4CXX_TRACE(logger_, "Setting threshold value to: " << threshold_value_);
	    		}
	    		break;
	    	}
	    	case 2:
	    	{
	    		// Setup thresholds from file provided
	        if (config.has_param(HexitecThresholdPlugin::CONFIG_THRESHOLD_FILE))
	    		{
	    	    std::string threshold_file = config.get_param<std::string>(
	    	    		HexitecThresholdPlugin::CONFIG_THRESHOLD_FILE);

						LOG4CXX_TRACE(logger_, "Setting thresholds from file: " << threshold_file);
						if (set_threshold_per_pixel(threshold_file.c_str()))
						{
							LOG4CXX_TRACE(logger_, "Read thresholds from file successfully");
						}
						else
						{
							LOG4CXX_ERROR(logger_, "Failed to read thresholds from file")
						}
	    		}
	    		break;
	    	}
	    	default:
	    		break;
	    }
		}

    if (config.has_param(HexitecThresholdPlugin::CONFIG_MAX_COLS))
    {
      fem_pixels_per_columns_ = config.get_param<int>(HexitecThresholdPlugin::CONFIG_MAX_COLS);
    }

    if (config.has_param(HexitecThresholdPlugin::CONFIG_MAX_ROWS))
    {
      fem_pixels_per_rows_ = config.get_param<int>(HexitecThresholdPlugin::CONFIG_MAX_ROWS);
    }

    fem_total_pixels_ = fem_pixels_per_columns_ * fem_pixels_per_rows_;
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecThresholdPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecThresholdPlugin");
  }

  /**
   * Perform processing on the frame.  Apply selected threshold mode.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecThresholdPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying threshold(s) to frame.");

    // Determine the size of the output thresholded image
    const std::size_t output_image_size = thresholded_image_size();

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
			// Pointers to thresholded image buffer - will be allocated on demand
			void* thresholded_image = NULL;

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

				// Allocate buffer to receive thresholded image
				thresholded_image = (void*)malloc(output_image_size);
				if (thresholded_image == NULL)
				{
					throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
				}

				// Define pointer to the input image data
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				// Execute selected method of applying threshold(s) (none, value, or file)
				switch (threshold_mode_)
				{
					case 0:
					{
						// Free thresholded_image and push frame as is
						free(thresholded_image);
						thresholded_image = NULL;

						this->push(frame);
						break;
					}
					case 1:
					{
						process_threshold_value(static_cast<float *>(input_ptr),
																	static_cast<float *>(thresholded_image));
						break;
					}
					case 2:
					{
						process_threshold_file(static_cast<float *>(input_ptr),
													 	 	 	 static_cast<float *>(thresholded_image));
						break;
					}
				}

//				/* Code for determining which directory src code is run from
//				 * Hint, it is from /install */
//#include <stdio.h>  /* defines FILENAME_MAX */
//#ifdef WINDOWS
//		#include <direct.h>
//		#define GetCurrentDir _getcwd
//#else
//		#include <unistd.h>
//		#define GetCurrentDir getcwd
//#endif
//
//				char cCurrentPath[FILENAME_MAX];
//				if (!GetCurrentDir(cCurrentPath, sizeof(cCurrentPath)))
//				{
//					LOG4CXX_TRACE(logger_, "Couldn't get current dir !!");
//				}
//				else
//					cCurrentPath[sizeof(cCurrentPath) - 1] = '\0'; /* not really required */
//				LOG4CXX_TRACE(logger_, "The current working directory is: " << cCurrentPath);

				// Set the frame image to the thresholded image buffer if appropriate
				if (thresholded_image)
				{
					// Setup the frame dimensions
					dimensions_t dims(2);
					dims[0] = image_height_;
					dims[1] = image_width_;

					boost::shared_ptr<Frame> data_frame;
					data_frame = boost::shared_ptr<Frame>(new Frame(dataset));

					data_frame->set_frame_number(frame->get_frame_number());

					data_frame->set_dimensions(dims);
					data_frame->copy_data(thresholded_image, output_image_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
		 														 " dataset, frame number: " << frame->get_frame_number());
					this->push(data_frame);

					free(thresholded_image);
					thresholded_image = NULL;
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
  std::size_t HexitecThresholdPlugin::thresholded_image_size() {

    return image_width_ * image_height_ * sizeof(float);

  }

  /**
   * Zero all pixels below threshold_value_.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to memory where the thresholded image is written
   *
   */
  void HexitecThresholdPlugin::process_threshold_value(float *in, float *out)
  {
    for (int i=0; i < FEM_TOTAL_PIXELS; i++)
    {
      // Clear pixel if it doesn't meet in the threshold:
			if (in[i] < threshold_value_)
			{
				out[i] = 0;
			}
			else
			{
				out[i] = in[i];
			}
    }
  }

  /**
   * Zero each pixel not meeting its corresponding pixel threshold.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to memory where the thresholded image is written
   *
   */
  void HexitecThresholdPlugin::process_threshold_file(float *in, float *out)
  {
    for (int i=0; i < FEM_TOTAL_PIXELS; i++)
    {
      // Clear pixel if it doesn't meet in the threshold:
			if (in[i] < threshold_per_pixel_[i])
			{
				out[i] = 0;
			}
			else
			{
				out[i] = in[i];
			}
    }
  }

  /**
   * Set each pixel threshold from the values by the provided file.
   *
   * \param[in] threshold_filename - the filename containing threshold values.
   *
   * \return bool indicating whether reading file was successful
   */
  bool HexitecThresholdPlugin::set_threshold_per_pixel(const char *threshold_filename)
  {
    uint16_t defaultValue = 0;
    thresholds_status_ = get_data(threshold_filename, defaultValue);

    return thresholds_status_;
  }

  /**
   * Set each pixel threshold from the values by the provided file.
   *
   * \param[in] threshold_filename - the filename containing threshold values.
   * \param[in] default_value - Default value if there's any issues reading the file
   *
   * \return bool indicating whether reading file was successful
   */
  bool HexitecThresholdPlugin::get_data(const char *filename, uint16_t default_value)
  {
  	int index = 0, thresholdFromFile = 0;
    bool success = true;

    std::ifstream inFile(filename);

    if (!inFile)
    {
      for (int val = 0; val < FEM_TOTAL_PIXELS; val ++)
      {
        threshold_per_pixel_[val] = default_value;
      }
      success = false;
      LOG4CXX_WARN(logger_, "Couldn't access threshold file, using default value");
    }
    else
    {
			std::string line;
			while(std::getline(inFile, line))
			{
				std::stringstream ss(line);

				while( ss >> thresholdFromFile )
				{
					threshold_per_pixel_[index] = thresholdFromFile;
					index++;
				}
			}
  	}

    // If file do not contain enough threshold values for all pixels,
    // 	assign default threshold to remaining pixels
    if (index < FEM_TOTAL_PIXELS)
    {
      for (int val = index; val < FEM_TOTAL_PIXELS; val ++)
      {
				threshold_per_pixel_[val] = default_value;
      }
    }
		else
		{
			success = true;
		}
		inFile.close();

		return success;
  }

} /* namespace FrameProcessor */
