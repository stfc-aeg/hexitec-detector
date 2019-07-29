/*
 * HexitecHistogramPlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: Christian Angelsen
 */

#include <HexitecHistogramPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecHistogramPlugin::CONFIG_MAX_FRAMES     = "max_frames_received";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_START      = "bin_start";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_END 		    = "bin_end";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_WIDTH 		  = "bin_width";
  const std::string HexitecHistogramPlugin::CONFIG_FLUSH_HISTOS   = "flush_histograms";
  const std::string HexitecHistogramPlugin::CONFIG_SENSORS_LAYOUT = "sensors_layout";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecHistogramPlugin::HexitecHistogramPlugin() :
      image_width_(Hexitec::pixel_columns_per_sensor),
      image_height_(Hexitec::pixel_rows_per_sensor),
      image_pixels_(image_width_ * image_height_),
			max_frames_received_(0),
			frames_counter_(0),
			flush_histograms_(false)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecHistogramPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecHistogramPlugin version " <<
    												this->get_version_long() << " loaded.");

    bin_start_   = 0;
    bin_end_     = 8000;
    bin_width_   = 10;
    number_bins_ = (int)(((bin_end_ - bin_start_) / bin_width_) + 0.5);

    initialiseHistograms();

    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
  }

  /**
   * Destructor.
   */
  HexitecHistogramPlugin::~HexitecHistogramPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecHistogramPlugin destructor.");
  }

  int HexitecHistogramPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecHistogramPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecHistogramPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecHistogramPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecHistogramPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

  /**
   * Allocate and initialise histograms
   *
   */
  void HexitecHistogramPlugin::initialiseHistograms()
  {
    // Setup the dimension(s) for energy_bins, summed_histograms
    dimensions_t dims(1);
    dims[0] = number_bins_;

    // Setup the energy bins

    FrameMetaData energy_meta;

    energy_meta.set_dimensions(dims);
    energy_meta.set_compression_type(no_compression);
    energy_meta.set_data_type(raw_float);
    energy_meta.set_frame_number(0);
    energy_meta.set_dataset_name("energy_bins");

    energy_bins_ = boost::shared_ptr<Frame>(new DataBlockFrame(energy_meta, number_bins_ * sizeof(float)));

    // Setup the summed histograms

    FrameMetaData summed_meta;

    summed_meta.set_dimensions(dims);
    summed_meta.set_compression_type(no_compression);
    summed_meta.set_data_type(raw_64bit);
    summed_meta.set_frame_number(0);
    summed_meta.set_dataset_name("summed_histograms");

    summed_histograms_ = boost::shared_ptr<Frame>(new DataBlockFrame(summed_meta, number_bins_ * sizeof(uint64_t)));

    // Setup the pixels' histograms

    // Setup the dimensions pixel_histograms
    dimensions_t pixel_dims(2);
    pixel_dims[0] = image_pixels_;
    pixel_dims[1] = number_bins_;

    FrameMetaData pixel_meta;

    pixel_meta.set_dimensions(pixel_dims);
    pixel_meta.set_compression_type(no_compression);
    pixel_meta.set_data_type(raw_float);
    pixel_meta.set_frame_number(0);
    pixel_meta.set_dataset_name("pixel_histograms");

    pixel_histograms_ = boost::shared_ptr<Frame>(new DataBlockFrame(pixel_meta, image_pixels_ * number_bins_ * sizeof(float)));

    // Initialise bins
    float currentBin = bin_start_;
    float *pHxtBin = static_cast<float *>(energy_bins_->get_data_ptr());	// New implementation
    for (long i = bin_start_; i < number_bins_; i++, currentBin += bin_width_)
    {
       *pHxtBin = currentBin;
       pHxtBin++;
    }

		// Clear histogram values
		float *pixels = static_cast<float *>(pixel_histograms_->get_data_ptr());
		float *summed = static_cast<float *>(summed_histograms_->get_data_ptr());
		memset(pixels, 0, (number_bins_ * image_pixels_) * sizeof(float));
		memset(summed, 0, number_bins_ * sizeof(uint64_t));

  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_      <=> sensors_layout
   * - max_frames_received_			<=> max_frames_received
   * - bin_start_								<=> bin_start
   * - bin_end_									<=> bin_end
   * - bin_width_								<=> bin_width
   * - flush_histograms_				<=> flush_histograms
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecHistogramPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
 	  if (config.has_param(HexitecHistogramPlugin::CONFIG_SENSORS_LAYOUT))
		{
 		  sensors_layout_str_= config.get_param<std::string>(HexitecHistogramPlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
		}

    if (config.has_param(HexitecHistogramPlugin::CONFIG_MAX_FRAMES))
    {
    	max_frames_received_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_MAX_FRAMES);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_START))
    {
    	bin_start_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_BIN_START);
		}

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_END))
    {
    	bin_end_ = config.get_param<long>(HexitecHistogramPlugin::CONFIG_BIN_END);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_WIDTH))
		{
    	bin_width_ = config.get_param<double>(HexitecHistogramPlugin::CONFIG_BIN_WIDTH);
		}

    number_bins_  = (int)(((bin_end_ - bin_start_) / bin_width_) + 0.5);

    if (config.has_param(HexitecHistogramPlugin::CONFIG_FLUSH_HISTOS))
    {
    	flush_histograms_ = config.get_param<bool>(HexitecHistogramPlugin::CONFIG_FLUSH_HISTOS);

      LOG4CXX_TRACE(logger_, " ***** GOING TO PUSH THE HISTOGRAMS NOW! assuming:" << flush_histograms_);

    	if (flush_histograms_)
    	{
				/// Time to push current histogram data
				writeHistogramsToDisk();

				// // Clear histogram values - Not needed, initialiseHistograms() does this
				// float *pixels = static_cast<float *>(pixel_histograms_->get_data_ptr());
				// float *summed = static_cast<float *>(summed_histograms_->get_data_ptr());
		    // memset(pixels, 0, (number_bins_ * image_pixels_) * sizeof(float));
		    // memset(summed, 0, number_bins_ * sizeof(uint64_t));

				frames_counter_ = 0;

    		// Clear flush_histograms_
    		flush_histograms_ = false;
        // (Re-)Initialise memory
        initialiseHistograms();
    	}
    }

  }

  void HexitecHistogramPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
  	// Return the configuration of the histogram plugin
  	std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_MAX_FRAMES , max_frames_received_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_BIN_START, bin_start_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_BIN_END , bin_end_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_BIN_WIDTH, bin_width_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_FLUSH_HISTOS, flush_histograms_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecHistogramPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecHistogramPlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/max_frames_received", max_frames_received_);
    status.set_param(get_name() + "/bin_start", bin_start_);
    status.set_param(get_name() + "/bin_end", bin_end_);
    status.set_param(get_name() + "/bin_width", bin_width_);
    status.set_param(get_name() + "/flush_histograms", flush_histograms_);
  }

  /**
   * Reset process plugin statistics, i.e. counter of packets lost
   */
  bool HexitecHistogramPlugin::reset_statistics(void)
  {
  	// Nothing to reset??

    return true;
  }

  /**
   * Perform processing on the frame.  Calculate histograms based upon
   * each frame, writing resulting datasets to file when configured
	 * maximum number of frames received.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecHistogramPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data_ptr()));

    // Check dataset's name
    FrameMetaData &incoming_frame_meta = frame->meta_data();
    const std::string& dataset = incoming_frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
			LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
 														 " dataset, frame number: " << frame->get_frame_number());
			this->push(frame);
    }
    else if (dataset.compare(std::string("data")) == 0)
    {
			try
			{
				frames_counter_++;

				// Define pointer to the input image data
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				// Add this frame's contribution onto histograms
				add_frame_data_to_histogram_with_sum(static_cast<float *>(input_ptr));

				// Write histograms to disc when maximum number of frames received
				if ( ((frames_counter_ % max_frames_received_) == 0) &&
						(frames_counter_ != 0) )	// Fix why empty histograms written to 2nd (third et cetera) HDF5 files? - Not quite..
				// if (frames_counter_ == max_frames_received_)
				{
					/// Time to push current histogram data to file
					writeHistogramsToDisk();
				}

				/// Histogram will access data dataset but not change it in any way
				/// 	Therefore do not need to check frame dimensions, allocated memory,
				/// 	etc

				// Pass on data dataset unmodified:

				LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
	 														 " dataset, frame number: " << frame->get_frame_number());
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
   * Write Histogram data to disk.
   */
  void HexitecHistogramPlugin::writeHistogramsToDisk()
  {
		LOG4CXX_TRACE(logger_, "Pushing " << energy_bins_->get_meta_data().get_dataset_name() << " dataset");
		this->push(energy_bins_);

		LOG4CXX_TRACE(logger_, "Pushing " << summed_histograms_->get_meta_data().get_dataset_name() << " dataset");
		this->push(summed_histograms_);

		LOG4CXX_TRACE(logger_, "Pushing " << pixel_histograms_->get_meta_data().get_dataset_name() << " dataset");
		this->push(pixel_histograms_);

  }

  /**
   * Perform processing on the frame.  Calculate histograms based upon
   * each frame.
   *
   * \param[frame] frame - Pointer to a frame object.
   */
  void HexitecHistogramPlugin::add_frame_data_to_histogram_with_sum(float *frame)
  {
		const void* pixel_ptr = static_cast<const void*>(
				static_cast<const char*>(pixel_histograms_->get_data_ptr()));
		void* pixel_input_ptr = static_cast<void *>(
				static_cast<char *>(const_cast<void *>(pixel_ptr)));

		const void* summed_ptr = static_cast<const void*>(
				static_cast<const char*>(summed_histograms_->get_data_ptr()));
		void* summed_input_ptr = static_cast<void *>(
				static_cast<char *>(const_cast<void *>(summed_ptr)));

		float *currentHistogram = static_cast<float *>(pixel_input_ptr);
		uint64_t *summed = static_cast<uint64_t *>(summed_input_ptr);

		float thisEnergy;
		int bin;
		int pixel;
		for (int i = 0; i < image_pixels_; i++)
		{
			pixel = i;
			thisEnergy = frame[i];

			if (thisEnergy <= 0.0)
				continue;
			bin = (int)((thisEnergy / bin_width_));
			if (bin <= number_bins_)
			{
				(*(currentHistogram + (pixel * number_bins_) + bin))++;
				(*(summed + bin)) ++;
			}
		}
  }

  // Called when the user NOT selected spectrum option
  void HexitecHistogramPlugin::addFrameDataToHistogram(float *frame)
  {
		float *currentHistogram = static_cast<float *>(pixel_histograms_->get_data_ptr());
		float thisEnergy;
		int bin;
		int pixel;

		for (int i = 0; i < image_pixels_; i++)
		{
			pixel = i;
			thisEnergy = frame[i];
			if (thisEnergy == 0)
				continue;
			bin = (int)((thisEnergy / bin_width_));
			if (bin <= number_bins_)
			{
				(*(currentHistogram + (pixel * number_bins_) + bin))++;
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
	std::size_t HexitecHistogramPlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
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
