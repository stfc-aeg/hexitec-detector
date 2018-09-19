/*
 * HexitecHistogramPlugin.cpp
 *
 *  Created on: 24 Jul 2018
 *      Author: ckd27546
 */

#include <HexitecHistogramPlugin.h>

namespace FrameProcessor
{

  const std::string HexitecHistogramPlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecHistogramPlugin::CONFIG_IMAGE_HEIGHT = "height";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecHistogramPlugin::HexitecHistogramPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecHistogramPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecHistogramPlugin constructor.");

    frameSize = image_width_ * image_height_;
    binStart   = 0;
    binEnd     = 12;
    binWidth   = 1.0;
    nBins      = (int)(((binEnd - binStart) / binWidth) + 0.5);;

//    hxtV3Buffer.allData = (float *) calloc((nBins * frameSize) + nBins, sizeof(float));
//    hxtBin = hxtV3Buffer.allData;
//    histogramPerPixel = hxtV3Buffer.allData + nBins;

    hxtBin = (float *) malloc(((nBins * frameSize) + nBins) * sizeof(float));
    memset(hxtBin, 0, ((nBins * frameSize) + nBins) * sizeof(float) );
    histogramPerPixel = hxtBin + nBins;

    summedHistogram = (long long *) malloc(nBins * sizeof(long long));
    memset(summedHistogram, 0, nBins * sizeof(long long));
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
    LOG4CXX_TRACE(logger_, "Calculating histograms..");

    // Determine the size of the output reordered image
    const std::size_t output_image_size = reordered_image_size();

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
			// Pointers to reordered image buffer - will be allocated on demand
			void* reordered_image = NULL;

			try
			{

				// Check that the pixels are contained within the dimensions of the
				// specified output image, otherwise throw an error
				if (FEM_TOTAL_PIXELS > image_pixels_)
				{
					std::stringstream msg;
					msg << "Pixel count inferred from FEM ("
							<< FEM_TOTAL_PIXELS
							<< ") will exceed dimensions of output image (" << image_pixels_ << ")";
					throw std::runtime_error(msg.str());
				}

				// Allocate buffer to receive reordered image.
				reordered_image = (void*)malloc(output_image_size);
				if (reordered_image == NULL)
				{
					throw std::runtime_error("Failed to allocate temporary buffer for reordered image");
				}

				// Calculate pointer into the input image data based on loop index
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

//				reorder_pixels(static_cast<float *>(input_ptr),
//														 static_cast<float *>(reordered_image));


				// Set the frame image to the reordered image buffer if appropriate
				if (reordered_image)
				{
					// Setup the frame dimensions
					dimensions_t dims(2);
					dims[0] = image_height_;
					dims[1] = image_width_;

					boost::shared_ptr<Frame> data_frame;
					data_frame = boost::shared_ptr<Frame>(new Frame(dataset));

					data_frame->set_frame_number(frame->get_frame_number());

					data_frame->set_dimensions(dims);
					data_frame->copy_data(reordered_image, output_image_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
		 														 " dataset, frame number: " << frame->get_frame_number());
					this->push(data_frame);

					free(reordered_image);
					reordered_image = NULL;
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

  /**
   * Determine the size of a reordered image size based on the counter depth.
   *
   * \return size of the reordered image in bytes
   */
  std::size_t HexitecHistogramPlugin::reordered_image_size() {

    return image_width_ * image_height_ * sizeof(float);
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

