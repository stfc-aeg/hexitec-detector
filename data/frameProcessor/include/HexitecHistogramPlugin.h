/*
 * HexitecHistogramPlugin.h
 *
 *  Created on: 11 Jul 2018
 *      Author: Christian Angelsen
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
#include "DataBlockFrame.h"
//
#include <boost/algorithm/string.hpp>
#include <map>

namespace FrameProcessor
{
  typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

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
      /** Configuration constant for number of frame per acquisition **/
      static const std::string CONFIG_MAX_FRAMES;
      /** Configuration constant for bin start **/
      static const std::string CONFIG_BIN_START;
      /** Configuration constant for bin end **/
      static const std::string CONFIG_BIN_END;
      /** Configuration constant for bin width **/
      static const std::string CONFIG_BIN_WIDTH;
      /** Configuration constant for flush_histograms **/
      static const std::string CONFIG_FLUSH_HISTOS;
      /** Configuration constant for reset_histograms **/
      static const std::string CONFIG_RESET_HISTOS;
      /** Configuration constant for Hardware sensors **/
      static const std::string CONFIG_SENSORS_LAYOUT;
      /** Configuration constant for frames processed **/
      static const std::string CONFIG_FRAMES_PROCESSED;
      /** Configuration constant for histograms written **/
      static const std::string CONFIG_HISTOGRAMS_WRITTEN;
      /** Configuration constant for pass processed (dataset) **/
      static const std::string CONFIG_PASS_PROCESSED;

      std::size_t parse_sensors_layout_map(const std::string sensors_layout_str);
      std::string sensors_layout_str_;
      HexitecSensorLayoutMap sensors_layout_;

      void process_frame(boost::shared_ptr<Frame> frame);

      void add_frame_data_to_histogram_with_sum(float *frame);
      // function copied from HexitecGigE, but not currently in use:
      void addFrameDataToHistogram(float *frame);

      boost::shared_ptr<Frame> spectra_bins_;
      boost::shared_ptr<Frame> summed_spectra_;
      boost::shared_ptr<Frame> pixel_spectra_;

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
      /** Count number of frames processed **/
      int frames_processed_;
      /** Flush (remaining data to) histograms **/
      // bool flush_histograms_;
      int flush_histograms_;
      int reset_histograms_;
      int histograms_written_;
      bool pass_processed_;

      int bin_start_;
      int bin_end_;
      double bin_width_;
      long long number_bins_;
      void initialiseHistograms();
      void writeHistogramsToDisk();
      /// Debug only:
      int debugCounter;
  };

  /**
   * Registration of this plugin through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameProcessorPlugin, HexitecHistogramPlugin, "HexitecHistogramPlugin");

} /* namespace FrameProcessor */

#endif /* INCLUDE_HEXITECHISTOGRAMPLUGIN_H_ */
