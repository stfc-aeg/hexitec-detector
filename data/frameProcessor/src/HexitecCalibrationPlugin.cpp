/*
 * HexitecCalibrationPlugin.cpp
 *
 *  Created on: 24 Sept 2018
 *      Author: Christian Angelsen
 */

#include <HexitecCalibrationPlugin.h>
#include <DebugLevelLogger.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE  = "gradients_filename";
  const std::string HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE = "intercepts_filename";
  const std::string HexitecCalibrationPlugin::CONFIG_SENSORS_LAYOUT  = "sensors_layout";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecCalibrationPlugin::HexitecCalibrationPlugin() :
      gradients_status_(false),
      intercepts_status_(false),
      gradient_values_(NULL),
      intercept_values_(NULL),
      gradients_filename_(""),
      intercepts_filename_("")
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecCalibrationPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecCalibrationPlugin version " <<
      this->get_version_long() << " loaded.");

    // Set image_width_, image_height_, image_pixels_
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);

    gradient_values_ = (float *) calloc(image_pixels_, sizeof(float));
    intercept_values_ = (float *) calloc(image_pixels_, sizeof(float));

    *gradient_values_ = 1;
    *intercept_values_ = 0;
  }

  /**
   * Destructor.
   */
  HexitecCalibrationPlugin::~HexitecCalibrationPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecCalibrationPlugin destructor.");
    free(gradient_values_);
    free(intercept_values_);
  }

  int HexitecCalibrationPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecCalibrationPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecCalibrationPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecCalibrationPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecCalibrationPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_  <=> sensors_layout
   * - gradients_filename   <=> gradients_file
   * - intercepts_filename  <=> intercepts_file
   * 
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecCalibrationPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecCalibrationPlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_= config.get_param<std::string>(HexitecCalibrationPlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
      reset_calibration_values();
    }

    if (config.has_param(HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE))
    {
      gradients_filename_ = config.get_param<std::string>(HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE);
      setGradients(gradients_filename_.c_str());
    }

    if (config.has_param(HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE))
    {
      intercepts_filename_ = config.get_param<std::string>(HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE);
      setIntercepts(intercepts_filename_.c_str());
    }
 
  }

  void HexitecCalibrationPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the calibration plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_GRADIENTS_FILE, gradients_filename_);
    reply.set_param(base_str + HexitecCalibrationPlugin::CONFIG_INTERCEPTS_FILE, intercepts_filename_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecCalibrationPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Status requested for HexitecCalibrationPlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/gradients_filename", gradients_filename_);
    status.set_param(get_name() + "/intercepts_filename", intercepts_filename_);
  }

  /**
   * Reset calibration plugin statistics
   */
  bool HexitecCalibrationPlugin::reset_statistics(void)
  {
    // Nothing to reset..?
    return true;
  }

  /**
   * Perform processing on the frame. Each pixel is calibrated with the gradient and intercept
   * values provided by the two corresponding files.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecCalibrationPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Applying Calibration.");

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
    else if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));
        calibrate_pixels(static_cast<float *>(input_ptr));
        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "HexitecCalibrationPlugin failed: " << e.what());
      }
		}
    else
    {
      LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }
  }

  /**
   * Calibrate an image's pixels.
   *
   * \param[in] image - Pointer to the image data.
   */
  void HexitecCalibrationPlugin::calibrate_pixels(float *image)
  {
    for (int i=0; i<image_pixels_; i++)
    {
      if (image[i] > 0)
      {
        image[i] = (image[i] * gradient_values_[i])  + intercept_values_[i];
      }
    }
  }

  /**
   * Set the filename containing the gradient values.
   *
   * \param[in] gradientFilename - The name of the gradient file.
   */
  void HexitecCalibrationPlugin::setGradients(const char *gradientFilename)
  {
    float defaultValue = 1;
    gradients_status_ = getData(gradientFilename, gradient_values_, defaultValue);
    if (gradients_status_)
    {
      LOG4CXX_TRACE(logger_, "Setting Gradients Successful, used file: " << gradientFilename);
    }
    else
    {
      LOG4CXX_ERROR(logger_, "setGradients() Failed (using default value instead)");
    }
  }

  /**
   * Set the filename containing the intercept values.
   *
   * \param[in] interceptFilename - The name of the intercept file.
   */
  void HexitecCalibrationPlugin::setIntercepts(const char *interceptFilename)
  {
    float defaultValue = 0;
    intercepts_status_ = getData(interceptFilename, intercept_values_, defaultValue);
    if (intercepts_status_)
    {
      LOG4CXX_TRACE(logger_, "Setting Intercepts Successful, used file: " << interceptFilename);
    }
    else
    {
      LOG4CXX_ERROR(logger_, "setIntercepts() Failed (using default value instead)");
    }
  }

  /**
   * Read all the values from the provided file.  If the file is too short, pad missing
   * values using the provided default value.
   *
   * \param[in] filename - The name of the file to be read.
   * \param[in] dataValue - Array that will receive values read from file.
   * \param[in] defaultValue - The default value used if filename is too short (to
   *    provide image_pixels_ number of values).
   * \return bool indicating success of reading file
   */
  bool HexitecCalibrationPlugin::getData(const char *filename, float *dataValue, float defaultValue)
  {
    int i = 0;
    std::ifstream inFile;
    bool success = false;

    /// Count number of floats in file:
    std::ifstream   file(filename);
    int file_values = std::distance(std::istream_iterator<double>(file),
      std::istream_iterator<double>());
    file.close();

    if (image_pixels_ != file_values)
    {
      LOG4CXX_ERROR(logger_, "Expected " << image_pixels_ << " values but read " << file_values
        << " values from file: " << filename);

      LOG4CXX_WARN(logger_, "Using default values instead");
      for (int val = 0; val < image_pixels_; val ++)
      {
        dataValue[val] = defaultValue;
      }

      return success;
    }

    inFile.open(filename);

    while (inFile >> dataValue[i])
    {
      i++;
    }
    inFile.close();
    success = true;

    return success;
  }

  /**
   * Parse the number of sensors map configuration string.
   * 
   * This method parses a configuration string containing number of sensors mapping information,
   * which is expected to be of the format "NxN" e.g, 2x2. The map is saved in a member
   * variable.
   * 
   * \param[in] sensors_layout_str - string of number of sensors configured
   * \return number of valid map entries parsed from string
   */
  std::size_t HexitecCalibrationPlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
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
    image_pixels_= image_width_ * image_height_;

    // Return the number of valid entries parsed
    return sensors_layout_.size();
  }

  /**
   * Reset arrays used to store calibration values.
   * 
   * This method is called when the number of sensors is changed,
   * to prevent accessing unassigned memory
   */
  void HexitecCalibrationPlugin::reset_calibration_values()
  {
    free(gradient_values_);
    free(intercept_values_);
    gradient_values_ = (float *) calloc(image_pixels_, sizeof(float));
    intercept_values_ = (float *) calloc(image_pixels_, sizeof(float));
  }

} /* namespace FrameProcessor */
