/*
 * HexitecHistogramPlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecHistogramPlugin.h>

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
    logger_ = Logger::getLogger("FW.HexitecHistogramPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecHistogramPlugin constructor.");

    frameSize = image_width_ * image_height_;
    binStart   = 0;
    binEnd     = 8000;
    binWidth   = 10;
    nBins      = (int)(((binEnd - binStart) / binWidth) + 0.5);

    initialiseHistograms();
  }

  /**
   * Destructor.
   */
  HexitecHistogramPlugin::~HexitecHistogramPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecHistogramPlugin destructor.");

    free(summedHistogram);
    summedHistogram = NULL;
    free(hxtBin);
    hxtBin = NULL;
    // histogramPerPixel points at memory within hxtBin
    histogramPerPixel = NULL;
  }

  /**
   * Allocate and initialise histograms
   *
   */
  void HexitecHistogramPlugin::initialiseHistograms()
  {
    hxtBin = (float *) malloc(((nBins * frameSize) + nBins) * sizeof(float));
    memset(hxtBin, 0, ((nBins * frameSize) + nBins) * sizeof(float) );
    histogramPerPixel = hxtBin + nBins;

    summedHistogram = (long long *) malloc(nBins * sizeof(long long));
    memset(summedHistogram, 0, nBins * sizeof(long long));

    // Initialise bins
    float currentBin = binStart;
    float *pHxtBin = hxtBin;
    for (long long i = binStart; i < nBins; i++, currentBin += binWidth)
    {
       *pHxtBin = currentBin;
       pHxtBin++;
    }

  }
  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - max_frames_received
   * - binStart
   * - binEnd
   * - binWidth
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[out] reply - Reference to the reply IpcMessage object.
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
    	binStart = config.get_param<int>(HexitecHistogramPlugin::CONFIG_BIN_START);
		}

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_END))
    {
    	binEnd = config.get_param<int>(HexitecHistogramPlugin::CONFIG_BIN_END);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_BIN_WIDTH))
		{
    	binWidth = config.get_param<double>(HexitecHistogramPlugin::CONFIG_BIN_WIDTH);
		}

    nBins      = (int)(((binEnd - binStart) / binWidth) + 0.5);

    if (config.has_param(HexitecHistogramPlugin::CONFIG_MAX_COLS))
    {
      fem_pixels_per_columns_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_MAX_COLS);
    }

    if (config.has_param(HexitecHistogramPlugin::CONFIG_MAX_ROWS))
    {
      fem_pixels_per_rows_ = config.get_param<int>(HexitecHistogramPlugin::CONFIG_MAX_ROWS);
    }

    fem_total_pixels_ = fem_pixels_per_columns_ * fem_pixels_per_rows_;

    //    histogramPerPixel = hxtBin + nBins;

    // Free the existing allocated histogram memory
    free(summedHistogram);
    summedHistogram = NULL;
    free(hxtBin);
    hxtBin = NULL;
    // (Re-)Initialise memory
    initialiseHistograms();
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
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

				// Pointer to the input image data
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				// Add this frame's contribution onto histograms
				addFrameDataToHistogramWithSum(static_cast<float *>(input_ptr));

				// Write histograms to disc when the maximum number of frames received
				if (frames_counter_ == max_frames_received_)
				{
					/// Time to push current histogram data

					// Determine the size of the histograms
					const std::size_t float_size = nBins * sizeof(float);
					const std::size_t long_long_size = nBins * sizeof(long long);
		      /// Total amount of memory covered by the pixel histograms
		      const std::size_t pixel_histograms_size = frameSize * nBins * sizeof(float);

					// Setup the dimension(s) for energy_bins, summed_histograms
					dimensions_t dims(1);
					dims[0] = nBins;

					// Setup the energy bins

					std::string dataset_name = "energy_bins";
					boost::shared_ptr<Frame> energy_bins;
					energy_bins = boost::shared_ptr<Frame>(new Frame(dataset_name));

					energy_bins->set_frame_number(0);

					energy_bins->set_dimensions(dims);
					energy_bins->copy_data(hxtBin, float_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset_name <<
																 " dataset, frame number: " << 0);
					this->push(energy_bins);

					// Setup the summed histograms

					dataset_name = "summed_histograms";
					boost::shared_ptr<Frame> summed_histograms;
					summed_histograms = boost::shared_ptr<Frame>(new Frame(dataset_name));

					summed_histograms->set_frame_number(0);

					summed_histograms->set_dimensions(dims);
					summed_histograms->copy_data(summedHistogram, long_long_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset_name <<
																 " dataset, frame number: " << 0);
					this->push(summed_histograms);

					// Setup the pixels' histograms

					// Setup the dimensions pixel_histograms
					dimensions_t pxls_dims(2);
					pxls_dims[0] = frameSize;
					pxls_dims[1] = nBins;

					dataset_name = "pixel_histograms";

					boost::shared_ptr<Frame> pixel_histograms;
					pixel_histograms = boost::shared_ptr<Frame>(new Frame(dataset_name));

					pixel_histograms->set_frame_number(0);

					pixel_histograms->set_dimensions(pxls_dims);
					pixel_histograms->copy_data(histogramPerPixel, pixel_histograms_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset_name <<
																 " dataset, frame number: " << 0);
					this->push(pixel_histograms);

					// Clear histogram values
			    memset(histogramPerPixel, 0, (nBins * frameSize) * sizeof(float));
			    memset(summedHistogram, 0, nBins * sizeof(long long));

					frames_counter_ = 0;
				}

				/// Histogram will access data dataset but not change it in any way
				/// 	Therefore do not need to check frame dimensions, malloc memory,
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

  // Called when the user NOT selected spectrum option
  void HexitecHistogramPlugin::addFrameDataToHistogram(float *frame)
  {
      float *currentHistogram = &histogramPerPixel[0];
      float thisEnergy;
      int bin;
      int pixel;

      for (int i = 0; i < frameSize; i++)
      {
         pixel = i;
         thisEnergy = frame[i];
         if (thisEnergy == 0)
             continue;
         bin = (int)((thisEnergy / binWidth));
         if (bin <= nBins)
         {
            (*(currentHistogram + (pixel * nBins) + bin))++;
         }
         else
         {
   /*         qDebug() << "BAD BIN = " << bin << " in pixel " << pixel << " ("
                     << (int)(pixel/80) << "," << (pixel % 80) <<")"*/;
         }
      }
  }

  // Called when the user HAS selected spectrum option
  void HexitecHistogramPlugin::addFrameDataToHistogramWithSum(float *frame)
  {
		float *currentHistogram = &histogramPerPixel[0];
		long long *summed = &summedHistogram[0];
		float thisEnergy;
		int bin;
		int pixel;
		for (int i = 0; i < frameSize; i++)
		{
			pixel = i;
			thisEnergy = frame[i];

			if (thisEnergy <= 0.0)
				continue;
			bin = (int)((thisEnergy / binWidth));
			if (bin <= nBins)
			{
				(*(currentHistogram + (pixel * nBins) + bin))++;
				(*(summed + bin)) ++;
			}
			else
			{
				/*qDebug() << "BAD BIN = " << bin << " in pixel " << pixel << " ("
									<< (int)(pixel/80) << "," << (pixel % 80) <<")"*/;
			}
		}
  }

} /* namespace FrameProcessor */

