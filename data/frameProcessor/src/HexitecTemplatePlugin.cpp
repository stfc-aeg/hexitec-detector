/*
 * HexitecTemplatePlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecTemplatePlugin.h>

namespace FrameProcessor
{

  const std::string HexitecTemplatePlugin::CONFIG_DROPPED_PACKETS = "packets_lost";
  const std::string HexitecTemplatePlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecTemplatePlugin::CONFIG_IMAGE_HEIGHT = "height";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecTemplatePlugin::HexitecTemplatePlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
      packets_lost_(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecTemplatePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecTemplatePlugin constructor.");

  }

  /**
   * Destructor.
   */
  HexitecTemplatePlugin::~HexitecTemplatePlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecTemplatePlugin destructor.");
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
  void HexitecTemplatePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecTemplatePlugin::CONFIG_DROPPED_PACKETS))
    {
      packets_lost_ = config.get_param<int>(HexitecTemplatePlugin::CONFIG_DROPPED_PACKETS);
    }

    if (config.has_param(HexitecTemplatePlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecTemplatePlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecTemplatePlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecTemplatePlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecTemplatePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecTemplatePlugin");
    status.set_param(get_name() + "/packets_lost", packets_lost_);
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecTemplatePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Reordering frame.");
    LOG4CXX_TRACE(logger_, "Frame size: " << frame->get_data_size());

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
      reordered_image = (void*)malloc(output_image_size);
      if (reordered_image == NULL)
      {
        throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
      }

			// Calculate pointer into the input image data based on loop index
			void* input_ptr = static_cast<void *>(
					static_cast<char *>(const_cast<void *>(data_ptr)));

//        reorder_pixels(static_cast<unsigned short *>(input_ptr),
//                             static_cast<unsigned short *>(reordered_image));


      // Set the frame image to the reordered image buffer if appropriate
      if (reordered_image)
      {
        // Setup the frame dimensions
        dimensions_t dims(2);
        dims[0] = image_height_;
        dims[1] = image_width_;

        boost::shared_ptr<Frame> data_frame;
        data_frame = boost::shared_ptr<Frame>(new Frame("data"));

        data_frame->set_frame_number(hdr_ptr->frame_number);

        data_frame->set_dimensions(dims);
        data_frame->copy_data(reordered_image, output_image_size);

        LOG4CXX_TRACE(logger_, "Pushing data frame.");
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

  /**
   * Determine the size of a reordered image size based on the counter depth.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t HexitecTemplatePlugin::reordered_image_size() {

    return image_width_ * image_height_ * sizeof(unsigned short);

  }

} /* namespace FrameProcessor */

