/*
 * HexitecThresholdPlugin.cpp
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecThresholdPlugin.h>

namespace FrameProcessor
{

  const std::string HexitecThresholdPlugin::CONFIG_IMAGE_WIDTH 		 = "width";
  const std::string HexitecThresholdPlugin::CONFIG_IMAGE_HEIGHT 	 = "height";
  const std::string HexitecThresholdPlugin::CONFIG_THRESHOLD_MODE  = "threshold_mode";
  const std::string HexitecThresholdPlugin::CONFIG_THRESHOLD_VALUE = "threshold_value";
  const std::string HexitecThresholdPlugin::CONFIG_THRESHOLD_FILE  = "threshold_file";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecThresholdPlugin::HexitecThresholdPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecThresholdPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecThresholdPlugin constructor.");

    thresholdsStatus = true;
    thresholdValue = 3;
    thresholdPerPixel = (uint16_t *) malloc(FEM_TOTAL_PIXELS * sizeof(uint16_t));
    memset(thresholdPerPixel, 0, FEM_TOTAL_PIXELS * sizeof(uint16_t));
    /// Set threshold mode to none (initially; 0=none, 1=value ,2=file)
    thresholdMode = (ThresholdMode)0;

  }

  /**
   * Destructor.
   */
  HexitecThresholdPlugin::~HexitecThresholdPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecThresholdPlugin destructor.");

    free(thresholdPerPixel);
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
	    std::string threshold_mode = config.get_param<std::string>(HexitecThresholdPlugin::CONFIG_THRESHOLD_MODE);
	    /// Which threshold mode selected?
	    if (threshold_mode.compare(std::string("none")) == 0)
	    {
	    	thresholdMode = (ThresholdMode)0;
	    	LOG4CXX_TRACE(logger_, "User selected threshold mode: none");
	    }
	    else if (threshold_mode.compare(std::string("value")) == 0)
	    {
	    	thresholdMode = (ThresholdMode)1;
	    	LOG4CXX_TRACE(logger_, "User selected threshold mode: value");
	    }
	    else if (threshold_mode.compare(std::string("file")) == 0)
	    {
	    	thresholdMode = (ThresholdMode)2;
	    	LOG4CXX_TRACE(logger_, "User selected threshold mode: file");
	    }
	    /// Setup threshold value(s) accordingly
	    switch (thresholdMode)
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
	    	    thresholdValue = config.get_param<int>(HexitecThresholdPlugin::CONFIG_THRESHOLD_VALUE);
	    			LOG4CXX_TRACE(logger_, "Setting threshold value to: " << thresholdValue);
	    		}
	    		break;
	    	}
	    	case 2:
	    	{
	    		// Setup thresholds from file provided
	        if (config.has_param(HexitecThresholdPlugin::CONFIG_THRESHOLD_FILE))
	    		{
	    	    std::string threshold_file = config.get_param<std::string>(HexitecThresholdPlugin::CONFIG_THRESHOLD_FILE);

						LOG4CXX_TRACE(logger_, "Setting thresholds from file: " << threshold_file);
						if (setThresholdPerPixel(threshold_file.c_str()))
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

  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecThresholdPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecThresholdPlugin");
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
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

				// Set pointer to the input image data
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				// Execute selected method of applying threshold(s) (none, value, or file)
				switch (thresholdMode)
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
						processThresholdValue(static_cast<float *>(input_ptr),
																	static_cast<float *>(thresholded_image));
						break;
					}
					case 2:
					{
						processThresholdFile(static_cast<float *>(input_ptr),
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
   * Determine the size of a reordered image size based on the counter depth.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t HexitecThresholdPlugin::thresholded_image_size() {

    return image_width_ * image_height_ * sizeof(float);

  }

  /**
   * Zero all pixels below thresholdValue's value
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to memory where the thresholded image is written
   *
   */
  void HexitecThresholdPlugin::processThresholdValue(float* in, float* out)
  {
    for (int i=0; i < FEM_TOTAL_PIXELS; i++)
    {
      // Clear pixel if it doesn't meet in the threshold:
	  if (in[i] < thresholdValue)
	  {
	  	out[i] = 0;
	  }
	  else
	  {
    	out[i] = in[i];
	  }
//	  if (i < 15)
//  	    LOG4CXX_TRACE(logger_, "DEBUG, in[" << i << "] = " << in[i] << " out[" << i << "] = " << out[i]
//															 << " (thresholdValue = " << thresholdValue << ")");
    }
  }

  /**
   * Zero all pixels below not meeting corresponding pixel threshold
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to memory where the thresholded image is written
   *
   */
  void HexitecThresholdPlugin::processThresholdFile(float* in, float* out)
  {
    for (int i=0; i < FEM_TOTAL_PIXELS; i++)
    {
      // Clear pixel if it doesn't meet in the threshold:
			if (in[i] < thresholdPerPixel[i])
			{
				out[i] = 0;
			}
			else
			{
				out[i] = in[i];
			}
//		  if (i < 15)
//	  	  LOG4CXX_TRACE(logger_, "DEBUG, in[" << i << "] = " << in[i] << " out[" << i << "] = " << out[i]
//															 << " (thresholdPerPixel[" << i << "] = " << thresholdPerPixel[i]  << ")");
    }
  }

  // Helper functions:
  bool HexitecThresholdPlugin::setThresholdPerPixel(const char * thresholdFilename)
  {
    uint16_t defaultValue = 0;
    thresholdsStatus = getData(thresholdFilename, defaultValue);

    return thresholdsStatus;
  }

  bool HexitecThresholdPlugin::getData(const char *filename, uint16_t defaultValue)
  {
  	int index = 0, thresholdFromFile = 0;
    bool success = true;

    std::ifstream inFile(filename);

    if (!inFile)
    {
      for (int val = 0; val < FEM_TOTAL_PIXELS; val ++)
      {
        thresholdPerPixel[val] = defaultValue;
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
					thresholdPerPixel[index] = thresholdFromFile;
//					if (index < 15)
//						 LOG4CXX_TRACE(logger_, "thresholdFromFile = " << thresholdFromFile
//								 << " thresholdPerPixel[" << index << " ] = " << thresholdPerPixel[index]);
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
				thresholdPerPixel[val] = defaultValue;
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
