/*
 * HexitecNextFramePlugin.cpp
 *
 *  Created on: 18 Sept 2018
 *      Author: Christian Angelsen
 */

#include <HexitecNextFramePlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecNextFramePlugin::CONFIG_SENSORS_LAYOUT = "sensors_layout";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecNextFramePlugin::HexitecNextFramePlugin() :
      image_width_(Hexitec::pixel_columns_per_sensor),
      image_height_(Hexitec::pixel_rows_per_sensor),
      image_pixels_(image_width_ * image_height_),
			last_frame_number_(-1)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecNextFramePlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecNextFramePlugin version " <<
    												this->get_version_long() << " loaded.");

    last_frame_ = (float *) calloc(image_pixels_, sizeof(float));
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
    ///
    debugFrameCounter = 0;
  }

  /**
   * Destructor.
   */
  HexitecNextFramePlugin::~HexitecNextFramePlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecNextFramePlugin destructor.");
    free(last_frame_);
    last_frame_ = NULL;
  }

  int HexitecNextFramePlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecNextFramePlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecNextFramePlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecNextFramePlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecNextFramePlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_      <=> sensors_layout
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecNextFramePlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
 	  if (config.has_param(HexitecNextFramePlugin::CONFIG_SENSORS_LAYOUT))
		{
 		  sensors_layout_str_= config.get_param<std::string>(HexitecNextFramePlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
		}

    // Parsing sensors above may update width, height members
    if (image_pixels_ != image_width_ * image_height_)
    {
      image_pixels_ = image_width_ * image_height_;
      reset_last_frame_values();
    }
  }

  void HexitecNextFramePlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecNextFramePlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecNextFramePlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecNextFramePlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecNextFramePlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  If same pixel hit in current frame as in the previous,
   * 	set pixel in current frame to zero.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecNextFramePlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    long long current_frame_number = frame->get_frame_number();

    LOG4CXX_TRACE(logger_, "Applying Next Frame algorithm.");

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
			LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
 														 " dataset, frame number: " << current_frame_number);
			this->push(frame);
    }
    else if (dataset.compare(std::string("data")) == 0)
    {
			try
			{
				// Define pointer to the input image data
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				// Don't compare current against last frame if not adjacent
				if ((last_frame_number_+1) != current_frame_number)
				{
					LOG4CXX_TRACE(logger_, "Not correcting current frame, because last frame number: " <<
																	last_frame_number_ << " versus current_frame_number: "
																	<< current_frame_number);
				}
				else
				{
					// Compare current frame versus last frame, if same pixel hit in both
					// 	then clear current pixel
					apply_algorithm(static_cast<float *>(input_ptr));
				}

				LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
															 " dataset, frame number: " << current_frame_number);

				last_frame_number_ = current_frame_number;

				// Copy current frame into last frame's place - regardless of any correection
				//	taking place, as we'll always need the current frame to compare against
				// 	the previous frame
				// 		Will this work (static_cast'ing..) ???
				memcpy(last_frame_, static_cast<float *>(input_ptr), image_pixels_ * sizeof(float));

				this->push(frame);
			}
			catch (const std::exception& e)
			{
				std::stringstream ss;
				ss << "HEXITEC frame decode failed: " << e.what();
				LOG4CXX_ERROR(logger_, ss.str());
			}
		}
    else
    {
    	LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }
  }

  /**
   * Compare current against last frame, zero Pixel in current frame if hit
   * 		in the last frame.
   *
   * \param[in] in - Pointer to the incoming image data.
   * \param[in] out - Pointer to the allocated memory for the corrected image.
   *
   */
  void HexitecNextFramePlugin::apply_algorithm(float *in)
  {
    for (int i=0; i<image_pixels_; i++)
    {
    	// If pixel in last frame is nonzero, clear it from current frame
    	// 	(whether hit or not), otherwise don't clear pixel frame current frame
    	if (last_frame_[i] > 0.0)
    	{
    		in[i] = 0.0;
    	}
    }

  }

	//! Parse the number of sensors map configuration string.
	//!
	//! This method parses a configuration string containing number of sensors mapping information,
	//! which is expected to be of the format "NxN" e.g, 2x2. The map is saved in a member
	//! variable.
	//!
	//! \param[in] sensors_layout_str - string of number of sensors configured
	//! \return number of valid map entries parsed from string
	//!
	std::size_t HexitecNextFramePlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
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

	    // Return the number of valid entries parsed
	    return sensors_layout_.size();
	}

	//! Reset array used to store last_frame values.
	//!
	//! This method is called when the number of sensors is changed,
	//! to prevent accessing unassigned memory
	//!
  void HexitecNextFramePlugin::reset_last_frame_values()
  {
    free(last_frame_);
    last_frame_ = (float *) calloc(image_pixels_, sizeof(float));
  }

  //// Debug function: Takes a file prefix and frame, and writes all nonzero pixels to a file
	void HexitecNextFramePlugin::writeFile(std::string filePrefix, float *frame)
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
			 + std::string("_ODIN_Cal_detailed.txt");
		outFile.open(fname.c_str(), std::ofstream::app);
		outFile.write((const char *)hitPixelsString.c_str(), hitPixelsString.length() * sizeof(char));
		outFile.close();
	}

} /* namespace FrameProcessor */
