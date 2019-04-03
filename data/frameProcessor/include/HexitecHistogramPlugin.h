/*
 * HexitecHistogramPlugin.h
 *
 *  Created on: 11 Jul 2018
 *      Author: ckd27546
 */

#ifndef INCLUDE_HEXITECHISTOGRAMPLUGIN_H_
#define INCLUDE_HEXITECHISTOGRAMPLUGIN_H_

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;


#include "FrameProcessorPlugin.h"
#include "HexitecDefinitions.h"
#include "ClassLoader.h"

namespace FrameProcessor
{

  /** Histogram for Hexitec Frame objects.
   *
   * The HexitecHistogramPlugin calculates histogram data from all processed frames
   * and periodically writes these histograms to disk.
   */
  class HexitecHistogramPlugin : public FrameProcessorPlugin
  {
  public:
    HexitecHistogramPlugin();
    virtual ~HexitecHistogramPlugin();

    int get_version_major();
    int get_version_minor();
    int get_version_patch();
    std::string get_version_short();
    std::string get_version_long();

    void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);
    void requestConfiguration(OdinData::IpcMessage& reply);
    void status(OdinData::IpcMessage& status);
    bool reset_statistics(void);

  private:
    /** Configuration constant for image width **/
    static const std::string CONFIG_IMAGE_WIDTH;
    /** Configuration constant for image height **/
    static const std::string CONFIG_IMAGE_HEIGHT;
    /** Configuration constant for number of frame per acquisition **/
    static const std::string CONFIG_MAX_FRAMES;
    /** Configuration constant for bin start **/
    static const std::string CONFIG_BIN_START;
    /** Configuration constant for bin end **/
    static const std::string CONFIG_BIN_END;
    /** Configuration constant for bin width **/
    static const std::string CONFIG_BIN_WIDTH;
    /** Configuration constant for maximum columns **/
    static const std::string CONFIG_MAX_COLS;
    /** Configuration constant for maximum rows **/
		static const std::string CONFIG_MAX_ROWS;
    /** Configuration constant for flush_histograms **/
		static const std::string CONFIG_FLUSH_HISTOS;

    void process_frame(boost::shared_ptr<Frame> frame);

    void add_frame_data_to_histogram_with_sum(float *frame);
    // function copied from HexitecGigE, but not currently in use:
    void addFrameDataToHistogram(float *frame);

    /** Pointer to logger **/
    LoggerPtr logger_;
    /** Image width **/
    int image_width_;
    /** Image height **/
    int image_height_;
    /** Image pixel count **/
    int image_pixels_;
    /** number of frames expected per acquisition **/
    int max_frames_received_;
    /** Count number of frames **/
    int frames_counter_;
    /** Flush (remaining data to) histograms **/
    bool flush_histograms_;

    int bin_start_;
    int bin_end_;
    double bin_width_;
    long long number_bins_;
    float *hexitec_bin_;
    float *histogram_per_pixel_;
    long long *summed_histogram_;
    void initialiseHistograms();
    void writeHistogramsToDisk();

    int fem_pixels_per_rows_;
    int fem_pixels_per_columns_;
    int fem_total_pixels_;

  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecHistogramPlugin, "HexitecHistogramPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECHISTOGRAMPLUGIN_H_ */
