/*
 * HexitecAdditionPlugin.cpp
 *
 *  Created on: 08 Aug 2018
 *      Author: Christian Angelsen
 */

#include <HexitecAdditionPlugin.h>
#include "version.h"

namespace FrameProcessor
{
  const std::string HexitecAdditionPlugin::CONFIG_PIXEL_GRID_SIZE = "pixel_grid_size";
  const std::string HexitecAdditionPlugin::CONFIG_SENSORS_LAYOUT  = "sensors_layout";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecAdditionPlugin::HexitecAdditionPlugin() :
      pixel_grid_size_(3)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecAdditionPlugin");
    logger_->setLevel(Level::getAll());
    LOG4CXX_TRACE(logger_, "HexitecAdditionPlugin version " <<
                            this->get_version_long() << " loaded.");

    directional_distance_ = (int)pixel_grid_size_/2;  // Set to 1 for 3x3: 2 for 5x5 pixel grid

    // Set image_width_, image_height_, image_pixels_, number_rows_, number_columns_
    sensors_layout_str_ = Hexitec::default_sensors_layout_map;
    parse_sensors_layout_map(sensors_layout_str_);
    ///
    debugFrameCounter = 0;
  }

  int HexitecAdditionPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecAdditionPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecAdditionPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecAdditionPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecAdditionPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
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
   * 
   * - sensors_layout_str_  <=> sensors_layout
   * - pixel_grid_size_ 		<=> pixel_grid_size
   *
   * \param[in] config - Reference to the configuration IpcMessage object.
   * \param[in] reply - Reference to the reply IpcMessage object.
   */
  void HexitecAdditionPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
    if (config.has_param(HexitecAdditionPlugin::CONFIG_SENSORS_LAYOUT))
    {
      sensors_layout_str_= config.get_param<std::string>(HexitecAdditionPlugin::CONFIG_SENSORS_LAYOUT);
      parse_sensors_layout_map(sensors_layout_str_);
    }

    if (config.has_param(HexitecAdditionPlugin::CONFIG_PIXEL_GRID_SIZE))
    {
      pixel_grid_size_ = config.get_param<unsigned int>(HexitecAdditionPlugin::CONFIG_PIXEL_GRID_SIZE);
      directional_distance_ = (int)pixel_grid_size_/2;  // Set to 1 for 3x3: 2 for 5x5 pixel grid
    }

  }

  void HexitecAdditionPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
    // Return the configuration of the process plugin
    std::string base_str = get_name() + "/";
    reply.set_param(base_str + HexitecAdditionPlugin::CONFIG_SENSORS_LAYOUT, sensors_layout_str_);
    reply.set_param(base_str + HexitecAdditionPlugin::CONFIG_PIXEL_GRID_SIZE, pixel_grid_size_);
  }

  /**
   * Collate status information for the plugin.  The status is added to the status IpcMessage object.
   *
   * \param[in] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecAdditionPlugin::status(OdinData::IpcMessage& status)
  {
    // Record the plugin's status items
    LOG4CXX_DEBUG(logger_, "Status requested for HexitecAdditionPlugin");
    status.set_param(get_name() + "/sensors_layout", sensors_layout_str_);
    status.set_param(get_name() + "/pixel_grid_size", pixel_grid_size_);
  }

  /**
   * Reset process plugin statistics
   */
  bool HexitecAdditionPlugin::reset_statistics(void)
  {
    // Nowt to reset..?

    return true;
  }

  /**
   * Perform processing on the frame.  The Charged Sharing algorithm is executed.
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecAdditionPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Applying CS Addition algorithm.");

    // Obtain a pointer to the start of the data in the frame
    const void* data_ptr = static_cast<const void*>(
    static_cast<const char*>(frame->get_data_ptr()));

    // Check datasets name
    FrameMetaData &frame_meta = frame->meta_data();
    const std::string& dataset = frame_meta.get_dataset_name();

    if (dataset.compare(std::string("raw_frames")) == 0)
    {
      LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
            " dataset, frame number: " << frame->get_frame_number());
      this->push(frame);
    }
    else if (dataset.compare(std::string("processed_frames")) == 0)
    {
      try
      {
        // Define pointer to the input image data
        void* input_ptr = static_cast<void *>(
          static_cast<char *>(const_cast<void *>(data_ptr)));

        // Take Frame object at input_ptr, apply CS Addition algorithm
        prepare_charged_sharing(static_cast<float *>(input_ptr));

        LOG4CXX_TRACE(logger_, "Pushing " << dataset <<
                  " dataset, frame number: " << frame->get_frame_number());
        this->push(frame);
      }
      catch (const std::exception& e)
      {
        LOG4CXX_ERROR(logger_, "HexitecAdditionPlugin failed: " << e.what());
      }
    }
    else
    {
      LOG4CXX_ERROR(logger_, "Unknown dataset encountered: " << dataset);
    }
  }

  /**
   * Prepare frame for charged sharing processing
   *
   * \param[in] input_frame - Pointer to the image data to be processed.
   * \param[in] output_frame - Pointer to the processed image data.
   */
  void HexitecAdditionPlugin::prepare_charged_sharing(float *frame)
  {
    /// extendedFrame contains empty (1-2) pixel(s) on all 4 sides to enable charged
    /// 	sharing algorithm execution
    int sidePadding          = 2 *  directional_distance_;
    int extendedFrameRows    = (number_rows_ + sidePadding);
    int extendedFrameColumns = (number_columns_ + sidePadding);
    int extendedFrameSize    = extendedFrameRows * extendedFrameColumns;

    float *extendedFrame = NULL;
    extendedFrame = (float *) calloc(extendedFrameSize, sizeof(float));

    // Copy frame's each row into extendedFrame leaving (directional_distance_ pixel(s))
    // 	padding on each side
    int startPosn = extendedFrameColumns * directional_distance_ + directional_distance_;
    int endPosn   = extendedFrameSize - (extendedFrameColumns*directional_distance_);
    int increment = extendedFrameColumns;
    float *rowPtr = frame;

    // Copy input_frame to extendedFrame (with frame of 0's surrounding all four sides)
    for (int i = startPosn; i < endPosn; )
    {
      memcpy(&(extendedFrame[i]), rowPtr, number_columns_ * sizeof(float));
      rowPtr = rowPtr + number_columns_;
      i = i + increment;
    }

    //// CS example frame, with directional_distance_ = 1
    ///
    ///      0     1    2    3  ...   79   80   81
    ///     82    83   84   85  ...  161  162  163
    ///    164   165  166  167  ...  243  244  245
    ///     ..    ..  ..   ..         ..   ..   ..
    ///    6642 6643 6644 6645  ... 6721 6722 6723
    ///
    ///   Where frame's first row is 80 pixels from position 83 - 162,
    ///      second row is 165 - 244, etc

    endPosn = extendedFrameSize - (extendedFrameColumns * directional_distance_)
                - directional_distance_;
    process_addition(extendedFrame, extendedFrameColumns, startPosn, endPosn);

    /// Copy CS frame (i.e. 82x82) back into original (80x80) frame
    rowPtr = frame;
    for (int i = startPosn; i < endPosn; )
    {
      memcpy(rowPtr, &(extendedFrame[i]), number_columns_ * sizeof(float));
      rowPtr = rowPtr + number_columns_;
      i = i + increment;
    }

    free(extendedFrame);
    extendedFrame = NULL;
  }

  /**
   * Perform charged sharing algorithm
   *
   * \param[in] extended_frame - Pointer to the image data, surrounded by a frame of zeros
   * \param[in] extended_frame_columns - Number of columns in the extended frame
   * \param[in] start_position - The first pixel in the frame
   * \param[in] end_position - The final pixel in the frame
   */
  void HexitecAdditionPlugin::process_addition(float *extended_frame,
      int extended_frame_columns, int start_position, int end_position)
  {
    float *neighbourPixel = NULL, *currentPixel = extended_frame;
    float *maxPosition = NULL;
    int rowIndexBegin = (-1*directional_distance_);
    int rowIndexEnd   = (directional_distance_+1);
    int colIndexBegin = rowIndexBegin;
    int colIndexEnd   = rowIndexEnd;
    for (int i = start_position; i < end_position;  i++)
    {
      if (extended_frame[i] > 0)
      {
        currentPixel = (&(extended_frame[i]));
        maxPosition = (&(extended_frame[i]));
        for (int row = rowIndexBegin; row < rowIndexEnd; row++)
        {
          for (int column = colIndexBegin; column < colIndexEnd; column++)
          {
            if ((row == 0) && (column == 0)) // Don't compare pixel against itself
              continue;

            neighbourPixel = (currentPixel + (extended_frame_columns*row)  + column);
            if (*neighbourPixel > 0)
            {
              if (*neighbourPixel >= *maxPosition)
              {
                *neighbourPixel += *maxPosition;
                *maxPosition = 0;
                maxPosition = neighbourPixel;
              }
              else
              {
                *maxPosition += *neighbourPixel;
                *neighbourPixel = 0;
              }
            }
          }
        }
      }
    }
  }

  /**
   * Parse the number of sensors map configuration string.
   * 
   * This method parses a configuration string containing number of sensors mapping information,
   * which is expected to be of the format "NxN" e.g, 2x2. The map is saved in a member
   * variable.
   * 
   * \param[in] sensors_layout_str - string of number of sensors configured
   * \return number of valid map entries parsed from string
   */ 
  std::size_t HexitecAdditionPlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
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

    number_rows_    = image_height_;
    number_columns_ = image_width_;

    // Return the number of valid entries parsed
    return sensors_layout_.size();
  }

  // DEBUGGING FUNCTIONS:
  
  void  HexitecAdditionPlugin::print_nonzero_pixels(float *in, int numberRows, int numberCols)
  {
    LOG4CXX_TRACE(logger_, " +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
    float pixel = 0.0;
    int index  = -1;
    for (int row = 0; row < numberRows; row++ )
    {
      for (int col = 0; col < numberCols; col++ )
      {
        // /// Print the final 4 lines (so we can check 5x5 grid size)
        // if ((row > (numberRows-5)))
        // {
        index = numberRows*row + col;
        pixel = in[index];
        if (pixel > 0.0)
          LOG4CXX_TRACE(logger_, "" << &(in[index]) << " [" << index << "] I.e. ["
                                    << row << "][" << col << "] = " << pixel);
        // }
      }
    }
  }

  void  HexitecAdditionPlugin::print_last_row(float *in, int numberRows, int numberCols)
  {
    LOG4CXX_TRACE(logger_, " -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-");
    LOG4CXX_TRACE(logger_, "" << in << " &(in[0]) " << &in[0]);

    float pixel = 0.0;
    int index = -1;
    for (int row = 0; row < numberRows; row++ )
    {
      for (int col = 0; col < numberCols; col++ )
      {
        /// Print the final 4 lines (so we can check 5x5 grid size)
        if ((row > (numberRows-5)))
        {
          index = numberRows*row + col;
          pixel = in[index];
          if (pixel > 0.0)
            LOG4CXX_TRACE(logger_, "" << &(in[index]) << " [" << index << "] I.e. [" << row <<
                "][" << col << "] = " << pixel );
        }
        // Print final address
        if ((row == (numberRows-1)) && (col == (numberCols-1)))
        {
          index = numberRows*row + col;
          LOG4CXX_TRACE(logger_, "" << &(in[index]) << " [" << index << "] I.e. [" << row <<
              "][" << col << "] = " << pixel );
        }
      }
    }
  }

  void HexitecAdditionPlugin::check_memory(float *float_pointer, int offset)
  {
    LOG4CXX_TRACE(logger_, "\t\t ***\t\t :" << float_pointer << " runs until: "
        << (float_pointer+offset) << " diff: " << ((float_pointer+offset)-(float_pointer))
        << " last 3 values: " << *(float_pointer+offset-3) << "  " << *(float_pointer+offset-2)
        << "  " << *(float_pointer+offset-1));
  }

  /// Debug function: Takes a file prefix, frame and writes all nonzero pixels to file
  void HexitecAdditionPlugin::writeFile(std::string filePrefix, float *frame)
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

