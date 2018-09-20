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

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecHistogramPlugin::HexitecHistogramPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_),
			max_frames_received_(0),
			frames_counter_(0)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecHistogramPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecHistogramPlugin constructor.");

    frameSize = image_width_ * image_height_;
    binStart   = 0;
    binEnd     = 8000;
    binWidth   = 10;
    nBins      = 800;

    nBins      = (int)(((binEnd - binStart) / binWidth) + 0.5);

//    hxtV3Buffer.allData = (float *) calloc((nBins * frameSize) + nBins, sizeof(float));
//    hxtBin = hxtV3Buffer.allData;
//    histogramPerPixel = hxtV3Buffer.allData + nBins;

    hxtBin = NULL;
    histogramPerPixel = NULL;

    summedHistogram = NULL;

    hxtsProcessed = 0;

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
  }

  /**
   * Configure the Hexitec plugin.  This receives an IpcMessage which should be processed
   * to configure the plugin, and any response can be added to the reply IpcMessage.  This
   * plugin supports the following configuration parameters:
   * - bitdepth
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
    	binWidth = config.get_param<int>(HexitecHistogramPlugin::CONFIG_BIN_WIDTH);
		}

    nBins      = (int)(((binEnd - binStart) / binWidth) + 0.5);

//    hxtV3Buffer.allData = (float *) calloc((nBins * frameSize) + nBins, sizeof(float));
//    hxtBin = hxtV3Buffer.allData;
//    histogramPerPixel = hxtV3Buffer.allData + nBins;

//    LOG4CXX_TRACE(logger_, "setting up hxtBin.. binEnd: " << binEnd << " binStart: " <<
//    							binStart << " binWidth: " << binWidth << " nBins: " << nBins);

    hxtBin = (float *) malloc(((nBins * frameSize) + nBins) * sizeof(float));
    memset(hxtBin, 0, ((nBins * frameSize) + nBins) * sizeof(float) );
    histogramPerPixel = hxtBin + nBins;

    LOG4CXX_TRACE(logger_, "\t\t\te sizeof summedHistogram: " << sizeof(summedHistogram));
    summedHistogram = (long long *) malloc(nBins * sizeof(long long));
    memset(summedHistogram, 0, nBins * sizeof(long long));

    // Initialise bins
    float currentBin = binStart;
    float *pHxtBin = hxtBin;
    for (long long i = binStart; i < nBins; i++, currentBin += binWidth)
    {
       *pHxtBin = currentBin;
//       if ( i < 12)
//         LOG4CXX_TRACE(logger_, "\t\t\t\tcurrentBin: " << currentBin << " pHxtBin: " << *pHxtBin);
       pHxtBin++;
    }

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
//    status.set_param(get_name() + "/packets_lost", packets_lost_);
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecHistogramPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Calculating histograms.");

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
        static_cast<const char*>(frame->get_data()));

    // Check dataset; Which set determines how to proceed..
    const std::string& dataset = frame->get_dataset_name();
    if (dataset.compare(std::string("raw")) == 0)
    {
			LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
 														 " dataset, frame number: " << frame->get_frame_number());
			this->push(frame);
    }
    else if (dataset.compare(std::string("data")) == 0)
    {
			try
			{
				/// Histogram will access data dataset but not change it in any way
				/// 	Therefore do not need to check frame dimensions, malloc memory,
				/// 	etc

				frames_counter_++;
				// Pass on data dataset unmodified:
				LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
	 														 " dataset, frame number: " << frame->get_frame_number());
				this->push(frame);

//				// Check that the pixels are contained within the dimensions of the
//				// specified output image, otherwise throw an error
//				if (FEM_TOTAL_PIXELS > image_pixels_)
//				{
//					std::stringstream msg;
//					msg << "Pixel count inferred from FEM ("
//							<< FEM_TOTAL_PIXELS
//							<< ") will exceed dimensions of output image (" << image_pixels_ << ")";
//					throw std::runtime_error(msg.str());
//				}

				// Calculate pointer into the input image data based on loop index
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

//				reorder_pixels(static_cast<float *>(input_ptr),
//														 static_cast<float *>(histogram_data));

				// Add frame's contribution onto histograms
				addFrameDataToHistogramWithSum(static_cast<float *>(input_ptr));

				// Only bright histograms to disc if this is the final frame of the acquisition
				if (frames_counter_ == max_frames_received_)
				{
					/// Time to push current histogram data

					// Determine the size of the histograms
					const std::size_t float_size = nBins * sizeof(float);
					const std::size_t long_long_size = nBins * sizeof(long long);

//					// Pointers to reordered image buffer - will be allocated on demand
//					void* histogram_data = NULL;

//					// Allocate buffer to receive reordered image.
//					histogram_data = (void*)malloc(histogram_size);
//					if (histogram_data == NULL)
//					{
//						throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
//					}


					// Setup the frame dimensions
					dimensions_t dims(2);
					dims[0] = nBins;
//					dims[1] = nBins;

					boost::shared_ptr<Frame> energy_bins;
					energy_bins = boost::shared_ptr<Frame>(new Frame("energy_bins"));

					energy_bins->set_frame_number(frame->get_frame_number());

					energy_bins->set_dimensions(dims);
					energy_bins->copy_data(hxtBin, float_size);

					LOG4CXX_TRACE(logger_, "Pushing " << "energy_bins" <<
																 " dataset, frame number: " << frame->get_frame_number());
					this->push(energy_bins);

					// Setup the summed histograms

					boost::shared_ptr<Frame> summed_histograms;
					summed_histograms = boost::shared_ptr<Frame>(new Frame("summed_histograms"));

					summed_histograms->set_frame_number(frame->get_frame_number());

					summed_histograms->set_dimensions(dims);
					summed_histograms->copy_data(summedHistogram, long_long_size);

					LOG4CXX_TRACE(logger_, "Pushing " << "summedHistograms" <<
																 " dataset, frame number: " << frame->get_frame_number());
					this->push(summed_histograms);

					/// Clear (but do not free) the memory used
			    memset(hxtBin, 0, ((nBins * frameSize) + nBins) * sizeof(float) );
			    memset(summedHistogram, 0, nBins * sizeof(long long));

					frames_counter_ = 0;
				}
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
                     << (int)(pixel/400) << "," << (pixel % 400) <<")"*/;
         }
      }

      hxtsProcessed++;
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

        if (thisEnergy == 0)
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
                    << (int)(pixel/400) << "," << (pixel % 400) <<")"*/;
        }
     }

     hxtsProcessed++;
  }

} /* namespace FrameProcessor */

