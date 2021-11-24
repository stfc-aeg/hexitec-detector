#include <string>

#include "HexitecFrameSimulatorPlugin.h"
#include "FrameSimulatorOptionsHexitec.h"

#include <cstdlib>
#include <time.h>
#include <iostream>
#include <algorithm>
#include <boost/lexical_cast.hpp>

#include "version.h"

namespace FrameSimulator {


    /** Construct a HexitecFrameSimulatorPlugin
    * setup an instance of the logger
    * initialises data and frame counts
    */
    HexitecFrameSimulatorPlugin::HexitecFrameSimulatorPlugin() : FrameSimulatorPluginUDP() {
        //Setup logging for the class
        logger_ = Logger::getLogger("FS.HexitecFrameSimulatorPlugin");
        logger_->setLevel(Level::getAll());

        total_packets = 0;
        total_bytes = 0;
        current_frame_num = -1;
        // Setup default rows, columns values and sensors config
        image_width_ = Hexitec::pixel_columns_per_sensor;
        image_height_ = Hexitec::pixel_rows_per_sensor;
        sensors_layout_str_ = "2x2";
        sensors_config_ = Hexitec::sensorConfigTwo;
        packet_header_extended_ = true;
        if (packet_header_extended_)
            packet_header_size_ = sizeof(Hexitec::PacketExtendedHeader);
        else
            packet_header_size_ = sizeof(Hexitec::PacketHeader);
    }

    void HexitecFrameSimulatorPlugin::populate_options(po::options_description& config) {
        
        FrameSimulatorPluginUDP::populate_options(config);

        opt_image_pattern_json.add_option_to(config);
        opt_sensors_layout.add_option_to(config);
    }

    bool HexitecFrameSimulatorPlugin::setup(const po::variables_map& vm) {
        LOG4CXX_DEBUG(logger_, "Setting Up Hexitec Frame Simulator Plugin");

        // Extract optional argument for this plugin
        boost::optional<std::string> detector_sensors_layout;

        opt_sensors_layout.get_val(vm, detector_sensors_layout);
        if (detector_sensors_layout)
        {
            sensors_layout_str_ = detector_sensors_layout.get();
            int parsed_sensors = parse_sensors_layout_map(sensors_layout_str_);
            if (parsed_sensors > 0)
            {
                LOG4CXX_TRACE(logger_, "Parsed sensors_layout: " << sensors_layout_str_ << " into " 
                                        << image_height_ << " by " << image_width_ << " pixels");
            }
            else
            {
                LOG4CXX_ERROR(logger_, "Couldn't parse sensors from string: \"" << sensors_layout_str_ << "\"");
                return false;
            }
        }
        else
        {
            LOG4CXX_WARN(logger_, "No sensors_layout argument, defaulting to 80 x 80 pixels");
            image_width_ = Hexitec::pixel_columns_per_sensor;
            image_height_ = Hexitec::pixel_rows_per_sensor;
        }

        //Extract Optional arguments for this plugin
        boost::optional<std::string> image_pattern_json;

        opt_image_pattern_json.get_val(vm, image_pattern_json);
        if(image_pattern_json) {
            image_pattern_json_path_ = image_pattern_json.get();
        }

        LOG4CXX_DEBUG(logger_, "Using Image Pattern from file: " << image_pattern_json_path_);

        // Actually read out the data from the image file
        boost::property_tree::ptree img_tree;
        boost::property_tree::json_parser::read_json(image_pattern_json_path_, img_tree);

        num_pixels_ = image_width_ * image_height_;
        pixel_data_ = new uint16_t[num_pixels_];
        int x = 0;
        try
        {
            BOOST_FOREACH(boost::property_tree::ptree::value_type &row, img_tree.get_child("img"))
            {
                BOOST_FOREACH(boost::property_tree::ptree::value_type &cell, row.second)
                {
                    // Don't write beyond allocated memory:
                    if (x == num_pixels_)
                        throw std::exception();
                    pixel_data_[x] = cell.second.get_value<uint16_t>();
                    x++;
                }
            }
        }
        catch (std::exception& e)
        {
            LOG4CXX_WARN(logger_, "Set to use " << image_width_ << " by " << image_height_ << " pixels but file contains >" << num_pixels_ << "!");
            LOG4CXX_ERROR(logger_, "Image Pattern file size must match dimensions set by sensors_layout (" << sensors_layout_str_ << ")");
            return false;
        }
        // Check the correct number of values read from file
        if (x < num_pixels_)
        {
            LOG4CXX_ERROR(logger_, "Requires " << num_pixels_ << " pixels but Image Pattern file contains only " << x);
            return false;
        }

        return FrameSimulatorPluginUDP::setup(vm);
    }

    /** Extracts the frames from the pcap data file buffer
     * \param[in] data - pcap data
     * \param[in] size
     */
    void HexitecFrameSimulatorPlugin::extract_frames(const u_char *data, const int &size) {

        LOG4CXX_DEBUG(logger_, "Extracting Frame(s) from packet");
        // Get first 8 or 16 (extended header) bytes, turn into header
        // check header flags
        if (packet_header_extended_)
            extract_64b_header(data);
        else
            extract_32b_header(data);

        // Create new packet, copy packet data and push into frame
        boost::shared_ptr<Packet> pkt(new Packet());
        unsigned char *datacp = new unsigned char[size];
        memcpy(datacp, data, size);
        pkt->data = datacp;
        pkt->size = size;
        frames_[frames_.size() - 1].packets.push_back(pkt);

        total_packets++;
    }

    void HexitecFrameSimulatorPlugin::extract_32b_header(const u_char *data) {

        const Hexitec::PacketHeader* packet_hdr = reinterpret_cast<const Hexitec::PacketHeader*>(data);

        uint32_t frame_number = packet_hdr->frame_counter;
        uint32_t packet_number_flags = packet_hdr->packet_number_flags;

        bool is_SOF = packet_number_flags & Hexitec::start_of_frame_mask;
        bool is_EOF = packet_number_flags & Hexitec::end_of_frame_mask;
        uint32_t packet_number = packet_number_flags & Hexitec::packet_number_mask;

        if(is_SOF) {
            LOG4CXX_DEBUG(logger_, "SOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            if(packet_number != 0) {
                LOG4CXX_WARN(logger_, "Detected SOF marker on packet !=0");
            }

            // It's a new frame, so we create a new frame and add it to the list
            UDPFrame frame(frame_number);
            frames_.push_back(frame);
            frames_[frames_.size() - 1].SOF_markers.push_back(frame_number);
        }

        if(is_EOF) {
            LOG4CXX_DEBUG(logger_, "EOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            frames_[frames_.size() - 1].EOF_markers.push_back(frame_number);
        }
    }

    void HexitecFrameSimulatorPlugin::extract_64b_header(const u_char *data) {

        const Hexitec::PacketExtendedHeader* packet_hdr = reinterpret_cast<const Hexitec::PacketExtendedHeader*>(data);

        uint64_t frame_number = packet_hdr->frame_counter;
        uint32_t packet_flags = packet_hdr->packet_flags;
        uint32_t packet_number = packet_hdr->packet_number & Hexitec::packet_number_mask;

        bool is_SOF = packet_flags & Hexitec::start_of_frame_mask;
        bool is_EOF = packet_flags & Hexitec::end_of_frame_mask;

        if(is_SOF) {
            LOG4CXX_DEBUG(logger_, "SOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            if(packet_number != 0) {
                LOG4CXX_WARN(logger_, "Detected SOF marker on packet !=0");
            }

            // It's a new frame, so we create a new frame and add it to the list
            UDPFrame frame(frame_number);
            frames_.push_back(frame);
            frames_[frames_.size() - 1].SOF_markers.push_back(frame_number);
        }

        if(is_EOF) {
            LOG4CXX_DEBUG(logger_, "EOF Marker for Frame " << frame_number << " at packet "
                << packet_number << " total " << total_packets);

            frames_[frames_.size() - 1].EOF_markers.push_back(frame_number);
        }
    }

    /** Creates a number of frames
     *
     * @param num_frames - number of frames to create
     */
    void HexitecFrameSimulatorPlugin::create_frames(const int &num_frames) {
        LOG4CXX_DEBUG(logger_, "Creating Frames");

        // Calculate number of pixel image bytes in frame
        std::size_t image_bytes = num_pixels_ * sizeof(uint16_t);

        // Allocate buffer for packet data including header
        u_char* head_packet_data = new u_char[Hexitec::primary_packet_size + packet_header_size_];
        u_char* tail_packet_data = new u_char[Hexitec::tail_packet_size[sensors_config_] + packet_header_size_];
        
        // Loop over specified number of frames to generate packet and frame data
        for (int frame = 0; frame < num_frames; frame++) {
            
            u_char* data_ptr = reinterpret_cast<u_char*>(pixel_data_);

            uint32_t packet_number = 0;
            uint32_t packet_flags = 0;
            for (int i=0; i < Hexitec::num_primary_packets[sensors_config_]; i++)
            {
                // Setup Head Packet Header
                if (packet_header_extended_)
                {
                    Hexitec::PacketExtendedHeader* head_packet_header =
                        reinterpret_cast<Hexitec::PacketExtendedHeader*>(head_packet_data);

                    packet_flags = 0;
                    // Add SoF if this is the first packet of the frame
                    if (packet_number == 0)
                        packet_flags = packet_flags | Hexitec::start_of_frame_mask;

                    head_packet_header->frame_counter = frame;
                    head_packet_header->packet_number = packet_number;
                    head_packet_header->packet_flags = packet_flags;
                }
                else
                {
                    Hexitec::PacketHeader* head_packet_header =
                        reinterpret_cast<Hexitec::PacketHeader*>(head_packet_data);

                    packet_flags = (packet_number & Hexitec::packet_number_mask);
                    // Add SoF if this is the first packet of the frame
                    if (packet_number == 0)
                        packet_flags = packet_flags | Hexitec::start_of_frame_mask;

                    head_packet_header->frame_counter = frame;
                    head_packet_header->packet_number_flags = packet_flags;
                }
                
                // Copy data into packet
                memcpy((head_packet_data + packet_header_size_), data_ptr, Hexitec::primary_packet_size);

                // Pass packet to Frame Extraction
                this->extract_frames(head_packet_data, Hexitec::primary_packet_size + packet_header_size_);

                // Increment packet number and data_ptr
                packet_number += 1;
                data_ptr += Hexitec::primary_packet_size;
            }
            // Repeat for the Tail Packet Header and Data
            if (packet_header_extended_)
            {
                Hexitec::PacketExtendedHeader* tail_packet_header = 
                    reinterpret_cast<Hexitec::PacketExtendedHeader*>(tail_packet_data);
                packet_flags = Hexitec::end_of_frame_mask;
                tail_packet_header->frame_counter = frame;
                tail_packet_header->packet_number = packet_number;
                tail_packet_header->packet_flags = packet_flags;
            }
            else
            {
                Hexitec::PacketHeader* tail_packet_header = 
                    reinterpret_cast<Hexitec::PacketHeader*>(tail_packet_data);
                packet_flags =
                    (packet_number & Hexitec::packet_number_mask) | Hexitec::end_of_frame_mask;
                tail_packet_header->frame_counter = frame;
                tail_packet_header->packet_number_flags = packet_flags;
            }
            // packet_flags = packet_flags | Hexitec::end_of_frame_mask;

            // Copy data into Head Packet
            memcpy((tail_packet_data + packet_header_size_), data_ptr, Hexitec::tail_packet_size[sensors_config_]);

            // Pass head packet to Frame Extraction
            this->extract_frames(tail_packet_data, Hexitec::tail_packet_size[sensors_config_] + packet_header_size_);
        }

        delete [] head_packet_data;
        delete [] tail_packet_data;
        delete [] pixel_data_;

    }

    /** Parse the number of sensors map configuration string.
     * 
     * This method parses a configuration string containing number of sensors mapping information,
     * which is expected to be of the format "NxM" e.g, 2x2. The map is saved in a member
     * variable.
     * 
     * \param[in] sensors_layout_str - string of number of sensors configured
     * \return number of valid map entries parsed from string
     */
    std::size_t HexitecFrameSimulatorPlugin::parse_sensors_layout_map(const std::string sensors_layout_str)
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
        if (map_entries.size() == 2)
        {
            int sensor_rows = static_cast<int>(strtol(map_entries[0].c_str(), NULL, 10));
            int sensor_columns = static_cast<int>(strtol(map_entries[1].c_str(), NULL, 10));

            if ((sensor_rows > 0) && (sensor_columns > 0))
            {
                sensors_layout_[0] = Hexitec::HexitecSensorLayoutMapEntry(sensor_rows, sensor_columns);
                image_width_ = sensors_layout_[0].sensor_columns_ * Hexitec::pixel_columns_per_sensor;
                image_height_ = sensors_layout_[0].sensor_rows_ * Hexitec::pixel_rows_per_sensor;
                // Successfully parsed, update sensors_config too
                set_sensors_config(sensors_layout_[0].sensor_rows_, sensors_layout_[0].sensor_columns_);
            }
            else
            {
                LOG4CXX_ERROR(logger_, "Couldn't parse sensors_layout argument");
            }
        }

        // Return the number of valid entries parsed
        return sensors_layout_.size();
    }

    /** Match the number of sensors to a corresponding SensorConfigNumber.
     * 
     * This method compares the number of sensors against the known detector configurations.
     * Assuming it's a valid selection, the matching Hexitec::SensorConfigNumber value is
     * assigned to the sensors_config_ member variable.
     * 
     * \param[in] sensor_rows - number of sensors in the vertical plane
     * \param[in] sensor_columns - number of sensors in the horizontal plane
     * \return whether elections matches a known configuration
     */
    bool HexitecFrameSimulatorPlugin::set_sensors_config(int sensor_rows, int sensor_columns) {

        bool parseOK = false;
        
        if ((sensor_rows == 1) && (sensor_columns == 1))
        {
            // Single sensor, i.e. 1x1
            sensors_config_ = Hexitec::sensorConfigOne;
            parseOK = true;
        }
        if (sensor_rows == 2)
        {
            if (sensor_columns == 2)
            {
                // 2x2
                sensors_config_ = Hexitec::sensorConfigTwo;
                parseOK = true;
            }
            else if (sensor_columns == 6)
            {
                // 2x6
                sensors_config_ = Hexitec::sensorConfigThree;
                parseOK = true;
            }
        }

        return parseOK;
    }

    /**
     * Get the plugin major version number.
     *
     * \return major version number as an integer
     */
    int HexitecFrameSimulatorPlugin::get_version_major() {
        return ODIN_DATA_VERSION_MAJOR;
    }

    /**
     * Get the plugin minor version number.
     *
     * \return minor version number as an integer
     */
    int HexitecFrameSimulatorPlugin::get_version_minor() {
        return ODIN_DATA_VERSION_MINOR;
    }

    /**
     * Get the plugin patch version number.
     *
     * \return patch version number as an integer
     */
    int HexitecFrameSimulatorPlugin::get_version_patch() {
        return ODIN_DATA_VERSION_PATCH;
    }

    /**
     * Get the plugin short version (e.g. x.y.z) string.
     *
     * \return short version as a string
     */
    std::string HexitecFrameSimulatorPlugin::get_version_short() {
        return ODIN_DATA_VERSION_STR_SHORT;
    }

    /**
     * Get the plugin long version (e.g. x.y.z-qualifier) string.
     *
     * \return long version as a string
     */
    std::string HexitecFrameSimulatorPlugin::get_version_long() {
        return ODIN_DATA_VERSION_STR;
    }

}
