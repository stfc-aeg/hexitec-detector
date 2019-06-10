/*
 * HexitecCalibrationPlugin.cpp
 *
 *  Created on: 24 Sept 2018
 *      Author: Christian Angelsen
 */

#include <HexitecCalibrationPlugin.h>
#include "version.h"

namespace FrameProcessor
{

  const std::string HexitecCalibrationPlugin::CONFIG_IMAGE_WIDTH 		 = "width";
  const std::string HexitecCalibrationPlugin::CONFIG_IMAGE_HEIGHT 	 = "height";
  const std::string HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE  = "gradients_filename";
  const std::string HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE = "intercepts_filename";
  const std::string HexitecCalibrationPlugin::CONFIG_MAX_COLS 			 = "fem_max_cols";
  const std::string HexitecCalibrationPlugin::CONFIG_MAX_ROWS 			 = "fem_max_rows";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecCalibrationPlugin::HexitecCalibrationPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
			gradients_status_(false),
			intercepts_status_(false),
			gradient_values_(NULL),
			intercept_values_(NULL),
			fem_pixels_per_rows_(80),
			fem_pixels_per_columns_(80),
			fem_total_pixels_(fem_pixels_per_rows_ * fem_pixels_per_columns_),
			gradients_filename_(""),
			intercepts_filename_("")
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecCalibrationPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecCalibrationPlugin version " <<
    												this->get_version_long() << " loaded.");

		gradient_values_ = (float *) calloc(image_pixels_, sizeof(float));
		intercept_values_ = (float *) calloc(image_pixels_, sizeof(float));

		*gradient_values_ = 1;
		*intercept_values_ = 0;
    ///
    debugFrameCounter = 0;

  }

  /**
   * Destructor.
   */
  HexitecCalibrationPlugin::~HexitecCalibrationPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecCalibrationPlugin destructor.");

	 free(gradient_values_);
	 free(intercept_values_);
  }

  int HexitecCalibrationPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecCalibrationPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecCalibrationPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecCalibrationPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecCalibrationPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - image_width_ 						<=> width
 	 * - image_height_	 					<=> height
 	 * - gradients_filename 			<=> gradients_file
 	 * - intercepts_filename 			<=> intercepts_file
	 * - fem_pixels_per_columns_	<=> fem_max_cols
	 * - fem_pixels_per_rows_ 		<=> fem_max_rows
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
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
			gradients_filename_ = config.get_param<std::string>(HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE);
			setGradients(gradients_filename_.c_str());
		}

    if (config.has_param(HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE))
		{
	    intercepts_filename_ = config.get_param<std::string>(HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE);
			setIntercepts(intercepts_filename_.c_str());
		}

    if (config.has_param(HexitecCalibrationPlugin::CONFIG_MAX_COLS))
    {
      fem_pixels_per_columns_ = config.get_param<int>(HexitecCalibrationPlugin::CONFIG_MAX_COLS);
    }

    if (config.has_param(HexitecCalibrationPlugin::CONFIG_MAX_ROWS))
    {
      fem_pixels_per_rows_ = config.get_param<int>(HexitecCalibrationPlugin::CONFIG_MAX_ROWS);
    }

    fem_total_pixels_ = fem_pixels_per_columns_ * fem_pixels_per_rows_;

  }

  void HexitecCalibrationPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the calibration plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_IMAGE_WIDTH, image_width_);
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_IMAGE_HEIGHT, image_height_);
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE, gradients_filename_);
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE, intercepts_filename_);
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_MAX_COLS, fem_pixels_per_columns_);
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_MAX_ROWS, fem_pixels_per_rows_);

  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecCalibrationPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecCalibrationPlugin");
    status.set_param(get_name() + "/image_width", image_width_);
    status.set_param(get_name() + "/image_height", image_height_);
    status.set_param(get_name() + "/gradients_filename", gradients_filename_);
    status.set_param(get_name() + "/intercepts_filename", intercepts_filename_);
    status.set_param(get_name() + "/fem_max_rows", fem_pixels_per_rows_);
    status.set_param(get_name() + "/fem_max_cols", fem_pixels_per_columns_);
  }

  /**
   * Reset calibration plugin statistics
   */
  bool HexitecCalibrationPlugin::reset_statistics(void)
  {
    // Nothing to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  Each pixel is calibrated with the gradient and intercept values
   *  provided by the two corresponding files.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecCalibrationPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying Calibration.");

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
					msg << "Pixel count inferred from FEM ("
							<< fem_total_pixels_
							<< ") will exceed dimensions of output image (" << image_pixels_ << ")";
					throw std::runtime_error(msg.str());
				}

				// Define pointer to the input image data
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				calibrate_pixels(static_cast<float *>(input_ptr));

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
   * Calibrate an image's pixels.
   *
   * \param[in] image - Pointer to the image data.
   */
  void HexitecCalibrationPlugin::calibrate_pixels(float *image)
  {
    for (int i=0; i<fem_total_pixels_; i++)
    {
     	if (image[i] > 0)
     	{
     		image[i] = (image[i] * gradient_values_[i])  + intercept_values_[i];
     	}
    }
  }

  /**
   * Set the filename containing the gradient values.
   *
   * \param[in] gradientFilename - The name of the gradient file.
   */
  void HexitecCalibrationPlugin::setGradients(const char *gradientFilename)
  {
    float defaultValue = 1;
    gradients_status_ = getData(gradientFilename, gradient_values_, defaultValue);
    if (gradients_status_)
    {
    	LOG4CXX_TRACE(logger_, "Setting Gradients Successful, used file: " << gradientFilename);
    }
    else
    {
    	LOG4CXX_ERROR(logger_, "setGradients() Failed (using default value instead), used file: " << gradientFilename);
    }
  }

  /**
   * Set the filename containing the intercept values.
   *
   * \param[in] interceptFilename - The name of the intercept file.
   */
  void HexitecCalibrationPlugin::setIntercepts(const char *interceptFilename)
  {
    float defaultValue = 0;
    intercepts_status_ = getData(interceptFilename, intercept_values_, defaultValue);
    if (intercepts_status_)
    {
    	LOG4CXX_TRACE(logger_, "Setting Intercepts Successful, used file: " << interceptFilename);
    }
    else
    {
    	LOG4CXX_ERROR(logger_, "setIntercepts() Failed (using default value instead), used file: " << interceptFilename);
    }
  }

  /**
   * Read all the values from the provided file.  If the file is too short, pad missing
   * 	values using the provided default value.
   *
   * \param[in] filename - The name of the file to be read.
   * \param[in] dataValue - Array that will receive values read from file.
   * \param[in] defaultValue - The default value used if filename is too short to
   * 	(provide image_pixels_ number of values).
   *
   * \return bool indicating success of reading file
   */
  bool HexitecCalibrationPlugin::getData(const char *filename, float *dataValue, float defaultValue)
  {
  	int i = 0;
		std::ifstream inFile;
		bool success = false;

		inFile.open(filename);

		if (!inFile)
		{
			LOG4CXX_TRACE(logger_, "Couldn't open file, using default values");

			for (int val = 0; val < image_pixels_; val ++)
			{
				dataValue[val] = defaultValue;
			}
		}

		while (inFile >> dataValue[i])
		{
			i++;
		}

		if (i < image_pixels_)
		{
			for (int val = i; val < image_pixels_; val ++)
			{
				dataValue[val] = defaultValue;
				if (i == val)
					LOG4CXX_TRACE(logger_, "Only found " << i << " values in " << filename
							<< " (Expected: " << image_pixels_ << "); Padding with default value: "
							<< defaultValue);
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

