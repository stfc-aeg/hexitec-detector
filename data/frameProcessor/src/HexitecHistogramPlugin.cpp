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
  const std::string HexitecHistogramPlugin::CONFIG_MAX_COLS 		= "max_cols";
  const std::string HexitecHistogramPlugin::CONFIG_MAX_ROWS 		= "max_rows";

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
	    fem_total_pixels_(fem_pixels_per_rows_ * fem_pixels_per_columns_)
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
  }

  /**
   * Destructor.
   */
  HexitecHistogramPlugin::~HexitecHistogramPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecHistogramPlugin destructor.");

    free(summed_histogram_);
    summed_histogram_ = NULL;
    free(hexitec_bin_);
    hexitec_bin_ = NULL;
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
    float *pHxtBin = hexitec_bin_;
    for (long long i = bin_start_; i < number_bins_; i++, currentBin += bin_width_)
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
   * - bin_start_								<=> bin_start_
   * - bin_end_									<=> bin_end_
   * - bin_width_								<=> bin_width_
	 * - fem_pixels_per_columns_	<=> max_cols
	 * - fem_pixels_per_rows_ 		<=> max_rows
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
    	bin_end_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_BIN_END);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_WIDTH))
		{
    	bin_width_ = config.get_param<double>(HexitecHistogramPlugin::CONFIG_BIN_WIDTH);
		}

    number_bins_      = (int)(((bin_end_ - bin_start_) / bin_width_) + 0.5);

    if (config.has_param(HexitecHistogramPlugin::CONFIG_MAX_COLS))
    {
      fem_pixels_per_columns_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_MAX_COLS);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_MAX_ROWS))
    {
      fem_pixels_per_rows_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_MAX_ROWS);
    }

    fem_total_pixels_ = fem_pixels_per_columns_ * fem_pixels_per_rows_;

    //    histogram_per_pixel_ = hexitec_bin_ + number_bins_;

    // Free the existing allocated histogram memory
    free(summed_histogram_);
    summed_histogram_ = NULL;
    free(hexitec_bin_);
    hexitec_bin_ = NULL;
    // (Re-)Initialise memory
    initialiseHistograms();
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
        static_cast<const char*>(frame->get_data()));

    // Check dataset; Which set determines how to proceed..
    const std::string& dataset = frame->get_dataset_name();
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

				// Write histograms to disc when the maximum number of frames received
				if (frames_counter_ == max_frames_received_)
				{
					/// Time to push current histogram data

					// Determine the size of the histograms
					const std::size_t float_size = number_bins_ * sizeof(float);
					const std::size_t long_long_size = number_bins_ * sizeof(long long);
		      /// Total amount of memory covered by the pixel histograms
		      const std::size_t pixel_histograms_size = image_pixels_ * number_bins_ * sizeof(float);

					// Setup the dimension(s) for energy_bins, summed_histograms
					dimensions_t dims(1);
					dims[0] = number_bins_;

					// Setup the energy bins

					std::string dataset_name = "energy_bins";
					boost::shared_ptr<Frame> energy_bins;
					energy_bins = boost::shared_ptr<Frame>(new Frame(dataset_name));

					energy_bins->set_frame_number(0);

					energy_bins->set_dimensions(dims);
					energy_bins->copy_data(hexitec_bin_, float_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset_name <<
																 " dataset, frame number: " << 0);
					this->push(energy_bins);

					// Setup the summed histograms

					dataset_name = "summed_histograms";
					boost::shared_ptr<Frame> summed_histograms;
					summed_histograms = boost::shared_ptr<Frame>(new Frame(dataset_name));

					summed_histograms->set_frame_number(0);

					summed_histograms->set_dimensions(dims);
					summed_histograms->copy_data(summed_histogram_, long_long_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset_name <<
																 " dataset, frame number: " << 0);
					this->push(summed_histograms);

					// Setup the pixels' histograms

					// Setup the dimensions pixel_histograms
					dimensions_t pxls_dims(2);
					pxls_dims[0] = image_pixels_;
					pxls_dims[1] = number_bins_;

					dataset_name = "pixel_histograms";

					boost::shared_ptr<Frame> pixel_histograms;
					pixel_histograms = boost::shared_ptr<Frame>(new Frame(dataset_name));

					pixel_histograms->set_frame_number(0);

					pixel_histograms->set_dimensions(pxls_dims);
					pixel_histograms->copy_data(histogram_per_pixel_, pixel_histograms_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset_name <<
																 " dataset, frame number: " << 0);
					this->push(pixel_histograms);

					// Clear histogram values
			    memset(histogram_per_pixel_, 0, (number_bins_ * image_pixels_) * sizeof(float));
			    memset(summed_histogram_, 0, number_bins_ * sizeof(long long));

					frames_counter_ = 0;
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
   * Perform processing on the frame.  Calculate histograms based upon
   * each frame, writing resulting datasets to file when configured
	 * maximum number of frames received.
   *
   * \param[frame] frame - Pointer to a Frame object.
   */
  void HexitecHistogramPlugin::add_frame_data_to_histogram_with_sum(float *frame)
  {
		float *currentHistogram = &histogram_per_pixel_[0];
		long long *summed = &summed_histogram_[0];
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

} /* namespace FrameProcessor */

