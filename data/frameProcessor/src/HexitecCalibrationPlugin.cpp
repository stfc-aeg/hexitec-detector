/*
 * HexitecCalibrationPlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecCalibrationPlugin.h>

namespace FrameProcessor
{

  const std::string HexitecCalibrationPlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecCalibrationPlugin::CONFIG_IMAGE_HEIGHT = "height";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecCalibrationPlugin::HexitecCalibrationPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
			gradientsStatus(false),
			interceptsStatus(false),
			gradientFilename(NULL),
			interceptFilename(NULL),
			gradientValue(1),
			interceptValue(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecCalibrationPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecCalibrationPlugin constructor.");

  }

  /**
   * Destructor.
   */
  HexitecCalibrationPlugin::~HexitecCalibrationPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecCalibrationPlugin destructor.");
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
    const std::size_t calibrated_image_size = reordered_image_size();

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

				// Allocate buffer to receive reordered image.
				reordered_image = (void*)malloc(calibrated_image_size);
				if (reordered_image == NULL)
				{
					throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
				}

				// Calculate pointer into the input image data based on loop index
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

	//        reorder_pixels(static_cast<float *>(input_ptr),
	//                             static_cast<float *>(reordered_image));


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
					data_frame->copy_data(reordered_image, calibrated_image_size);

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
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where
   * 										the calibrated pixels will be stored.
   */
  void HexitecCalibrationPlugin::calibrate_pixels(float* in, float* out)
  {

    for (int i=0; i<FEM_TOTAL_PIXELS; i++)
    {
     		out[i] = in[i];

    }
//    for(index = 0; index < 162; index++)
//    {
//      if (index < 15)
//        LOG4CXX_TRACE(logger_, "REORDER, out[" << index << "] = " << out[index]);
//    }
//    LOG4CXX_TRACE(logger_, " *** reorder_pixels(), TAKE OUT THIS PIXEL HACK! ***");
  }

  void HexitecCalibrationPlugin::setGradients()
  {
     double defaultValue = 1;
     gradientsStatus = getData(gradientFilename, gradientValue, defaultValue);
  }

  void HexitecCalibrationPlugin::setIntercepts()
  {
     double defaultValue = 0;
     interceptsStatus = getData(interceptFilename, interceptValue, defaultValue);
  }

  bool HexitecCalibrationPlugin::getData(char *filename, double *dataValue, double defaultValue)
  {
     int i = 0;
     std::ifstream inFile;
     bool success = false;

     inFile.open(filename);

     if (!inFile)
     {
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

