/*
 * HexitecReorderPlugin.cpp
 *
 *  Created on: 11 Jul 2018
 *      Author: Christian Angelsen
 */

#include <HexitecReorderPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecReorderPlugin::CONFIG_DROPPED_PACKETS  = "packets_lost";
  const std::string HexitecReorderPlugin::CONFIG_RAW_DATA         = "raw_data";
  const std::string HexitecReorderPlugin::CONFIG_SENSORS_LAYOUT   = "sensors_layout";
  const std::string HexitecReorderPlugin::CONFIG_FRAME_NUMBER     = "frame_number";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecReorderPlugin::HexitecReorderPlugin() :
  		sensors_config_(Hexitec::sensorConfigTwo),
      image_width_(Hexitec::pixel_columns_per_sensor),
      image_height_(Hexitec::pixel_rows_per_sensor),
      image_pixels_(image_width_ * image_height_),
      packets_lost_(0),
      frame_number_(0),
      write_raw_data_(true)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecReorderPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecReorderPlugin version " <<
                  this->get_version_long() << " loaded.");

    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
    ///
    debugFrameCounter = 0;
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
   * to configure the plugin, and any response can be added to the reply IpcMessage. This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_    <=> sensors_layout
   * - packets_lost_          <=> dropped_packets
   * - write_raw_data_        <=> raw_data
   * - frame_number_          <=> frame_number
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecReorderPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecReorderPlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_ = config.get_param<std::string>(HexitecReorderPlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
    }

    if (config.has_param(HexitecReorderPlugin::CONFIG_DROPPED_PACKETS))
    {
      packets_lost_ = config.get_param<int>(HexitecReorderPlugin::CONFIG_DROPPED_PACKETS);
    }

    if (config.has_param(HexitecReorderPlugin::CONFIG_RAW_DATA))
    {
      write_raw_data_ = config.get_param<bool>(HexitecReorderPlugin::CONFIG_RAW_DATA);
    }

    if (config.has_param(HexitecReorderPlugin::CONFIG_FRAME_NUMBER))
    {
      frame_number_ = config.get_param<int>(HexitecReorderPlugin::CONFIG_FRAME_NUMBER);
      LOG4CXX_DEBUG(logger_, " *** RESET frame_number to be " << frame_number_);
    }
  }

  void HexitecReorderPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
  	// Return the configuration of the reorder plugin
  	std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecReorderPlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
    reply.set_param(base_str + HexitecReorderPlugin::CONFIG_DROPPED_PACKETS, packets_lost_);
    reply.set_param(base_str + HexitecReorderPlugin::CONFIG_RAW_DATA, write_raw_data_);
    reply.set_param(base_str + HexitecReorderPlugin::CONFIG_FRAME_NUMBER, frame_number_);
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
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/packets_lost", packets_lost_);
    status.set_param(get_name() + "/raw_data", write_raw_data_);
    status.set_param(get_name() + "/frame_number", frame_number_);
  }

  /**
   * Reset process plugin statistics, i.e. counter of packets lost
   */
  bool HexitecReorderPlugin::reset_statistics()
  {
    LOG4CXX_DEBUG(logger_, "Statistics reset requested for Reorder plugin")

    // Reset packets lost counter
    packets_lost_ = 0;
  }

  /**
   * Process and report lost UDP packets for the frame
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecReorderPlugin::process_lost_packets(boost::shared_ptr<Frame>& frame)
  {
    const Hexitec::FrameHeader* hdr_ptr = static_cast<const Hexitec::FrameHeader*>(frame->get_data_ptr());
    Hexitec::SensorConfigNumber sensors_config = static_cast<Hexitec::SensorConfigNumber>(sensors_config_);
    if (hdr_ptr->total_packets_received < Hexitec::num_fem_frame_packets(sensors_config)){
      int packets_lost = Hexitec::num_fem_frame_packets(sensors_config) - hdr_ptr->total_packets_received;
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

    Hexitec::FrameHeader* hdr_ptr = static_cast<Hexitec::FrameHeader*>(frame->get_data_ptr());

    this->process_lost_packets(frame);

    //TODO: Interrim fix: (until F/W amended)
    //	Changes header's frame number.
    hdr_ptr->frame_number = frame_number_;
    // Change frame's frame number otherwise FP's will erroneously
    //	display actual Hardware frame number
    frame->set_frame_number(frame_number_);

    LOG4CXX_TRACE(logger_, "Raw frame number: " << hdr_ptr->frame_number);

    // Determine the size of the output reordered image
    const std::size_t output_image_size = reordered_image_size();
    LOG4CXX_TRACE(logger_, "Output image size: " << output_image_size);

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()) + sizeof(Hexitec::FrameHeader)
    );

    // Define pointer to the input image data
    void* input_ptr = static_cast<void *>(
        static_cast<char *>(const_cast<void *>(data_ptr)));

    try
    {
      FrameMetaData processed_meta;

      // Frame meta data common to both datasets
      dimensions_t dims(2);
      dims[0] = image_height_;
      dims[1] = image_width_;
      processed_meta.set_dimensions(dims);
      processed_meta.set_compression_type(no_compression);
      processed_meta.set_data_type(raw_float);
      processed_meta.set_frame_number(hdr_ptr->frame_number);

      // For processed_frames dataset, reuse existing meta data as only the dataset name will differ

      // Set the dataset name
      processed_meta.set_dataset_name("processed_frames");

      boost::shared_ptr<Frame> data_frame;
      data_frame = boost::shared_ptr<Frame>(new DataBlockFrame(processed_meta,
        output_image_size));

      // Get a pointer to the data buffer in the output frame
      void* output_ptr = data_frame->get_data_ptr();

      // Turn unsigned short raw pixel data into float data type
      convert_pixels_without_reordering(static_cast<unsigned short *>(input_ptr),
                                        static_cast<float *>(output_ptr));

      const std::string& dataset = processed_meta.get_dataset_name();
      LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: " <<
                    data_frame->get_frame_number());
      this->push(data_frame);

      // Only construct raw data frame if configured
      if (write_raw_data_)
      {
        FrameMetaData raw_meta;

        // Frame meta data common to both datasets
        dimensions_t dims(2);
        dims[0] = image_height_;
        dims[1] = image_width_;
        raw_meta.set_dimensions(dims);
        raw_meta.set_compression_type(no_compression);
        raw_meta.set_data_type(raw_16bit);
        raw_meta.set_frame_number(hdr_ptr->frame_number);
        const std::size_t raw_image_size = image_width_ * image_height_ * sizeof(unsigned short);
        // Set the dataset name
        raw_meta.set_dataset_name("raw_frames");

        boost::shared_ptr<Frame> raw_frame;
        raw_frame = boost::shared_ptr<Frame>(new DataBlockFrame(raw_meta,
                                                                raw_image_size));

        // Get a pointer to the data buffer in the output frame
        void* output_ptr = raw_frame->get_data_ptr();

        // Turn unsigned short raw pixel data into unsigned short frame
        copy_pixels_without_reordering(static_cast<unsigned short *>(input_ptr),
          static_cast<unsigned short *>(output_ptr));

        LOG4CXX_TRACE(logger_, "Pushing raw_frames dataset, frame number: " <<
                      raw_frame->get_frame_number());
        this->push(raw_frame);
      }

      // Manually update frame_number (until fixed in firmware)
      frame_number_++;
    }
    catch (const std::exception& e)
    {
      LOG4CXX_ERROR(logger_, "HexitecReorderPlugin failed: " << e.what());
    }
  }

  /**
   * Determine the size of a reordered image.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t HexitecReorderPlugin::reordered_image_size()
  {
    return image_width_ * image_height_ * sizeof(float);
  }

  /**
   * Convert an image's pixels from unsigned short to float data type, do not reorder.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to the allocated memory where the converted image is written.
   *
   */
  void HexitecReorderPlugin::convert_pixels_without_reordering(unsigned short *in, float *out)
  {
    int index = 0;

    for (int i=0; i<image_pixels_; i++)
    {
      // Do not reorder pixels:
      out[i] = (float)in[i];
    }
  }

  /**
   * Convert an image's pixels from unsigned short to unsigned short data type.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to the allocated memory where the converted image is written.
   *
   */
  void HexitecReorderPlugin::copy_pixels_without_reordering(unsigned short *in, unsigned short *out)
  {
    int index = 0;

    for (int i=0; i<image_pixels_; i++)
    {
      out[i] = (float)in[i];
    }
  }

  /** Parse the number of sensors map configuration string.
   * 
   * This method parses a configuration string containing number of sensors mapping information,
   * which is expected to be of the format "NxN" e.g, 2x2. The map is saved in a member variable.
   * 
   * \param[in] sensors_layout_str - string of number of sensors configured
   * \return number of valid map entries parsed from string
   */
  std::size_t HexitecReorderPlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
  {
    // Clear the current map
    sensors_layout_.clear();

    // Define entry and port:idx delimiters
    const std::string entry_delimiter("x");

    // Vector to hold entries split from map
    std::vector<std::string> map_entries;

    // Split into entries
    boost::split(map_entries, sensors_layout_str, boost::is_any_of(entry_delimiter));

    // If a valid entry is found, save into the map
    if (map_entries.size() == 2) {
      int sensor_rows = static_cast<int>(strtol(map_entries[0].c_str(), NULL, 10));
      int sensor_columns = static_cast<int>(strtol(map_entries[1].c_str(), NULL, 10));
      sensors_layout_[0] = Hexitec::HexitecSensorLayoutMapEntry(sensor_rows, sensor_columns);
    }

    image_width_  = sensors_layout_[0].sensor_columns_ * Hexitec::pixel_columns_per_sensor;
    image_height_ = sensors_layout_[0].sensor_rows_ * Hexitec::pixel_rows_per_sensor;
    image_pixels_ = image_width_ * image_height_;

    // Return the number of valid entries parsed
    return sensors_layout_.size();
  }

  /// Debug function: Takes a file prefix, frame and writes all nonzero pixels to a file
  void HexitecReorderPlugin::writeFile(std::string filePrefix, float *frame)
  {
    std::ostringstream hitPixelsStream;
    hitPixelsStream << "-------------- frame " << debugFrameCounter << " --------------\n";
    for (int i = 0; i < image_pixels_; i++ )
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

