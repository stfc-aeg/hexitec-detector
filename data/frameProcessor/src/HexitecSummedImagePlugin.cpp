/*
 * HexitecSummedImagePlugin.cpp
 *
 *  Created on: 11 Jan 2021
 *      Author: Christian Angelsen
 */

#include <HexitecSummedImagePlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecSummedImagePlugin::CONFIG_SENSORS_LAYOUT   = "sensors_layout";
  const std::string HexitecSummedImagePlugin::CONFIG_THRESHOLD_LOWER  = "threshold_lower";
  const std::string HexitecSummedImagePlugin::CONFIG_THRESHOLD_UPPER  = "threshold_upper";
  const std::string HexitecSummedImagePlugin::CONFIG_IMAGE_FREQUENCY  = "image_frequency";
  const std::string HexitecSummedImagePlugin::CONFIG_RESET_IMAGE      = "reset_image";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecSummedImagePlugin::HexitecSummedImagePlugin()
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecSummedImagePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecSummedImagePlugin version " <<
                  this->get_version_long() << " loaded.");

    // Set image_width_, image_height_, image_pixels_
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);

    summed_image_ = (unsigned short *) calloc(image_pixels_, sizeof(unsigned short *));
    memset(summed_image_, 0, image_pixels_ * sizeof(unsigned short));
    threshold_lower_ = 0;
    threshold_upper_ = 16382;
    image_frequency_ = 1;
  }

  /**
   * Destructor.
   */
  HexitecSummedImagePlugin::~HexitecSummedImagePlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecSummedImagePlugin destructor.");
    free(summed_image_);
    summed_image_ = NULL;
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
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_  <=> sensors_layout
   * - threshold_lower_     <=> threshold_lower
   * - threshold_upper_     <=> threshold_upper
   * - image_frequency_     <=> image_frequency
   * - reset_image_         <=> reset_image
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecSummedImagePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecSummedImagePlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_= config.get_param<std::string>(HexitecSummedImagePlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
      reset_summed_image_values();
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_THRESHOLD_LOWER))
    {
      threshold_lower_ = config.get_param<int>(HexitecSummedImagePlugin::CONFIG_THRESHOLD_LOWER);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_THRESHOLD_UPPER))
    {
      threshold_upper_ = config.get_param<int>(HexitecSummedImagePlugin::CONFIG_THRESHOLD_UPPER);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_IMAGE_FREQUENCY))
    {
      image_frequency_ = config.get_param<int>(HexitecSummedImagePlugin::CONFIG_IMAGE_FREQUENCY);
    }

    if (config.has_param(HexitecSummedImagePlugin::CONFIG_RESET_IMAGE))
    {
      reset_image_ = config.get_param<int>(HexitecSummedImagePlugin::CONFIG_RESET_IMAGE);

      if (reset_image_ == 1)
      {
        // Clear all pixels to be 0
        memset(summed_image_, 0, image_pixels_ * sizeof(unsigned short));
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
    reply.set_param(base_str + HexitecSummedImagePlugin::CONFIG_RESET_IMAGE, reset_image_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecSummedImagePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecSummedImagePlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/threshold_lower", threshold_lower_);
    status.set_param(get_name() + "/threshold_upper", threshold_upper_);
    status.set_param(get_name() + "/image_frequency", image_frequency_);
    status.set_param(get_name() + "/reset_image", reset_image_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecSummedImagePlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
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

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
      LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                        << frame->get_frame_number());
      this->push(frame);
    }
    else if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Pass on dataset processed_frames as is
        LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                          << frame->get_frame_number());
        this->push(frame);

        if ((frame->get_frame_number() % image_frequency_) == 0)
        {
          // Create summed_image dataset

          FrameMetaData summed_image_meta;
          dimensions_t dims(2);
          dims[0] = image_height_;
          dims[1] = image_width_;
          summed_image_meta.set_dimensions(dims);
          summed_image_meta.set_compression_type(no_compression);
          summed_image_meta.set_data_type(raw_16bit);
          summed_image_meta.set_frame_number(frame_number);
          summed_image_meta.set_dataset_name("summed_images");

          const std::size_t summed_image_size = image_width_ * image_height_ * sizeof(unsigned short);

          boost::shared_ptr<Frame> summed_frame;
          summed_frame = boost::shared_ptr<Frame>(new DataBlockFrame(summed_image_meta,
            summed_image_size));

          // Ensure frame is empty
          float *summed = static_cast<float *>(summed_frame->get_data_ptr());
          memset(summed, 0, image_pixels_ * sizeof(unsigned short));

          // Define pointer to the input image data
          void* input_ptr = static_cast<void *>(
            static_cast<char *>(const_cast<void *>(data_ptr)));

          void* output_ptr = summed_frame->get_data_ptr();

          // Apply algorithm
          apply_summed_image_algorithm(static_cast<float *>(input_ptr),
                                      static_cast<unsigned short *>(output_ptr));

          const std::string& dataset_name = summed_image_meta.get_dataset_name();
          LOG4CXX_TRACE(logger_, "Pushing " << dataset_name << " dataset, frame number: " <<
                        summed_frame->get_frame_number());
          this->push(summed_frame);
        }
        else
          LOG4CXX_TRACE(logger_, "Skipping frame: " << frame->get_frame_number());
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "HexitecSummedImagePlugin failed: " << e.what());
      }
    }
    else
    {
      // Push any other (histogram?) dataset
      LOG4CXX_TRACE(logger_, "Pushing " << dataset << " dataset, frame number: "
                                        << frame->get_frame_number());
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
  void HexitecSummedImagePlugin::apply_summed_image_algorithm(float *in, unsigned short *out)
  {
    for (int i=0; i<image_pixels_; i++)
    {
      // if (i < 15) // DEBUGGING
      // {
      //   std::cout << " BEFORE, i = " << std::setw(3) << i << " in[" << std::setw(2) << i << "] = "
      //             << std::setw(4) << in[i] << " thL: " << threshold_lower_ << " thU: " << threshold_upper_
      //             << " cond L: " << ((unsigned short)in[i] > threshold_lower_) << " cond U: " 
      //             << ((unsigned short)in[i] < threshold_upper_) << " L && U: "
      //             << (((unsigned short)in[i] > threshold_lower_) && ((unsigned short)in[i] < threshold_upper_))
      //             << " s_i[i]: " << std::setw(4) << summed_image_[i] << " out[i]: " << std::setw(4) << out[i];
      // }
      if (((unsigned short)in[i] > threshold_lower_) && ((unsigned short)in[i] < threshold_upper_))
      {
        summed_image_[i] += 1;
      }
      // Maintain history from previous frame(s)
      out[i] = summed_image_[i];

      // if (i < 15) // DEBUGGING
      // {
      //   if ((in[i] > threshold_lower_) && (in[i] < threshold_upper_))
      //     std::cout << "  YES!";
      //   else
      //     std::cout << "  NOWT!";
      //   std::cout << "  -=- AFTER " << std::setw(2) << i << " s_i[i]: " << std::setw(4)
      //             << summed_image_[i] << " out[i]: " << std::setw(4) << out[i] << std::endl;
      // }
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

  /** Reset array used to store summed image values.
   * 
   * This method is called when the number of sensors is changed,
   *  to prevent accessing unassigned memory.
   */
  void HexitecSummedImagePlugin::reset_summed_image_values()
  {
    free(summed_image_);
    summed_image_ = (unsigned short *) calloc(image_pixels_, sizeof(unsigned short));
    memset(summed_image_, 0, image_pixels_ * sizeof(unsigned short));
  }

} /* namespace FrameProcessor */
