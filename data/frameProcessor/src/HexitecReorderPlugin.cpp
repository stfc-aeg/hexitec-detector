/*
 * HexitecReorderPlugin.cpp
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecReorderPlugin.h>
#include "version.h"

namespace FrameProcessor
{

  const std::string HexitecReorderPlugin::CONFIG_DROPPED_PACKETS = "packets_lost";
  const std::string HexitecReorderPlugin::CONFIG_IMAGE_WIDTH 		 = "width";
  const std::string HexitecReorderPlugin::CONFIG_IMAGE_HEIGHT 	 = "height";
  const std::string HexitecReorderPlugin::CONFIG_ENABLE_REORDER  = "reorder";
  const std::string HexitecReorderPlugin::CONFIG_RAW_DATA 			 = "raw_data";
  /**
   * The constructor sets up logging used within the class.
   */
  HexitecReorderPlugin::HexitecReorderPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
      packets_lost_(0),
			reorder_pixels_(true),
			write_raw_data_(true)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecReorderPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecReorderPlugin version " <<
    												this->get_version_long() << " loaded.");

    // Setup Pixel order lookup table
    if (!pixelMapInitialised)
    {
       initialisePixelMap();
       pixelMapInitialised = true;
    }
    ///
    debugFrameCounter = 0;

  }

  /**
   * Setup pixel look up table
   */
  void HexitecReorderPlugin::initialisePixelMap()
  {
     int pmIndex = 0;

     for (int row = 0; row < 80; row++)
     {
        for (int col = 0; col < 20; col++)
        {
           for (int pix = 0; pix < 80; pix+=20)
           {
              pixelMap[pmIndex] = pix + col +(row * 80);
              pmIndex++;
           }
        }
     }
  }

  /**
   * Destructor.
   */
  HexitecReorderPlugin::~HexitecReorderPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecReorderPlugin destructor.");
  }

  int HexitecReorderPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecReorderPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecReorderPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecReorderPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecReorderPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - (bitdepth) - Removed
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecReorderPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecReorderPlugin::CONFIG_DROPPED_PACKETS))
    {
      packets_lost_ = config.get_param<int>(HexitecReorderPlugin::CONFIG_DROPPED_PACKETS);
    }

    if (config.has_param(HexitecReorderPlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecReorderPlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecReorderPlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecReorderPlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

    if (config.has_param(HexitecReorderPlugin::CONFIG_ENABLE_REORDER))
    {
      reorder_pixels_ = config.get_param<bool>(HexitecReorderPlugin::CONFIG_ENABLE_REORDER);
    }

    if (config.has_param(HexitecReorderPlugin::CONFIG_RAW_DATA))
    {
      write_raw_data_ = config.get_param<bool>(HexitecReorderPlugin::CONFIG_RAW_DATA);
    }

  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecReorderPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecReorderPlugin");
    status.set_param(get_name() + "/packets_lost", packets_lost_);
  }

  /**
   * Process and report lost UDP packets for the frame
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecReorderPlugin::process_lost_packets(boost::shared_ptr<Frame> frame)
  {
    const Hexitec::FrameHeader* hdr_ptr = static_cast<const Hexitec::FrameHeader*>(frame->get_data());
    LOG4CXX_DEBUG(logger_, "Processing lost packets for frame " << hdr_ptr->frame_number);
    LOG4CXX_DEBUG(logger_, "Packets received: " << hdr_ptr->total_packets_received
                                                << " out of a maximum "
                                                << Hexitec::num_fem_frame_packets());
    if (hdr_ptr->total_packets_received < Hexitec::num_fem_frame_packets()){
      int packets_lost = Hexitec::num_fem_frame_packets() - hdr_ptr->total_packets_received;
      LOG4CXX_ERROR(logger_, "Frame number " << hdr_ptr->frame_number << " has dropped " << packets_lost << " packet(s)");
      packets_lost_ += packets_lost;
      LOG4CXX_ERROR(logger_, "Total packets lost since startup " << packets_lost_);
    }
  }

  /**
   * Perform processing on the frame.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecReorderPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Reordering frame.");
    LOG4CXX_TRACE(logger_, "Frame size: " << frame->get_data_size());

    this->process_lost_packets(frame);

    const Hexitec::FrameHeader* hdr_ptr =
        static_cast<const Hexitec::FrameHeader*>(frame->get_data());

    LOG4CXX_TRACE(logger_, "Raw frame number: " << hdr_ptr->frame_number);
    LOG4CXX_TRACE(logger_, "Frame state: " << hdr_ptr->frame_state);
    LOG4CXX_TRACE(logger_, "Packets received: " << hdr_ptr->total_packets_received
        << " SOF markers: "<< (int)hdr_ptr->total_sof_marker_count
        << " EOF markers: "<< (int)hdr_ptr->total_eof_marker_count);

    // Determine the size of the output reordered image
    const std::size_t output_image_size = reordered_image_size();
    LOG4CXX_TRACE(logger_, "Output image size: " << output_image_size);

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data()) + sizeof(Hexitec::FrameHeader)
    );

    // Define pointer to the input image data
    void* input_ptr = static_cast<void *>(
        static_cast<char *>(const_cast<void *>(data_ptr)));

    // Pointer to raw image buffer
    void* raw_image = NULL;

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

      // Allocate buffer for raw data in float data type.
      raw_image = (void*)malloc(output_image_size);
      if (raw_image == NULL)
      {
        throw std::runtime_error("Failed to allocate temporary buffer for raw image");
      }

      if (reorder_pixels_)
      {
      	reorder_pixels(static_cast<unsigned short *>(input_ptr),
						static_cast<float *>(raw_image));
      }
      else
      {
				// Turn unsigned short raw pixel data into float data type raw pixel data
				convert_pixels_without_reordering(static_cast<unsigned short *>(input_ptr),
																					static_cast<float *>(raw_image));
      }
      ///
//      writeFile("All_540_frames_", static_cast<float *>(raw_image));
//      debugFrameCounter += 1;
      ///

      if (raw_image)
      {
				// Setup of the frame dimensions
				dimensions_t dims(2);
				dims[0] = image_height_;
				dims[1] = image_width_;

				// Only construct raw data frame if configured
      	if(write_raw_data_)
      	{
					boost::shared_ptr<Frame> raw_frame;
					raw_frame = boost::shared_ptr<Frame>(new Frame("raw_frames"));

					raw_frame->set_frame_number(hdr_ptr->frame_number);

					raw_frame->set_dimensions(dims);
					raw_frame->copy_data(raw_image, output_image_size);


					LOG4CXX_TRACE(logger_, "Pushing raw_frames dataset, frame number: "
																 << frame->get_frame_number());
					this->push(raw_frame);
      	}

				boost::shared_ptr<Frame> data_frame;
				data_frame = boost::shared_ptr<Frame>(new Frame("data"));

				data_frame->set_frame_number(hdr_ptr->frame_number);

				data_frame->set_dimensions(dims);
				data_frame->copy_data(raw_image, output_image_size);

				LOG4CXX_TRACE(logger_, "Pushing data dataset, frame number: "
															 << frame->get_frame_number());
				this->push(data_frame);

  			free(raw_image);
        raw_image = NULL;
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
   * Determine the size of a reordered image.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t HexitecReorderPlugin::reordered_image_size() {

    return image_width_ * image_height_ * sizeof(float);

  }

  /**
   * Reorder an image's pixels into geographical order.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to the allocated memory where the reordered image is written.
   *
   */
  void HexitecReorderPlugin::reorder_pixels(unsigned short *in, float *out)
  {
    int index = 0;

    for (int i=0; i<FEM_TOTAL_PIXELS; i++)
    {
        // Re-order pixels:
      	index = pixelMap[i];
				out[index] = (float)in[i];
    }
  }

  /**
   * Convert an image's pixels from unsigned short to float data type, and reorder.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to the allocated memory where the converted image is written.
   *
   */
  void HexitecReorderPlugin::convert_pixels_without_reordering(unsigned short *in, float *out)
  {
    int index = 0;

    for (int i=0; i<FEM_TOTAL_PIXELS; i++)
    {
				// Do not reorder pixels:
				out[i] = (float)in[i];
    }
  }

  //// Debug function: Takes a file prefix, frame and writes all nonzero pixels to a file
	void HexitecReorderPlugin::writeFile(std::string filePrefix, float *frame)
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
			 + std::string("_ODIN_Reorder_detailed.txt");
		outFile.open(fname.c_str(), std::ofstream::app);
		outFile.write((const char *)hitPixelsString.c_str(), hitPixelsString.length() * sizeof(char));
		outFile.close();
	}

} /* namespace FrameProcessor */

