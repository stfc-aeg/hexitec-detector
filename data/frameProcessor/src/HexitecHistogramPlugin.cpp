/*
 * HexitecHistogramPlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: Christian Angelsen
 */

#include <HexitecHistogramPlugin.h>
#include <DebugLevelLogger.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecHistogramPlugin::CONFIG_MAX_FRAMES         = "max_frames_received";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_START          = "bin_start";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_END            = "bin_end";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_WIDTH          = "bin_width";
  const std::string HexitecHistogramPlugin::CONFIG_RESET_HISTOS       = "reset_histograms";
  const std::string HexitecHistogramPlugin::CONFIG_SENSORS_LAYOUT     = "sensors_layout";
  const std::string HexitecHistogramPlugin::CONFIG_FRAMES_PROCESSED   = "frames_processed";
  const std::string HexitecHistogramPlugin::CONFIG_HISTOGRAMS_WRITTEN = "histograms_written";
  const std::string HexitecHistogramPlugin::CONFIG_HISTOGRAM_INDEX    = "histogram_index";
  const std::string HexitecHistogramPlugin::CONFIG_PASS_PROCESSED     = "pass_processed";
  const std::string HexitecHistogramPlugin::CONFIG_PASS_RAW           = "pass_raw";
  // const std::string HexitecHistogramPlugin::CONFIG_PASS_PIXEL_SPECTRA = "pass_pixel_spectra";
  const std::string HexitecHistogramPlugin::CONFIG_RANK_INDEX         = "rank_index";
  const std::string HexitecHistogramPlugin::CONFIG_RANK_OFFSET        = "rank_offset";
  const std::string HexitecHistogramPlugin::CONFIG_FRAMES_PER_TRIGGER  = "frames_per_trigger";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecHistogramPlugin::HexitecHistogramPlugin() :
      max_frames_received_(0),
      histograms_written_(0),
      frames_processed_(0),
      histogram_index_(0),
      rank_index_(0),
      rank_offset_(2),  // Default rank offset for Hexitec
      frames_per_trigger_(3),
      pass_processed_(true),
      pass_raw_(true),
      pass_pixel_spectra_(false)
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

    // Set image_width_, image_height_, image_pixels_
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
    initialiseHistograms();
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
    // Setup the dimension(s) for spectra_bins, summed_spectra
    dimensions_t dims(1);
    dims[0] = number_bins_;

    // Setup the spectra bins

    FrameMetaData spectra_meta;

    spectra_meta.set_dimensions(dims);
    spectra_meta.set_compression_type(no_compression);
    spectra_meta.set_data_type(raw_float);
    spectra_meta.set_frame_number(0);
    spectra_meta.set_dataset_name("spectra_bins");

    spectra_bins_ =
      boost::shared_ptr<Frame>(new DataBlockFrame(spectra_meta, number_bins_ * sizeof(float)));

    // Setup the summed spectra

    FrameMetaData summed_meta;

    summed_meta.set_dimensions(dims);
    summed_meta.set_compression_type(no_compression);
    summed_meta.set_data_type(raw_64bit);
    summed_meta.set_frame_number(0);
    summed_meta.set_dataset_name("summed_spectra");

    summed_spectra_ =
      boost::shared_ptr<Frame>(new DataBlockFrame(summed_meta, number_bins_ * sizeof(uint64_t)));


    // Setup the pixel spectra

    // Setup the dimensions pixel_spectra
    dimensions_t pixel_dims(3);
    pixel_dims[0] = image_height_;
    pixel_dims[1] = image_width_;
    pixel_dims[2] = number_bins_;

    FrameMetaData pixel_meta;

    pixel_meta.set_dimensions(pixel_dims);
    pixel_meta.set_compression_type(no_compression);
    pixel_meta.set_data_type(raw_float);
    pixel_meta.set_frame_number(0);
    pixel_meta.set_dataset_name("pixel_spectra");

    pixel_spectra_ =
      boost::shared_ptr<Frame>(new DataBlockFrame(pixel_meta, image_pixels_ * number_bins_ * sizeof(float)));

    // Initialise bins
    float currentBin = bin_start_;
    float *pHxtBin = static_cast<float *>(spectra_bins_->get_data_ptr());
    for (long i = bin_start_; i < number_bins_; i++, currentBin += bin_width_)
    {
      *pHxtBin = currentBin;
      pHxtBin++;
    }

    // Clear histogram values
    float *pixels = static_cast<float *>(pixel_spectra_->get_data_ptr());
    float *summed = static_cast<float *>(summed_spectra_->get_data_ptr());
    memset(pixels, 0, (number_bins_ * image_pixels_) * sizeof(float));
    memset(summed, 0, number_bins_ * sizeof(uint64_t));

    histograms_written_ = 0;
    frames_processed_ = 0;
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * 
   * - sensors_layout_str_  <=> sensors_layout
   * - max_frames_received_ <=> max_frames_received
   * - bin_start_           <=> bin_start
   * - bin_end_             <=> bin_end
   * - bin_width_           <=> bin_width
   * - reset_histograms_    <=> reset_histograms
   * - rank_index_          <=> rank_index
   * - rank_offset_         <=> rank_offset
   * - frames_per_trigger_  <=> frames_per_trigger
   * - pass_processed_      <=> pass_processed
   * - pass_raw_            <=> pass_raw
   * - pass_pixel_spectra_  <=> pass_pixel_spectra
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecHistogramPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecHistogramPlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_=
        config.get_param<std::string>(HexitecHistogramPlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_MAX_FRAMES))
    {
      max_frames_received_ =
        config.get_param<unsigned int>(HexitecHistogramPlugin::CONFIG_MAX_FRAMES);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_START))
    {
      bin_start_ = config.get_param<unsigned int>(HexitecHistogramPlugin::CONFIG_BIN_START);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_END))
    {
      bin_end_ = config.get_param<unsigned int>(HexitecHistogramPlugin::CONFIG_BIN_END);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_WIDTH))
    {
      bin_width_ = config.get_param<double>(HexitecHistogramPlugin::CONFIG_BIN_WIDTH);
    }

    number_bins_  = (int)(((bin_end_ - bin_start_) / bin_width_) + 0.5);

    if (config.has_param(HexitecHistogramPlugin::CONFIG_RESET_HISTOS))
    {
      reset_histograms_ =
        config.get_param<unsigned int>(HexitecHistogramPlugin::CONFIG_RESET_HISTOS);

      if (reset_histograms_ == 1)
      {
        frames_processed_ = 0;
        reset_histograms_ = 0;
      }      
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_RANK_INDEX))
    {
      rank_index_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_RANK_INDEX);
      // LOG4CXX_DEBUG_LEVEL(2, logger_, "Rank index set to: " << rank_index_);
      LOG4CXX_TRACE(logger_, "Rank index set to: " << rank_index_);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_RANK_OFFSET))
    {
      rank_offset_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_RANK_OFFSET);
      // LOG4CXX_DEBUG_LEVEL(2, logger_, "Rank offset set to: " << rank_offset_);
      LOG4CXX_TRACE(logger_, "Rank offset set to: " << rank_offset_);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_FRAMES_PER_TRIGGER))
    {
      frames_per_trigger_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_FRAMES_PER_TRIGGER);
      LOG4CXX_TRACE(logger_, "Frames per trigger set to: " << frames_per_trigger_);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_PASS_PROCESSED))
    {
      pass_processed_ = config.get_param<bool>(HexitecHistogramPlugin::CONFIG_PASS_PROCESSED);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_PASS_RAW))
    {
      pass_raw_ = config.get_param<bool>(HexitecHistogramPlugin::CONFIG_PASS_RAW);
    }

    // if (config.has_param(HexitecHistogramPlugin::CONFIG_PASS_PIXEL_SPECTRA))
    // {
    //   pass_pixel_spectra_ = config.get_param<bool>(HexitecHistogramPlugin::CONFIG_PASS_PIXEL_SPECTRA);
    // }

    // (Re-)Initialise memory
    initialiseHistograms();
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
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_FRAMES_PROCESSED, frames_processed_);
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_HISTOGRAMS_WRITTEN, histograms_written_);
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_HISTOGRAM_INDEX, histogram_index_);
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_PASS_PROCESSED, pass_processed_);
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_PASS_RAW, pass_raw_);
    // reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_PASS_PIXEL_SPECTRA, pass_pixel_spectra_);
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_RANK_INDEX, rank_index_);
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_RANK_OFFSET, rank_offset_);
    reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_FRAMES_PER_TRIGGER, frames_per_trigger_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecHistogramPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Status requested for HexitecHistogramPlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/max_frames_received", max_frames_received_);
    status.set_param(get_name() + "/bin_start", bin_start_);
    status.set_param(get_name() + "/bin_end", bin_end_);
    status.set_param(get_name() + "/bin_width", bin_width_);
    status.set_param(get_name() + "/frames_processed", frames_processed_);
    status.set_param(get_name() + "/histograms_written", histograms_written_);
    status.set_param(get_name() + "/histogram_index", histogram_index_);
    status.set_param(get_name() + "/pass_processed", pass_processed_);
    status.set_param(get_name() + "/pass_raw", pass_raw_);
    // status.set_param(get_name() + "/pass_pixel_spectra", pass_pixel_spectra_);
    status.set_param(get_name() + "/rank_index", rank_index_);
    status.set_param(get_name() + "/rank_offset", rank_offset_);
    status.set_param(get_name() + "/frames_per_trigger", frames_per_trigger_);
  }

  /**
   * Reset process plugin statistics, i.e. counter of packets lost
   */
  bool HexitecHistogramPlugin::reset_statistics(void)
  {
    // Reset frames_processed_??
    // frames_processed_ = 0;
    return true;
  }

  /** Process an EndOfAcquisition Frame.
  *
  * Write histograms to disk on end of acquisition
  */
  void HexitecHistogramPlugin::process_end_of_acquisition()
  {
    LOG4CXX_DEBUG_LEVEL(2, logger_, "End of acquisition frame received, pushing histograms");
    pass_pixel_spectra_ = true;
    writeHistogramsToDisk();
    pass_pixel_spectra_ = false;
    // Initialise new histogram datasets
    initialiseHistograms();
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
    long long frame_number = incoming_frame_meta.get_frame_number();

    const std::string& lvframes = "lvframes";
    const std::string& lvspectra = "lvspectra";

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
      // Pass raw_frames dataset down the chain, or only to lvframes
      if (pass_raw_)
      {
        // LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << dataset << " dataset, frame number: "
        LOG4CXX_TRACE(logger_, "H: " << dataset << ", frame number: " << frame_number << " Pushed onward");
        this->push(frame);
      }
      else
      {
        // LOG4CXX_DEBUG_LEVEL(3, 
        LOG4CXX_TRACE(logger_, dataset << " dataset pushed to " << lvframes);
        this->push(lvframes, frame);
      }
    }
    else if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Pass processed_frames dataset down the chain, or lvframes only
        if (pass_processed_)
        {
          // Pass on processed_frames dataset unmodified:
          LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << dataset << " dataset, frame number: "
            << frame_number);
          this->push(frame);
        }
        else
        {
          LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << dataset << " dataset to " << lvframes);
          this->push(lvframes, frame);
        }
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "processed_frames dataset failed: " << e.what());
      }
    }
    else if (dataset.compare(std::string("stacked_frames")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        // Add this frame's contribution onto histograms
        add_frame_data_to_histogram_with_sum(static_cast<float *>(input_ptr));
        frames_processed_++;

        // Push this trigger's histograms data to file
        histogram_index_ = frame->get_frame_number();
        writeHistogramsToDisk();
        LOG4CXX_TRACE(logger_, "H: " << dataset << ", pushed his, histogram_index: " << histogram_index_ );
        histograms_written_ += 1;
        LOG4CXX_TRACE(logger_, "H: " << dataset << ", pushed, index: " << frame->get_frame_number());
        this->push(frame);

        // Keep passing summed_spectra dataset to lvspectra
        LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " <<
          summed_spectra_->get_meta_data().get_dataset_name() << " dataset to " << lvspectra);
        this->push(lvspectra, summed_spectra_);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "stacked_frames dataset failed: " << e.what());
      }
    }
    else
    {
      // Push any other dataset
      LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << dataset << " dataset, frame number: "
        << frame_number);
      this->push(frame);
    }
  }

  /**
   * Write Histogram data to disk.
   */
  void HexitecHistogramPlugin::writeHistogramsToDisk()
  {
      spectra_bins_->set_frame_number(histogram_index_);
      summed_spectra_->set_frame_number(histogram_index_);
      if (pass_pixel_spectra_)
        pixel_spectra_->set_frame_number(rank_index_);

    const std::string& plugin_name = "hdf";
    // Temporary not pushing spectra_bins..
    LOG4CXX_DEBUG_LEVEL(3, logger_, "Pushing " << spectra_bins_->get_meta_data().get_dataset_name()
      << " dataset to " << plugin_name);
    this->push(plugin_name, spectra_bins_);

    // LOG4CXX_TRACE(logger_, " *** Pushing " << summed_spectra_->get_meta_data().get_dataset_name()
    //   << " dataset to " << plugin_name << ", histogram_index: " << histogram_index_);
    this->push(plugin_name, summed_spectra_);

    if (pass_pixel_spectra_)
    {
      LOG4CXX_TRACE(
      // LOG4CXX_DEBUG_LEVEL(3, 
      logger_, "Pushing " << pixel_spectra_->get_meta_data().get_dataset_name()
        << " dataset to " << plugin_name << " 'frame_number': "
        << pixel_spectra_->get_frame_number()  );
      this->push(plugin_name, pixel_spectra_);
    }
  }

  /**
   * Perform processing on the frame.  Calculate histograms based upon
   * each frame.
   * 
   * \param[frame] frame - Pointer to a frame object.
   */
  void HexitecHistogramPlugin::add_frame_data_to_histogram_with_sum(float *frame)
  {
    float total = 0.0f;
    const void* pixel_ptr = static_cast<const void*>(
      static_cast<const char*>(pixel_spectra_->get_data_ptr()));
    void* pixel_input_ptr = static_cast<void *>(
      static_cast<char *>(const_cast<void *>(pixel_ptr)));

    const void* summed_ptr = static_cast<const void*>(
      static_cast<const char*>(summed_spectra_->get_data_ptr()));
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
        total += thisEnergy;
      }
    }
    LOG4CXX_TRACE(logger_, "* Histogram frame number: " << histogram_index_ <<
      ", total pixel value: " << total);
  }

  // Called when the user NOT selected spectrum option
  void HexitecHistogramPlugin::addFrameDataToHistogram(float *frame)
  {
    float *currentHistogram = static_cast<float *>(pixel_spectra_->get_data_ptr());
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

  /** Parse the number of sensors map configuration string.
   * 
   * This method parses a configuration string containing number of sensors mapping information,
   * which is expected to be of the format "NxN" e.g, 2x2. The map is saved in a member
   * variable.
   * 
   * \param[in] sensors_layout_str - string of number of sensors configured
   * \return number of valid map entries parsed from string
   */
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

    image_width_  = sensors_layout_[0].sensor_columns_ * Hexitec::pixel_columns_per_sensor;
    image_height_ = sensors_layout_[0].sensor_rows_ * Hexitec::pixel_rows_per_sensor;
    image_pixels_ = image_width_ * image_height_;

    // Return the number of valid entries parsed
    return sensors_layout_.size();
  }

} /* namespace FrameProcessor */
