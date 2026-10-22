#ifndef FRAMESIMULATOR_HEXITECFRAMESIMULATORPLUGIN_H
#define FRAMESIMULATOR_HEXITECFRAMESIMULATORPLUGIN_H

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
using namespace log4cxx;
using namespace log4cxx::helpers;

#include <boost/shared_ptr.hpp>
#include <boost/property_tree/ptree.hpp>
#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include <boost/property_tree/json_parser.hpp>
#include <boost/foreach.hpp>
#include <map>
#include <string>
#include <stdexcept>
#include <boost/algorithm/string.hpp>

#include "ClassLoader.h"
#include "FrameSimulatorPluginUDP.h"
#include "HexitecDefinitions.h"


namespace FrameSimulator {

    typedef std::map<int, Hexitec::HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

    /** HexitecFrameSimulatorPlugin
     *
     *  'extract_frames' is called on setup: this takes the content of the pcap file and reproduces the
     *  Hexitec frames to store
     *  'replay_frames' is called by simulate: this then replays the stored frames
     *  'create_frames' is called on setup if no pcap file is specified. It creates frames based on a
     *  frame pattern config provided
     */
    class HexitecFrameSimulatorPlugin : public FrameSimulatorPluginUDP {

    public:

        HexitecFrameSimulatorPlugin();

        virtual void populate_options(po::options_description& config);
        virtual bool setup(const po::variables_map& vm);

        virtual int get_version_major();
        virtual int get_version_minor();
        virtual int get_version_patch();
        virtual std::string get_version_short();
        virtual std::string get_version_long();

    protected:

        virtual void extract_frames(const u_char* data, const int& size);
        virtual void create_frames(const int &num_frames);

    private:

        /** Pointer to logger **/
        LoggerPtr logger_;

        int total_packets;
        int total_bytes;

        int current_frame_num;
        uint16_t* pixel_data_;
        int num_pixels_;
        unsigned int frames_loaded_;

        std::string image_pattern_json_path_;
        std::string hdf_file_path_;
        std::string hdf_dataset_;
        unsigned int hdf_frames_;

        bool load_image_pattern_json(const std::string& image_pattern_json_path);
        bool load_hdf_file(
            const std::string& hdf_file_path, const std::string& hdf_dataset,
            unsigned int hdf_frames=0
        );

        std::size_t parse_sensor_layout_map(const std::string sensor_layout_str);
        HexitecSensorLayoutMap sensor_layout_;
        std::string sensor_layout_str_;
        int image_width_;
        int image_height_;

        // sensor_config_ map number of sensors to frame and packet structures,
        // see HexitecDefinitions.h for more details
        bool set_sensor_config(int sensor_rows, int sensor_columns);
        Hexitec::SensorConfigNumber sensor_config_;
        void extract_normal_header(const u_char *data);
        void extract_extended_header(const u_char *data);
        bool extended_packet_header_;
        int packet_header_size_;
    };

    REGISTER(FrameSimulatorPlugin, HexitecFrameSimulatorPlugin, "HexitecFrameSimulatorPlugin");
}

#endif //FRAMESIMULATOR_HEXITECFRAMESIMULATORPLUGIN_H
