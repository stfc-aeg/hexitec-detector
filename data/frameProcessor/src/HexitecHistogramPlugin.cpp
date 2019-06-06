/*
 * HexitecHistogramPlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecHistogramPlugin.h>
#include "version.h"

namespace FrameProcessor
{

  const std::string HexitecHistogramPlugin::CONFIG_IMAGE_WIDTH  = "width";
  const std::string HexitecHistogramPlugin::CONFIG_IMAGE_HEIGHT = "height";
  const std::string HexitecHistogramPlugin::CONFIG_MAX_FRAMES   = "max_frames_received";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_START    = "bin_start";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_END 		  = "bin_end";
  const std::string HexitecHistogramPlugin::CONFIG_BIN_WIDTH 		= "bin_width";
  const std::string HexitecHistogramPlugin::CONFIG_MAX_COLS 		= "fem_max_cols";
  const std::string HexitecHistogramPlugin::CONFIG_MAX_ROWS 		= "fem_max_rows";
  const std::string HexitecHistogramPlugin::CONFIG_FLUSH_HISTOS = "flush_histograms";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecHistogramPlugin::HexitecHistogramPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
			max_frames_received_(0),
			frames_counter_(0),
	    fem_pixels_per_rows_(80),
	    fem_pixels_per_columns_(80),
	    fem_total_pixels_(fem_pixels_per_rows_ * fem_pixels_per_columns_),
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
    //
    dCounter = 0;
  }

  /**
   * Destructor.
   */
  HexitecHistogramPlugin::~HexitecHistogramPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecHistogramPlugin destructor.");

    // These will become redundant:
    free(summed_histogram_);
    summed_histogram_ = NULL;
    // histogram_per_pixel_ points at memory within hexitec_bin_
    histogram_per_pixel_ = NULL;
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
		hexitec_bin_ = (float *) calloc((number_bins_ * image_pixels_) + number_bins_, sizeof(float));

    histogram_per_pixel_ = hexitec_bin_ + number_bins_;

    summed_histogram_ = (long long *) calloc(number_bins_, sizeof(long long));

    // Initialise bins
    float currentBin = bin_start_;
    float *pHxtBin = hexitec_bin_;	// Old implementation
    for (long i = bin_start_; i < number_bins_; i++, currentBin += bin_width_)
    {
       *pHxtBin = currentBin;
       pHxtBin++;
    }

  }
  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - image_width_ 						<=> width
 	 * - image_height_	 					<=> height
   * - max_frames_received_			<=> max_frames_received
   * - bin_start_								<=> bin_start
   * - bin_end_									<=> bin_end
   * - bin_width_								<=> bin_width
   * - fem_pixels_per_columns_	<=> fem_max_cols
   * - fem_pixels_per_rows_			<=> fem_max_rows
   * - flush_histograms_				<=> flush_histograms
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecHistogramPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecHistogramPlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

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

    if (config.has_param(HexitecHistogramPlugin::CONFIG_MAX_COLS))
    {
      fem_pixels_per_columns_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_MAX_COLS);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_MAX_ROWS))
    {
      fem_pixels_per_rows_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_MAX_ROWS);
    }

    fem_total_pixels_ = fem_pixels_per_columns_ * fem_pixels_per_rows_;

    if (config.has_param(HexitecHistogramPlugin::CONFIG_FLUSH_HISTOS))
    {
    	flush_histograms_ = config.get_param<bool>(HexitecHistogramPlugin::CONFIG_FLUSH_HISTOS);

    	if (flush_histograms_)
    	{
				/// Time to push current histogram data
				writeHistogramsToDisk();

		    memset(histogram_per_pixel_, 0, (number_bins_ * image_pixels_) * sizeof(float));
		    memset(summed_histogram_, 0, number_bins_ * sizeof(long long));

				frames_counter_ = 0;

    		// Clear flush_histograms_
    		flush_histograms_ = false;
    	}
    }

    //    histogram_per_pixel_ = hexitec_bin_ + number_bins_;

    // Free the existing allocated histogram memory
    free(summed_histogram_);
    summed_histogram_ = NULL;
    free(hexitec_bin_);
    hexitec_bin_ = NULL;
    // (Re-)Initialise memory
    initialiseHistograms();
    dCounter++;
  }

  void HexitecHistogramPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
  	// Return the configuration of the histogram plugin
  	std::string base_str = get_name() + "/";
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_IMAGE_WIDTH, image_width_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_IMAGE_HEIGHT, image_height_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_MAX_FRAMES , max_frames_received_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_BIN_START, bin_start_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_BIN_END , bin_end_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_BIN_WIDTH, bin_width_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_MAX_COLS, fem_pixels_per_columns_);
		reply.set_param(base_str + HexitecHistogramPlugin::CONFIG_MAX_ROWS, fem_pixels_per_rows_);
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
    status.set_param(get_name() + "/image_width", image_width_);
    status.set_param(get_name() + "/image_height", image_height_);
    status.set_param(get_name() + "/max_frames_received", max_frames_received_);
    status.set_param(get_name() + "/bin_start", bin_start_);
    status.set_param(get_name() + "/bin_end", bin_end_);
    status.set_param(get_name() + "/bin_width", bin_width_);
    status.set_param(get_name() + "/fem_max_rows", fem_pixels_per_rows_);
    status.set_param(get_name() + "/fem_max_cols", fem_pixels_per_columns_);
    status.set_param(get_name() + "/flush_histograms", flush_histograms_);
  }

  /**
   * Reset process plugin statistics, i.e. counter of packets lost
   */
  bool HexitecHistogramPlugin::reset_statistics(void)
  {
  	// Reset These parameters or not..??!
    image_pixels_ = image_width_ * image_height_;
    number_bins_  = (int)(((bin_end_ - bin_start_) / bin_width_) + 0.5);
    // Free the existing allocated histogram memory
    free(summed_histogram_);
    summed_histogram_ = NULL;
    free(hexitec_bin_);
    hexitec_bin_ = NULL;
    // (Re-)Initialise memory
    initialiseHistograms();
    //
    dCounter++;

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
//				if ( ((frames_counter_ % max_frames_received_) == 0) &&
//						(frames_counter_ != 0) )	// Fix why empty histograms written to 2nd (third et cetera) HDF5 files? - Not quite..
				if (frames_counter_ == max_frames_received_)
				{
					LOG4CXX_TRACE(logger_, " ----------------------------------------------------------------------------------------------");

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
		// Determine the size of the histograms
		const std::size_t float_size = number_bins_ * sizeof(float);
		const std::size_t long_long_size = number_bins_ * sizeof(long long);
    /// Total amount of memory covered by the pixel histograms
    const std::size_t pixel_histograms_size = image_pixels_ * number_bins_ * sizeof(float);

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

    boost::shared_ptr<Frame> energy_bins;
		energy_bins = boost::shared_ptr<Frame>(new DataBlockFrame(energy_meta, float_size));

		// Get a pointer to the data buffer in the output frame
		void* energy_ptr = energy_bins->get_data_ptr();

		// Copy summed_histrogram_ into energy_bins object
//		memcpy(energy_ptr, hexitec_bin_, number_bins_);	// Old implementation, produces funny results
		this->copy_histograms(hexitec_bin_, static_cast<float *>(energy_ptr), number_bins_);

		LOG4CXX_TRACE(logger_, "Pushing " << energy_bins->get_meta_data().get_dataset_name() << " dataset");
		this->push(energy_bins);

		// Setup the summed histograms

		FrameMetaData summed_meta;

		summed_meta.set_dimensions(dims);
		summed_meta.set_compression_type(no_compression);
		summed_meta.set_data_type(raw_64bit);
		summed_meta.set_frame_number(0);
		summed_meta.set_dataset_name("summed_histograms");

    boost::shared_ptr<Frame> summed_histograms;
		summed_histograms = boost::shared_ptr<Frame>(new DataBlockFrame(summed_meta, long_long_size));

		// Get a pointer to the data buffer in the output frame
		void* summed_ptr = summed_histograms->get_data_ptr();

		// Copy summed_histrogram_ into summed_histograms object
//		memcpy(summed_ptr, summed_histogram_, number_bins_);	// Old implementation
		this->copy_histograms(summed_histogram_, static_cast<long long *>(summed_ptr), number_bins_);

		LOG4CXX_TRACE(logger_, "Pushing " << summed_histograms->get_meta_data().get_dataset_name() << " dataset");
		this->push(summed_histograms);

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

		boost::shared_ptr<Frame> pixel_histograms;
		pixel_histograms = boost::shared_ptr<Frame>(new DataBlockFrame(pixel_meta, pixel_histograms_size));

		// Get a pointer to the data buffer in the output frame
		void* pixel_ptr = pixel_histograms->get_data_ptr();

		// Copy summed_histrogram_ into pixel_histograms object
//		memcpy(pixel_ptr, histogram_per_pixel_, image_pixels_ * number_bins_);	// Old implementation
		this->copy_histograms(histogram_per_pixel_, static_cast<float *>(pixel_ptr), image_pixels_ * number_bins_);

		LOG4CXX_TRACE(logger_, "Pushing " << pixel_histograms->get_meta_data().get_dataset_name() << " dataset");
		this->push(pixel_histograms);

  }

  /**
   * Perform processing on the frame.  Calculate histograms based upon
   * each frame.
   *
   * \param[frame] frame - Pointer to a frame object.
   */
  void HexitecHistogramPlugin::add_frame_data_to_histogram_with_sum(float *frame)
  {
		float *currentHistogram = &histogram_per_pixel_[0];	// Old Implementation
		long long *summed = &summed_histogram_[0];	// Old implementation

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
			else
			{
				/*qDebug() << "BAD BIN = " << bin << " in pixel " << pixel << " ("
									<< (int)(pixel/80) << "," << (pixel % 80) <<")"*/;
			}
		}
  }

  // Called when the user NOT selected spectrum option
  void HexitecHistogramPlugin::addFrameDataToHistogram(float *frame)
  {
      float *currentHistogram = &histogram_per_pixel_[0];
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
         else
         {
   /*         qDebug() << "BAD BIN = " << bin << " in pixel " << pixel << " ("
                     << (int)(pixel/80) << "," << (pixel % 80) <<")"*/;
         }
      }
  }

	void HexitecHistogramPlugin::copy_histograms(float *histograms, float *frame_data_ptr,
											 long long number_bins)
	{

		for (int i=0; i < number_bins; i++)
		{
			frame_data_ptr[i] = histograms[i];
		}
	}

	void HexitecHistogramPlugin::copy_histograms(long long *histograms, long long *frame_data_ptr,
											 long long number_bins)
	{

		for (int i=0; i < number_bins; i++)
		{
			frame_data_ptr[i] = histograms[i];
		}
	}

} /* namespace FrameProcessor */

