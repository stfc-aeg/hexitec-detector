/*
 * HexitecTemplatePlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: Christian Angelsen
 */

#include <HexitecTemplatePlugin.h>
#include <DebugLevelLogger.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecTemplatePlugin::CONFIG_SENSORS_LAYOUT  = "sensors_layout";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecTemplatePlugin::HexitecTemplatePlugin()
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecTemplatePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecTemplatePlugin version " <<
      this->get_version_long() << " loaded.");

    // Set image_width_, image_height_, image_pixels_
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
  }

  /**
   * Destructor.
   */
  HexitecTemplatePlugin::~HexitecTemplatePlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecTemplatePlugin destructor.");
  }

  int HexitecTemplatePlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecTemplatePlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecTemplatePlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecTemplatePlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecTemplatePlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_ <=> sensors_layout
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecTemplatePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecTemplatePlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_ =
        config.get_param<std::string>(HexitecTemplatePlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
    }
  }

  void HexitecTemplatePlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecTemplatePlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecTemplatePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Status requested for HexitecTemplatePlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecTemplatePlugin::reset_statistics(void)
  {
    // Nowt to reset..?
    return true;
  }

  /**
   * Perform processing on the frame.  For a new plugin, amend this
   *  function process data as intended.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecTemplatePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Applying ... template algorithm???");

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
      static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
      LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << dataset << " dataset, frame number: "
                                        << frame->get_frame_number());
      this->push(frame);
    }
    else if (dataset.compare(std::string("data")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        ///TODO: This function do not exist; Design it to match requirements
        // some_function(static_cast<float *>(input_ptr));

        LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << dataset << " dataset, frame number: "
          << frame->get_frame_number());
        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "HexitecTemplatePluginfailed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
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
  std::size_t HexitecTemplatePlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
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
