/*
 * HexitecSummedImagePlugin.cpp
 *
 *  Created on: 11 Jan 2021
 *      Author: Christian Angelsen
 */

#include <HexitecSummedImagePlugin.h>
#include <DebugLevelLogger.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecSummedImagePlugin::CONFIG_SENSORS_LAYOUT   = "sensors_layout";
  const std::string HexitecSummedImagePlugin::CONFIG_THRESHOLD_LOWER  = "threshold_lower";
  const std::string HexitecSummedImagePlugin::CONFIG_THRESHOLD_UPPER  = "threshold_upper";
  const std::string HexitecSummedImagePlugin::CONFIG_IMAGE_FREQUENCY  = "image_frequency";
  const std::string HexitecSummedImagePlugin::CONFIG_FRAMES_PROCESSED = "frames_processed";
  const std::string HexitecSummedImagePlugin::CONFIG_RESET_IMAGE      = "reset_image";
  const std::string HexitecSummedImagePlugin::CONFIG_RANK_INDEX       = "rank_index";
  const std::string HexitecSummedImagePlugin::CONFIG_RANK_OFFSET      = "rank_offset";
  const std::string HexitecSummedImagePlugin::CONFIG_FRAMES_PER_TRIGGER  = "frames_per_trigger";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecSummedImagePlugin::HexitecSummedImagePlugin() :
      rank_index_(0),
      rank_offset_(2),  // Default rank offset for Hexitec
      frames_per_trigger_(3),
      processed_frame_number_(0),
      frames_processed_(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecSummedImagePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecSummedImagePlugin version " <<
      this->get_version_long() << " loaded.");
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
    threshold_lower_ = 0;
    threshold_upper_ = 16382;
    image_frequency_ = 1;
    reset_image_ = 0;
    start_of_acquisition_ = true;
  }

  /**
   * Destructor.
   */
  HexitecSummedImagePlugin::~HexitecSummedImagePlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecSummedImagePlugin destructor.");
  }

  int HexitecSummedImagePlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecSummedImagePlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecSummedImagePlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecSummedImagePlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecSummedImagePlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Reset the frame number for the summed_image dataset.
   * 
   * The first frame of each trigger will increment frame number by rank offset.
   */
  void HexitecSummedImagePlugin::reset_frames_numbering()
  {
    processed_frame_number_ = rank_index_;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_  <=> sensors_layout
   * - threshold_lower_     <=> threshold_lower
   * - threshold_upper_     <=> threshold_upper
   * - image_frequency_     <=> image_frequency
   * - reset_image_         <=> reset_image
   * - frames_per_trigger_  <=> frames_per_trigger
   * - rank_index_          <=> rank_index
   * - rank_offset_         <=> rank_offset
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecSummedImagePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecSummedImagePlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_ =
        config.get_param<std::string>(HexitecSummedImagePlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_FRAMES_PER_TRIGGER))
    {
      frames_per_trigger_ = config.get_param<int>(HexitecSummedImagePlugin::CONFIG_FRAMES_PER_TRIGGER);
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Frames per trigger set to " << frames_per_trigger_);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_RANK_INDEX))
    {
      rank_index_ = config.get_param<int>(HexitecSummedImagePlugin::CONFIG_RANK_INDEX);
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Rank index set to " << rank_index_);
      reset_frames_numbering();
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_RANK_OFFSET))
    {
      rank_offset_ = config.get_param<int>(HexitecSummedImagePlugin::CONFIG_RANK_OFFSET);
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Rank offset set to " << rank_offset_);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_THRESHOLD_LOWER))
    {
      threshold_lower_ =
        config.get_param<unsigned int>(HexitecSummedImagePlugin::CONFIG_THRESHOLD_LOWER);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_THRESHOLD_UPPER))
    {
      threshold_upper_ =
        config.get_param<unsigned int>(HexitecSummedImagePlugin::CONFIG_THRESHOLD_UPPER);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_IMAGE_FREQUENCY))
    {
      image_frequency_ =
        config.get_param<unsigned int>(HexitecSummedImagePlugin::CONFIG_IMAGE_FREQUENCY);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_RESET_IMAGE))
    {
      reset_image_ =
        config.get_param<unsigned int>(HexitecSummedImagePlugin::CONFIG_RESET_IMAGE);

      if (reset_image_ == 1)
      {
        frames_processed_ = 0;
        reset_image_ = 0;
      }
    }
  }

  void HexitecSummedImagePlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_THRESHOLD_LOWER, threshold_lower_);
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_THRESHOLD_UPPER, threshold_upper_);
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_IMAGE_FREQUENCY, image_frequency_);
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_FRAMES_PROCESSED, frames_processed_);
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_RESET_IMAGE, reset_image_);
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_RANK_INDEX, rank_index_);
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_RANK_OFFSET, rank_offset_);
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_FRAMES_PER_TRIGGER, frames_per_trigger_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecSummedImagePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Status requested for HexitecSummedImagePlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/threshold_lower", threshold_lower_);
    status.set_param(get_name() + "/threshold_upper", threshold_upper_);
    status.set_param(get_name() + "/image_frequency", image_frequency_);
    status.set_param(get_name() + "/frames_processed", frames_processed_);
    status.set_param(get_name() + "/reset_image", reset_image_);
    status.set_param(get_name() + "/rank_index", rank_index_);
    status.set_param(get_name() + "/rank_offset", rank_offset_);
    status.set_param(get_name() + "/frames_per_trigger", frames_per_trigger_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecSummedImagePlugin::reset_statistics(void)
  {
    // Nowt to reset..?
    return true;
  }

  /** Process an EndOfAcquisition Frame.
  *
  * Push Summed Data set on end of acquisition
  */
  void HexitecSummedImagePlugin::process_end_of_acquisition()
  {
    LOG4CXX_DEBUG_LEVEL(2, logger_, "End of acquisition frame received, pushing dataset");
    if (frames_processed_ > 0)
    {
      this->push(summed_image_);
    }
    reset_frames_numbering();
    start_of_acquisition_ = true;
  }

  /**
   * Perform processing on the frame.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecSummedImagePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();
    long long frame_number = incoming_frame_meta.get_frame_number();

    if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        if (start_of_acquisition_)
        {
          start_of_acquisition_ = false;
          initialise_summed_image();
        }

        // Get a pointer to the data buffer in the output frame
        void* output_ptr = summed_image_->get_data_ptr();

        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        // Apply algorithm
        apply_summed_image_algorithm(static_cast<float *>(input_ptr),
          static_cast<uint32_t *>(output_ptr));
        frames_processed_ += 1;

        LOG4CXX_DEBUG_LEVEL(2, logger_, "Pushing " << dataset << ", frame number "<< frame_number);
        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "HexitecSummedImagePlugin failed: " << e.what());
      }
    }
    else
    {
      // Push dataset
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Pushing " << dataset << ", frame number "
        << frame_number);
      this->push(frame);
    }

  }

  /**
   * Apply summed image algorithm.
   *
   * This method determine which pixel(s) have values between threshold_lower_and threshold_upper_
   * and marking these in summed_image_ by incrementing them by 1, accumulating repeatedly hit
   * pixels across frames.
   *
   * \param[frame] frame - Pointer to a frame object.
   */
  void HexitecSummedImagePlugin::apply_summed_image_algorithm(float *in, uint32_t *out)
  {
    for (int i=0; i<image_pixels_; i++)
    {
      if (((uint32_t)in[i] > threshold_lower_) && ((uint32_t)in[i] < threshold_upper_))
      {
        out[i] += 1;
      }
    }
  }

  /**
   * Initialise summed image frame
   */
  void HexitecSummedImagePlugin::initialise_summed_image()
  {
    try
    {
      FrameMetaData summed_image_meta;

      // Frame meta data common to both datasets
      dimensions_t dims(2);
      dims[0] = image_height_;
      dims[1] = image_width_;
      summed_image_meta.set_dimensions(dims);
      summed_image_meta.set_compression_type(no_compression);
      summed_image_meta.set_data_type(raw_32bit);
      summed_image_meta.set_frame_number(processed_frame_number_);

      // Determine the size of the image
      const std::size_t summed_image_size = image_width_ * image_height_ * sizeof(uint32_t);

      // Set the dataset name
      summed_image_meta.set_dataset_name("summed_images");

      summed_image_ = boost::shared_ptr<Frame>(new DataBlockFrame(summed_image_meta, summed_image_size));

      // Get a pointer to the data buffer in the output frame
      void* output_ptr = static_cast<float *>(summed_image_->get_data_ptr());

      // Ensure frame is empty
      memset(output_ptr, 0, summed_image_size);

    }
    catch (const std::exception& e)
    {
      LOG4CXX_ERROR(logger_, "Failed to initialise stacked frame: " << e.what());
    }
  }


  /**
   * Parse the number of sensors map configuration string.
   * 
   * This method parses a configuration string containing number of sensors mapping information,
   * which is expected to be of the format "NxN" e.g, 2x2. The map's saved in a member variable.
   * 
   * \param[in] sensors_layout_str - string of number of sensors configured
   * \return number of valid map entries parsed from string
   */
  std::size_t HexitecSummedImagePlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
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

    image_width_ = sensors_layout_[0].sensor_columns_ * Hexitec::pixel_columns_per_sensor;
    image_height_ = sensors_layout_[0].sensor_rows_ * Hexitec::pixel_rows_per_sensor;
    image_pixels_ = image_width_ * image_height_;

    // Return the number of valid entries parsed
    return sensors_layout_.size();
  }

} /* namespace FrameProcessor */
