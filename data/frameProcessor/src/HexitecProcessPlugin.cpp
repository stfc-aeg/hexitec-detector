/*
 * HexitecProcessPlugin.cpp
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecProcessPlugin.h>

namespace FrameProcessor
{

  const std::string HexitecProcessPlugin::CONFIG_DROPPED_PACKETS = "packets_lost";
  const std::string HexitecProcessPlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecProcessPlugin::CONFIG_IMAGE_HEIGHT = "height";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecProcessPlugin::HexitecProcessPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
      packets_lost_(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecProcessPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecProcessPlugin constructor.");

    // Setup Pixel order lookup table
    if (!pixelMapInitialised)
    {
       initialisePixelMap();
       pixelMapInitialised = true;
    }

    /* DEVELOPMENT SPACE - for the other plug-ins' functionalities */


  }

  /**
   * Setup pixel look up table
   */
  void HexitecProcessPlugin::initialisePixelMap()
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
  HexitecProcessPlugin::~HexitecProcessPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecProcessPlugin destructor.");

    /* DEVELOPMENT SPACE - for the other plug-ins' functionalities */

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
  void HexitecProcessPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecProcessPlugin::CONFIG_DROPPED_PACKETS))
    {
      packets_lost_ = config.get_param<int>(HexitecProcessPlugin::CONFIG_DROPPED_PACKETS);
    }

    if (config.has_param(HexitecProcessPlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecProcessPlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecProcessPlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecProcessPlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecProcessPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecProcessPlugin");
    status.set_param(get_name() + "/packets_lost", packets_lost_);
  }

  /**
   * Process and report lost UDP packets for the frame
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecProcessPlugin::process_lost_packets(boost::shared_ptr<Frame> frame)
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
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecProcessPlugin::process_frame(boost::shared_ptr<Frame> frame)
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

      // Reorder pixels into the output image
      reorder_pixels(static_cast<unsigned short *>(input_ptr),
                     static_cast<unsigned short *>(reordered_image));

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
  std::size_t HexitecProcessPlugin::reordered_image_size() {

    return image_width_ * image_height_ * sizeof(unsigned short);

  }

  /**
   * Reorder an image's pixels into chronological order.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[out] out - Pointer to the allocated memory where the reordered image is written.
   *
   */
  void HexitecProcessPlugin::reorder_pixels(unsigned short* in, unsigned short* out)
  {
    int raw_addr = 0, x = 0, index = 0;

    for (int row=0; row<FEM_PIXELS_PER_ROW; row++)
    {
      for (int column=0; column<FEM_PIXELS_PER_COLUMN; column++)
      {
        // Re-order pixels:
      	index = pixelMap[raw_addr];
        out[index] = in[raw_addr];
        // Don't reorder:
//        out[raw_addr] = in[raw_addr];
//        if (row <1)
//        	LOG4CXX_TRACE(logger_, "REORDER, in[" << raw_addr << "] = " << in[raw_addr] << " out[" << index << "] = " << out[index] );
//        if (row < 1)
//          LOG4CXX_TRACE(logger_, " " << pixelMap[raw_addr] );
        raw_addr++;
      }
    }
  }


  /* ----------------------------------------------------------- */
  /* DEVELOPMENT SPACE - for the other plug-ins' functionalities */
  /* ----------------------------------------------------------- */



} /* namespace FrameProcessor */
