/*
 * HexitecAdditionPlugin.cpp
 *
 *  Created on: 08 Aug 2018
 *      Author: ckd27546
 */

#include <HexitecAdditionPlugin.h>

namespace FrameProcessor
{

  const std::string HexitecAdditionPlugin::CONFIG_IMAGE_WIDTH = "width";
  const std::string HexitecAdditionPlugin::CONFIG_IMAGE_HEIGHT = "height";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecAdditionPlugin::HexitecAdditionPlugin() :
      image_width_(80),
      image_height_(80),
      image_pixels_(image_width_ * image_height_)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FW.HexitecAdditionPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecAdditionPlugin constructor.");

    directionalDistance = 1;  // Set to 1 for 3x3: 2 for 5x5 pixel grid
    nRows = image_height_;
    nCols = image_width_;

  }

  /**
   * Destructor.
   */
  HexitecAdditionPlugin::~HexitecAdditionPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecAdditionPlugin destructor.");
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
  void HexitecAdditionPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecAdditionPlugin::CONFIG_IMAGE_WIDTH))
    {
      image_width_ = config.get_param<int>(HexitecAdditionPlugin::CONFIG_IMAGE_WIDTH);
    }

    if (config.has_param(HexitecAdditionPlugin::CONFIG_IMAGE_HEIGHT))
    {
      image_height_ = config.get_param<int>(HexitecAdditionPlugin::CONFIG_IMAGE_HEIGHT);
    }

    image_pixels_ = image_width_ * image_height_;

  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecAdditionPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecAdditionPlugin");
  }

  /**
   * Perform processing on the frame.  Depending on the selected bit depth
   * the corresponding pixel re-ordering algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecAdditionPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying CS Addition algorithm.");

    // Determine the size of the output processed image
    const std::size_t output_image_size = processed_image_size();

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
			// Pointers to processed image buffer - will be allocated on demand
			void* processed_image = NULL;

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

				// Allocate buffer to receive processed image.
				processed_image = (void*)malloc(output_image_size);
				if (processed_image == NULL)
				{
					throw std::runtime_error("Failed to allocate temporary buffer for processed image");
				}

				// Calculate pointer into the input image data based on loop index
				void* input_ptr = static_cast<void *>(
						static_cast<char *>(const_cast<void *>(data_ptr)));

				// Take Frame object at input_ptr, apply CS Addition algorithm and save results to
				//	at processed_image('s address)
				prepareChargedSharing(static_cast<float *>(input_ptr),
															static_cast<float *>(processed_image) );

				// Set the frame image to the processed image buffer if appropriate
				if (processed_image)
				{
					// Setup the frame dimensions
					dimensions_t dims(2);
					dims[0] = image_height_;
					dims[1] = image_width_;

					boost::shared_ptr<Frame> data_frame;
					data_frame = boost::shared_ptr<Frame>(new Frame(dataset) );

					data_frame->set_frame_number(frame->get_frame_number());

					data_frame->set_dimensions(dims);
					data_frame->copy_data(processed_image, output_image_size);

					LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
		 														 " dataset, frame number: " << frame->get_frame_number());
					this->push(data_frame);

					free(processed_image);
					processed_image = NULL;
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
   * Determine the size of a processed image size based on the counter depth.
   *
   * \return size of the processed image in bytes
   */
  std::size_t HexitecAdditionPlugin::processed_image_size() {

    return image_width_ * image_height_ * sizeof(float);
  }

  /**
   * Prepare frame for charged sharing processing
   *
   * \param[frame] frame - Pointer to the image data to be processed.
   *
   */
  void HexitecAdditionPlugin::prepareChargedSharing(float *inFrame, float *outFrame)
  {
     /// extendedFrame contains empty (1-2) pixel(s) on all 4 sides to enable charged
  	/// 	sharing algorithm execution
		int sidePadding          = 2 *  directionalDistance;
		int extendedFrameRows    = (nRows + sidePadding);
		int extendedFrameColumns = (nCols + sidePadding);
		int extendedFrameSize    = extendedFrameRows * extendedFrameColumns;

		float *extendedFrame;
		extendedFrame = (float*) malloc(extendedFrameSize * sizeof(float));
		memset(extendedFrame, 0, extendedFrameSize * sizeof(float));

		// Copy frame's each row into extendedFrame leaving (directionalDistance pixel(s))
		// 	padding on each side
		int startPosn = extendedFrameColumns * directionalDistance + directionalDistance;
		int endPosn   = extendedFrameSize;
		int increment = extendedFrameColumns;
		float *rowPtr = inFrame;

		for (int i = startPosn; i < endPosn; )
		{
			 memcpy(&(extendedFrame[i]), rowPtr, nCols * sizeof(float));
			 rowPtr = rowPtr + nCols;
			 i = i + increment;
		}

		//// CSD example frame, with directionalDistance = 1
		///
		///      0    1    2    3  ...  399  400  401
		///    402  403  404  405  ...  801  802  803
		///    804  805  806  807  ... 1203 1204 1205
		///   1206
		///   1608 1609 1610 1611  ... 2007 2008 2009
		///
		///   Where frame's first row is 400 pixels from position 403 - 802,
		///      second row is 805 - 1204, etc

		endPosn = extendedFrameSize - (extendedFrameColumns * directionalDistance)
								- directionalDistance;

		processAddition(extendedFrame, extendedFrameRows, startPosn, endPosn);

		/// Copy CSD frame (i.e. 402x402) back into originally sized frame (400x400)
		rowPtr = outFrame;
		for (int i = startPosn; i < endPosn; )
		{
			 memcpy(rowPtr, &(extendedFrame[i]), nCols * sizeof(float));
			 rowPtr = rowPtr + nCols;
			 i = i + increment;
		}

		free(extendedFrame);
		extendedFrame = NULL;
  }

  /**
   * Perform charged sharing algorithm
   *
   * \param[extendedFrame] extendedFrame - Pointer to the image data, surrounded by a frame
	 *																			 of zeros
   * \param[extendedFrameRows] extendedFrameRows - Number of rows of the extended frame
   * \param[startPosn] startPosn - Where the first pixel is in the frame
   * \param[endPosn] endPosn - Where the final pixel is in the frame
   *
   */
	void HexitecAdditionPlugin::processAddition(float *extendedFrame,
			int extendedFrameRows, int startPosn, int endPosn)
	{
	  float *neighbourPixel = NULL, *currentPixel = extendedFrame;
	  int rowIndexBegin = (-1*directionalDistance);
		int rowIndexEnd   = (directionalDistance+1);
		int colIndexBegin = rowIndexBegin;
		int colIndexEnd   = rowIndexEnd;
		int maxValue;

		for (int i = startPosn; i < endPosn;  i++)
		{
			if (extendedFrame[i] != 0)
			{
				maxValue = extendedFrame[i];
				currentPixel = (&(extendedFrame[i]));
				for (int row = rowIndexBegin; row < rowIndexEnd; row++)
				{
					for (int column = colIndexBegin; column < colIndexEnd; column++)
					{
						if ((row == 0) && (column == 0)) // Don't compare pixel with itself
							continue;

						neighbourPixel = (currentPixel + (extendedFrameRows*row)  + column);
						if (*neighbourPixel != 0)
						{
							if (*neighbourPixel > maxValue)
							{
								*neighbourPixel += extendedFrame[i];
								maxValue = *neighbourPixel;
								extendedFrame[i] = 0;
							}
							else
							{
								extendedFrame[i] += *neighbourPixel;
								maxValue = extendedFrame[i];
								*neighbourPixel = 0;
							}
						}
					}
				}
			}
		}
	}

} /* namespace FrameProcessor */

