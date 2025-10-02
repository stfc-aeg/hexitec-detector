/*
 * HexitecStackedPlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: Christian Angelsen
 */

#include <HexitecStackedPlugin.h>
#include <DebugLevelLogger.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecStackedPlugin::CONFIG_SENSORS_LAYOUT       = "sensors_layout";
  const std::string HexitecStackedPlugin::CONFIG_RANK_INDEX           = "rank_index";
  const std::string HexitecStackedPlugin::CONFIG_RANK_OFFSET          = "rank_offset";
  const std::string HexitecStackedPlugin::CONFIG_FRAMES_PER_TRIGGER   = "frames_per_trigger";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecStackedPlugin::HexitecStackedPlugin() :
      rank_index_(0),
      rank_offset_(2),  // Default rank offset for Hexitec
      frames_per_trigger_(3),
      stacked_frame_number_(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecStackedPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecStackedPlugin version " <<
      this->get_version_long() << " loaded.");

    // Set image_width_, image_height_, image_pixels_
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
  }

  /**
   * Destructor.
   */
  HexitecStackedPlugin::~HexitecStackedPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecStackedPlugin destructor.");
  }

  int HexitecStackedPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecStackedPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecStackedPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecStackedPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecStackedPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Reset the frame number for the stacked frame dataset.
   * 
   * The first frame of each trigger will increment frame number by rank offset.
   */
  void HexitecStackedPlugin::reset_frames_numbering()
  {
    stacked_frame_number_ = rank_index_;
  }

  void HexitecStackedPlugin::initialise_stacked_frame()
  {
    try
    {
      FrameMetaData stacked_meta;

      // Frame meta data
      dimensions_t dims(2);
      dims[0] = image_height_;
      dims[1] = image_width_;
      stacked_meta.set_dimensions(dims);
      stacked_meta.set_compression_type(no_compression);
      stacked_meta.set_data_type(raw_float);
      stacked_meta.set_frame_number(stacked_frame_number_);

      // Determine the size of the image
      const std::size_t output_image_size = image_width_ * image_height_ * sizeof(float);

      // Set the dataset name
      stacked_meta.set_dataset_name("stacked_frames");

      stacked_frame_ = boost::shared_ptr<Frame>(new DataBlockFrame(stacked_meta, output_image_size));

      // Get a pointer to the data buffer in the output frame
      void* output_ptr = static_cast<float *>(stacked_frame_->get_data_ptr());

      // Ensure frame is empty
      memset(output_ptr, 0, output_image_size);

      LOG4CXX_DEBUG_LEVEL(2, logger_, "Initialised stacked frame, number: " << stacked_frame_number_
        << " address: " << stacked_frame_);
    }
    catch (const std::exception& e)
    {
      LOG4CXX_ERROR(logger_, "Failed to initialise stacked frame: " << e.what());
    }
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - frames_per_trigger_  <=> frames_per_trigger
   * - rank_index_          <=> rank_index
   * - rank_offset_         <=> rank_offset
   * - sensors_layout_str_  <=> sensors_layout
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecStackedPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecStackedPlugin::CONFIG_FRAMES_PER_TRIGGER))
    {
      frames_per_trigger_ = config.get_param<int>(HexitecStackedPlugin::CONFIG_FRAMES_PER_TRIGGER);
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Frames per trigger set to: " << frames_per_trigger_);
    }

    if (config.has_param(HexitecStackedPlugin::CONFIG_RANK_INDEX))
    {
      rank_index_ = config.get_param<int>(HexitecStackedPlugin::CONFIG_RANK_INDEX);
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Rank index set to: " << rank_index_);
      reset_frames_numbering();
    }

    if (config.has_param(HexitecStackedPlugin::CONFIG_RANK_OFFSET))
    {
      rank_offset_ = config.get_param<int>(HexitecStackedPlugin::CONFIG_RANK_OFFSET);
      LOG4CXX_DEBUG_LEVEL(2, logger_, "Rank offset set to: " << rank_offset_);
    }

    if (config.has_param(HexitecStackedPlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_ =
        config.get_param<std::string>(HexitecStackedPlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
    }
  }

  void HexitecStackedPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecStackedPlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
    reply.set_param(base_str + HexitecStackedPlugin::CONFIG_FRAMES_PER_TRIGGER, frames_per_trigger_);
    reply.set_param(base_str + HexitecStackedPlugin::CONFIG_RANK_INDEX, rank_index_);
    reply.set_param(base_str + HexitecStackedPlugin::CONFIG_RANK_OFFSET, rank_offset_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecStackedPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Status requested for HexitecStackedPlugin");
    status.set_param(get_name() + "/frames_per_trigger", frames_per_trigger_);
    status.set_param(get_name() + "/rank_index", rank_index_);
    status.set_param(get_name() + "/rank_offset", rank_offset_);
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecStackedPlugin::reset_statistics(void)
  {
    // Nowt to reset..?
    return true;
  }

  /** Process an EndOfAcquisition Frame.
  *
  * This method is called when an EndOfAcquisition frame is received.
  */
  void HexitecStackedPlugin::process_end_of_acquisition()
  {
    LOG4CXX_DEBUG_LEVEL(2, logger_, "EoA: Pushing stacked frame, number: "
      << stacked_frame_->get_frame_number() << ", rank: " << rank_index_);
    this->push(stacked_frame_);

    reset_frames_numbering();
  }

  /**
   * Perform processing on the frame.  
   * 
   * Sums all N frames per trigger into one stacked frame.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecStackedPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();

    if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        // First frame of the trigger?
        if (frame->get_frame_number() % frames_per_trigger_ == 0)
        {
          initialise_stacked_frame();
        }

        // Get a pointer to the data buffer in the output frame
        void* output_ptr = stacked_frame_->get_data_ptr();

        // Add this frame's contribution onto stacked frame
        stack_current_frame(static_cast<float *>(input_ptr), static_cast<float *>(output_ptr));

        LOG4CXX_DEBUG_LEVEL(2, logger_, "Pushing processed_frames, number: " << frame->get_frame_number());
        // Pass on processed_frames dataset unmodified:
        this->push(frame);

        // Final frame of current trigger?
        if (frame->get_frame_number() % frames_per_trigger_ == (frames_per_trigger_ - 1))
        {
          LOG4CXX_DEBUG_LEVEL(2, logger_, dataset << " Final frame, pushing stacked frame: "
            << stacked_frame_number_ << " address: " << stacked_frame_);
          this->push(stacked_frame_);
          stacked_frame_number_ += rank_offset_;
        }
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "HexitecStackedPluginfailed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << dataset << " dataset, frame number: "
                                        << frame->get_frame_number());
      this->push(frame);
    }
  }

  /**
   * Add current frame to stacked frame.
   *
   * \param[in] in - Pointer to the incoming processed frame data.
   * \param[in] out - Pointer to the allocated memory of the stacked image.
   *
   */
  void HexitecStackedPlugin::stack_current_frame(float *in, float *out)
  {
    float total_in = 0.0f;
    float total_out = 0.0f;
    for (int i=0; i<image_pixels_; i++)
    {
      out[i] += in[i];
      total_out += out[i];  // DEBUG
      total_in += in[i];    // DEBUG
    }
    LOG4CXX_DEBUG_LEVEL(2, logger_, "Stacked frame: " << stacked_frame_number_
      << " stacked_frame total: " << total_out << " of which processed_frames added: "
      << total_in << " stacked_frame address: " << out);
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
  std::size_t HexitecStackedPlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
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
