/*
 * HexitecCalibrationPlugin.cpp
 *
 *  Created on: 24 Sept 2018
 *      Author: ckd27546
 */

#include <HexitecCalibrationPlugin.h>

namespace FrameProcessor
{

  const std::string HexitecCalibrationPlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecCalibrationPlugin::CONFIG_IMAGE_HEIGHT = "height";
  const std::string HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE = "gradients_file";
  const std::string HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE = "intercepts_file";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecCalibrationPlugin::HexitecCalibrationPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
			gradientsStatus(false),
			interceptsStatus(false),
			gradientValue(NULL),
			interceptValue(NULL),
			frameSize(6400)	// Redundant, Replace all cases of frameSize with image_pixels_
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecCalibrationPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecCalibrationPlugin constructor.");

		gradientValue = (float *) malloc(frameSize * sizeof(float));
		memset(gradientValue, 0, frameSize * sizeof(float));
		interceptValue = (float *) malloc(frameSize * sizeof(float));
		memset(interceptValue, 0, frameSize * sizeof(float));

		*gradientValue = 1;
		*interceptValue = 0;
    ///
    debugFrameCounter = 0;

  }

  /**
   * Destructor.
   */
  HexitecCalibrationPlugin::~HexitecCalibrationPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecCalibrationPlugin destructor.");

	 free(gradientValue);
	 free(interceptValue);
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
  void HexitecCalibrationPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecCalibrationPlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecCalibrationPlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecCalibrationPlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecCalibrationPlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

    if (config.has_param(HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE))
		{
			std::string gradients_file = config.get_param<std::string>(HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE);
			LOG4CXX_TRACE(logger_, "Setting gradients from file: " << gradients_file);
			setGradients(gradients_file.c_str());
		}

    if (config.has_param(HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE))
		{
	    std::string intercept_file = config.get_param<std::string>(HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE);
			LOG4CXX_TRACE(logger_, "Setting intercepts from file: " << intercept_file);
			setIntercepts(intercept_file.c_str());
		}

  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecCalibrationPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecCalibrationPlugin");
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecCalibrationPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying Calibration.");

    // Determine the size of the output reordered image
    const std::size_t output_image_size = calibrated_image_size();

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
			void* calibrated_image = NULL;

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
				calibrated_image = (void*)calloc(image_pixels_, sizeof(float));
				if (calibrated_image == NULL)
				{
					throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
				}

				// Calculate pointer into the input image data based on loop index
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				calibrate_pixels(static_cast<float *>(input_ptr),
														 static_cast<float *>(calibrated_image));
		    ///
//				writeFile("All_540_frames_", static_cast<float *>(calibrated_image));
//		    debugFrameCounter += 1;
		    ///

				// Set the frame image to the reordered image buffer if appropriate
				if (calibrated_image)
				{
					// Setup the frame dimensions
					dimensions_t dims(2);
					dims[0] = image_height_;
					dims[1] = image_width_;

					boost::shared_ptr<Frame> data_frame;
					data_frame = boost::shared_ptr<Frame>(new Frame(dataset));

					data_frame->set_frame_number(frame->get_frame_number());

					data_frame->set_dimensions(dims);
					data_frame->copy_data(calibrated_image, output_image_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
		 														 " dataset, frame number: " << frame->get_frame_number());
					this->push(data_frame);
					free(calibrated_image);
					calibrated_image = NULL;
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
  std::size_t HexitecCalibrationPlugin::calibrated_image_size() {

    return image_width_ * image_height_ * sizeof(float);
  }

  /**
   * Calibrate an image's pixels.
   *
   * \param[in] in 	 - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where
   * 										the calibrated pixels will be stored.
   */
  void HexitecCalibrationPlugin::calibrate_pixels(float* in, float* out)
  {
    for (int i=0; i<FEM_TOTAL_PIXELS; i++)
    {
     	if (in[i] > 0)
     	{
     		out[i] = (in[i] * gradientValue[i])  + interceptValue[i];
     	}
    }
  }

  void HexitecCalibrationPlugin::setGradients(const char *gradientFilename)
  {
    float defaultValue = 1;
    gradientsStatus = getData(gradientFilename, gradientValue, defaultValue);
    if (gradientsStatus)
    {
    	LOG4CXX_TRACE(logger_, "Setting Gradients Successful, used file: " << gradientFilename);
    }
    else
    {
    	LOG4CXX_ERROR(logger_, "setGradients() Failed (using default value instead), used file: " << gradientFilename);
    }
  }

  void HexitecCalibrationPlugin::setIntercepts(const char *interceptFilename)
  {
    float defaultValue = 0;
    interceptsStatus = getData(interceptFilename, interceptValue, defaultValue);
    if (interceptsStatus)
    {
    	LOG4CXX_TRACE(logger_, "Setting Intercepts Successful, used file: " << interceptFilename);
    }
    else
    {
    	LOG4CXX_ERROR(logger_, "setIntercepts() Failed (using default value instead), used file: " << interceptFilename);
    }
  }

  bool HexitecCalibrationPlugin::getData(const char *filename, float *dataValue, float defaultValue)
  {
  	int i = 0;
		std::ifstream inFile;
		bool success = false;

		inFile.open(filename);

		if (!inFile)
		{
			LOG4CXX_TRACE(logger_, "Couldn't open file, using default values");

			for (int val = 0; val < frameSize; val ++)
			{
				dataValue[val] = defaultValue;
			}
		}

		while (inFile >> dataValue[i])
		{
			i++;
		}

		if (i < frameSize)
		{
			for (int val = i; val < frameSize; val ++)
			{
				dataValue[val] = defaultValue;
				if (i == val)
					LOG4CXX_TRACE(logger_, "Only found " << i << " values in " << filename
						 << "; Padding remaining with default value: " << defaultValue);
			}
		}
		else
		{
			success = true;
		}
		inFile.close();

		return success;
  }

  //// Debug function: Takes a file prefix, frame and writes all nonzero pixels to a file
	void HexitecCalibrationPlugin::writeFile(std::string filePrefix, float *frame)
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

