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
      frames_processed_(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecStackedPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecStackedPlugin version " <<
      this->get_version_long() << " loaded.");

    // Set image_width_, image_height_, image_pixels_
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
    triggers_received_ = rapidjson::kArrayType;
    triggers_processed_ = rapidjson::kArrayType;
    triggers_incomplete_ = rapidjson::kArrayType;
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

  /** Initialise the stacked frame for the current trigger.
   *
   * \param[in] current_trigger - Pointer to the current TriggerObject.
   */
  void HexitecStackedPlugin::initialise_stacked_frame(TriggerObject* current_trigger)
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

      stacked_meta.set_frame_number(current_trigger->trigger_number);

      // Determine the size of the image
      const std::size_t output_image_size = image_width_ * image_height_ * sizeof(float);

      // Set the dataset name
      stacked_meta.set_dataset_name("stacked_frames");

      current_trigger->stacked_frame_ = boost::shared_ptr<Frame>(new DataBlockFrame(stacked_meta, output_image_size));

      // Get a pointer to the data buffer in the output frame
      void* output_ptr = static_cast<float *>(current_trigger->stacked_frame_->get_data_ptr());

      // Ensure frame is empty
      memset(output_ptr, 0, output_image_size);

      LOG4CXX_DEBUG_LEVEL(2, logger_, "Initialised stacked frame " << current_trigger->trigger_number);
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
    status.set_param(get_name() + "/frames_processed", frames_processed_);
    status.set_param(get_name() + "/rank_index", rank_index_);
    status.set_param(get_name() + "/rank_offset", rank_offset_);
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/triggers_received", triggers_received_);
    status.set_param(get_name() + "/triggers_processed", triggers_processed_);
    status.set_param(get_name() + "/triggers_incomplete", triggers_incomplete_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecStackedPlugin::reset_statistics(void)
  {
    // Nowt to reset..?
    LOG4CXX_DEBUG_LEVEL(2, logger_, "Resetting HexitecStackedPlugin statistics.");
    frames_processed_ = 0;
    triggers_received_.SetArray();
    triggers_processed_.SetArray();
    triggers_incomplete_.SetArray();
    return true;
  }

  /** Process an EndOfAcquisition Frame.
  *
  * This method is called when an EndOfAcquisition frame is received.
  */
  void HexitecStackedPlugin::process_end_of_acquisition()
  {
    LOG4CXX_DEBUG_LEVEL(2, logger_, "EoA: There are " << trigger_objects_.size() << " trigger(s) to push");
    for (auto& trigger_object : trigger_objects_)
    {
      LOG4CXX_DEBUG_LEVEL(2, logger_, "EoA: Pushing stacked frame, trigger "
        << trigger_object.trigger_number  << " with " << trigger_object.frames_received.size()
        << " frames");
      this->push(trigger_object.stacked_frame_);
      triggers_processed_.PushBack(trigger_object.trigger_number, triggers_processed_allocator_);
      triggers_incomplete_.PushBack(trigger_object.trigger_number, triggers_incomplete_allocator_);
    }
    trigger_objects_.clear();
  }

  /**
   * Determine whether frame is the first received of a trigger.
   * 
   * \param[in] frame - Frame number to search for.
   * \return true if first frame of trigger, false otherwise.
   */
  bool HexitecStackedPlugin::first_frame_of_trigger(int frame)
  {
    for (rapidjson::SizeType i = 0; i < triggers_received_.Size(); i++) {
        if (triggers_received_[i].IsInt() && triggers_received_[i].GetInt() == frame) {
            LOG4CXX_DEBUG_LEVEL(3, logger_, "Trigger: " << frame << " (at index " << i 
              << ") already seen. Don't create new TriggerObject.");
            return false;
        }
    }
    return true;
  }

  /**
   * Determine whether frame belongs to an already processed trigger
   *
   * \param[in] frame - Frame number to search for.
   * \return true if trigger already processed, false otherwise.
   */
  bool HexitecStackedPlugin::trigger_already_processed(int frame)
  {
    for (rapidjson::SizeType i = 0; i < triggers_processed_.Size(); i++) {
        if (triggers_processed_[i].IsInt() && triggers_processed_[i].GetInt() == frame) {
            LOG4CXX_DEBUG_LEVEL(3, logger_, "Trigger: " << frame << " (at index " << i
              << ") already processed. Don't process.");
            return true;
        }
    }
    return false;
  }

  /**
   * Check whether frame already received.
   * 
   * \param[in] trigger_object - Pointer to TriggerObject.
   * \param[in] frame_number - Frame number to search for.
   * \return true if frame already received, false otherwise.
   */
  bool HexitecStackedPlugin::frame_already_received(TriggerObject* trigger_object, int frame_number)
  {
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Checking if trigger " << trigger_object->trigger_number
      << " frame " << frame_number << " already received.");
    for (const auto& received_frame : trigger_object->frames_received)
    {
      LOG4CXX_DEBUG_LEVEL(3, logger_, "Comparing received frame: " << received_frame <<
        " (vs incoming frame: " << frame_number << ")");
      if (received_frame == frame_number)
      {
        return true;
      }
    }
    return false;
  }

  /**
   * Get number of frames received for trigger.
   * 
   * \param[in] trigger_object - Pointer to TriggerObject.
   * \return Number of frames received.
   */
  int HexitecStackedPlugin::get_number_of_frames_received(TriggerObject* trigger_object)
  {
    if (trigger_object)
    {
      return trigger_object->frames_received.size();
    }
    return 0;
  }

  /**
   * Get trigger of associated trigger number.
   *
   * \param[in] trigger_number - Trigger number to search for.
   * \return Pointer to TriggerObject if found, nullptr otherwise.
   */
  TriggerObject* HexitecStackedPlugin::get_trigger_object(int trigger_number)
  {
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Retrieving TriggerObject for trigger number: " << trigger_number);
    for (auto& trigger_object : trigger_objects_)
    {
      if (trigger_object.trigger_number == trigger_number)
      {
        return &trigger_object;
      }
    }
    return nullptr;
  }

  /**
   * Erase trigger of associated trigger number.
   * 
   * \param[in] trigger_number - Trigger number whose trigger object to erase.
   * \return true if found and erased, false otherwise.
   */
  bool HexitecStackedPlugin::erase_trigger_object(int trigger_number)
  {
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Finding TriggerObject of trigger " << trigger_number << " to erase");
    auto trigger_to_erase = std::remove_if(trigger_objects_.begin(), trigger_objects_.end(),
      [trigger_number](const TriggerObject& obj) { return obj.trigger_number == trigger_number; });

    if (trigger_to_erase != trigger_objects_.end())
    {
      trigger_objects_.erase(trigger_to_erase, trigger_objects_.end());
      return true;
    }
    else
      return false;
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
    long long frame_number = incoming_frame_meta.get_frame_number();

    if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        // Which trigger does frame belong to?
        int trigger_number = int(frame_number / frames_per_trigger_);

        if (trigger_already_processed(trigger_number))
        {
          // Blocks processed_frames, but not raw_frames.. Move that this protection earlier?
          LOG4CXX_ERROR(logger_, "Trigger " << trigger_number << " already processed, skipping frame "
            << frame_number << ".");
          return;
        }

        TriggerObject* current_trigger = nullptr;
        // First frame of the trigger?
        if (first_frame_of_trigger(trigger_number))
        {
          LOG4CXX_DEBUG_LEVEL(3, logger_, "New First frame (" << frame_number << ") of trigger "
            << trigger_number);
          current_trigger = new TriggerObject();
          current_trigger->trigger_number = trigger_number;
          current_trigger->frames_received.insert(frame_number);
          initialise_stacked_frame(current_trigger);
          // Note new trigger number we have received frame belonging to
          triggers_received_.PushBack(trigger_number, triggers_received_allocator_);
          // Save trigger object to vector for later retrieval
          trigger_objects_.push_back(*current_trigger);
        }
        else
        {
          LOG4CXX_DEBUG_LEVEL(3, logger_, "Not first frame (" << frame_number << ") of trigger "
            << trigger_number);
          current_trigger = get_trigger_object(trigger_number);
          if (current_trigger == nullptr)
          {
            LOG4CXX_ERROR(logger_, "Could not find existing TriggerObject for trigger number "
              << trigger_number);
            return;
          }
          if (frame_already_received(current_trigger, frame_number))
          {
            LOG4CXX_ERROR(logger_, "Duplicate frame number " << frame_number
              << " received for trigger " << trigger_number << ", skipping frame.");
            return;
          }
          current_trigger->frames_received.insert(frame_number);
        }

        // Get a pointer to the data buffer in the output frame
        void* output_ptr = current_trigger->stacked_frame_->get_data_ptr();

        // Add this frame's contribution onto stacked frame
        stack_current_frame(static_cast<float *>(input_ptr), static_cast<float *>(output_ptr));
        frames_processed_++;

        LOG4CXX_DEBUG_LEVEL(2, logger_, "Pushing processed_frames, number: " << frame_number);
        // Pass on processed_frames dataset unmodified:
        this->push(frame);

        // Final frame of current trigger?
        if (get_number_of_frames_received(current_trigger) == frames_per_trigger_)
        {
          LOG4CXX_DEBUG_LEVEL(3, logger_, "Trigger " << trigger_number << " all frames ("
            << frames_per_trigger_ << ") received, pushing stacked frame.");
          this->push(current_trigger->stacked_frame_);
          // Remove current_trigger from trigger_objects_ vector
          if (!erase_trigger_object(trigger_number))
          {
            LOG4CXX_ERROR(logger_, "Failed to erase TriggerObject for trigger "
              << trigger_number);
          }
          triggers_processed_.PushBack(trigger_number, triggers_processed_allocator_);
        }
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "HexitecStackedPlugin failed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << dataset << " dataset, frame number: "
        << frame_number);
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
    for (int i=0; i<image_pixels_; i++)
    {
      out[i] += in[i];
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
