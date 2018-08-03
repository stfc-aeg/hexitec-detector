/*
 * HexitecThresholdPlugin.cpp
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecThresholdPlugin.h>

namespace FrameProcessor
{

  const std::string HexitecThresholdPlugin::CONFIG_DROPPED_PACKETS = "packets_lost";
  const std::string HexitecThresholdPlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecThresholdPlugin::CONFIG_IMAGE_HEIGHT = "height";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecThresholdPlugin::HexitecThresholdPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
      packets_lost_(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecThresholdPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecThresholdPlugin constructor.");

    thresholdValue = 5;
    thresholdPerPixel = (uint16_t *) malloc(FEM_TOTAL_PIXELS * sizeof(uint16_t));
    memset(thresholdPerPixel, 0, FEM_TOTAL_PIXELS * sizeof(uint16_t));

    bThresholdsFromFile = true;

    if (bThresholdsFromFile)
    {
			std::string fname = "/u/ckd27546/develop/projects/odin-demo/hexitec-detector/data/frameProcessor/t_threshold_file.txt";
			LOG4CXX_TRACE(logger_, "Setting thresholds from file: " << fname);
			const char* filename = fname.c_str();
			bool bOK = setThresholdPerPixel(fname.c_str());

			LOG4CXX_TRACE(logger_, "CTOR, setThresholdPerPixel() returned: " << bOK);
    }
    else
    {
			LOG4CXX_TRACE(logger_, "Configured to use threshold value: " << thresholdValue);
    }

  }

  /**
   * Destructor.
   */
  HexitecThresholdPlugin::~HexitecThresholdPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecThresholdPlugin destructor.");

    /* DEVELOPMENT SPACE - for the other plug-ins' functionalities */

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
    if (config.has_param(HexitecThresholdPlugin::CONFIG_DROPPED_PACKETS))
    {
      packets_lost_ = config.get_param<int>(HexitecThresholdPlugin::CONFIG_DROPPED_PACKETS);
    }

    if (config.has_param(HexitecThresholdPlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecThresholdPlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecThresholdPlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecThresholdPlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

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
    status.set_param(get_name() + "/packets_lost", packets_lost_);
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecThresholdPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Preparing to apply threshold(s) to frame.");
    LOG4CXX_TRACE(logger_, "Frame size: " << frame->get_data_size());

    const Hexitec::FrameHeader* hdr_ptr =
        static_cast<const Hexitec::FrameHeader*>(frame->get_data());

    LOG4CXX_TRACE(logger_, "Raw frame number: " << hdr_ptr->frame_number);
    LOG4CXX_TRACE(logger_, "Frame state: " << hdr_ptr->frame_state);

    // Determine the size of the output thresholded image
    const std::size_t output_image_size = thresholded_image_size();
    LOG4CXX_TRACE(logger_, "Output image size: " << output_image_size);

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data()) + sizeof(Hexitec::FrameHeader)
    );

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

//      // Allocate buffer to receive reordered image.
//      reordered_image = (void*)malloc(output_image_size);
//      if (reordered_image == NULL)
//      {
//        throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
//      }
      // Allocate buffer to receive reordered image.
      thresholded_image = (void*)malloc(output_image_size);
      if (thresholded_image == NULL)
      {
        throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
      }

      // Calculate pointer into the input image data based on loop index
      void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

//      // Reorder pixels into the output image
//      reorder_pixels(static_cast<unsigned short *>(input_ptr),
//                     static_cast<unsigned short *>(reordered_image));


      // Compare pixels against the threshold, copying pixels that pass to the output image
      if (bThresholdsFromFile)
      {
      	processThresholdFile(static_cast<unsigned short *>(input_ptr),
											 static_cast<unsigned short *>(thresholded_image));
      }
      else
      {
      	processThresholdValue(static_cast<unsigned short *>(input_ptr),
      												 static_cast<unsigned short *>(thresholded_image));
      }

      /* Code for determining which directory code is run from
       * Hint, it is from /install */
//#include <stdio.h>  /* defines FILENAME_MAX */
//#ifdef WINDOWS
//    #include <direct.h>
//    #define GetCurrentDir _getcwd
//#else
//    #include <unistd.h>
//    #define GetCurrentDir getcwd
//#endif

//      char cCurrentPath[FILENAME_MAX];
//      if (!GetCurrentDir(cCurrentPath, sizeof(cCurrentPath)))
//      {
//        LOG4CXX_TRACE(logger_, "Couldn't get current dir !!");
//      }
//      else
//        cCurrentPath[sizeof(cCurrentPath) - 1] = '\0'; /* not really required */
//      LOG4CXX_TRACE(logger_, "The current working directory is: " << cCurrentPath);

      // Set the frame image to the thresholded image buffer if appropriate
      if (thresholded_image)
      {
        // Setup the frame dimensions
        dimensions_t dims(2);
        dims[0] = image_height_;
        dims[1] = image_width_;

        boost::shared_ptr<Frame> data_frame;
        data_frame = boost::shared_ptr<Frame>(new Frame("data"));

        data_frame->set_frame_number(hdr_ptr->frame_number);

        data_frame->set_dimensions(dims);
        data_frame->copy_data(thresholded_image, output_image_size);

        LOG4CXX_TRACE(logger_, "Pushing data frame.");
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

  /**
   * Determine the size of a reordered image size based on the counter depth.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t HexitecThresholdPlugin::thresholded_image_size() {

    return image_width_ * image_height_ * sizeof(unsigned short);

  }


  /**
   * (HexitecThresholdPlugin) Zero all pixels below thresholdValue's value
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the thresholded image is written.
   *
   */
  void HexitecThresholdPlugin::processThresholdValue(unsigned short* in, unsigned short* out)
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
//	  if (i < 40)
//  	    LOG4CXX_TRACE(logger_, "DEBUG, in[" << i << "] = " << in[i] << " out[" << i << "] = " << out[i] );
    }
  }

  /**
   * (HexitecThresholdPlugin) Zero all pixels below not meeting corresponding pixel threshold
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the thresholded image is written.
   *
   */
  void HexitecThresholdPlugin::processThresholdFile(unsigned short* in, unsigned short* out)
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
//	  if (i < 40)
//  	    LOG4CXX_TRACE(logger_, "DEBUG, in[" << i << "] = " << in[i] << " out[" << i << "] = " << out[i] );
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
      LOG4CXX_WARN(logger_, "Couldn't access threshold file, using default value instead");
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
					if (index < 15)
						 LOG4CXX_TRACE(logger_, "thresholdFromFile = " << thresholdFromFile << " thresholdPerPixel[" << index << " ] = " << thresholdPerPixel[index]);
					index++;
				}
			}
  	}

    LOG4CXX_TRACE(logger_, "And again: thresholdPerPixel: " << thresholdPerPixel[0] << " " << thresholdPerPixel[1] << " " << thresholdPerPixel[2]);
    LOG4CXX_TRACE(logger_, "index finished at: " << index);

    // If file do not contain enough threshold values for all pixels, assign default threshold to remaining pixels
    if (index < FEM_TOTAL_PIXELS)
    {
      for (int val = index; val < FEM_TOTAL_PIXELS; val ++)
      {
				if ( index < (val + 5))
					LOG4CXX_ERROR(logger_, "! filling in at val : " << val << " index: " << index);
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

