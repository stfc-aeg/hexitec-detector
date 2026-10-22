#include <string>

#include "HexitecFrameSimulatorPlugin.h"
#include "FrameSimulatorOptionsHexitec.h"

#include <cstdlib>
#include <time.h>
#include <iostream>
#include <algorithm>
#include <hdf5.h>

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
        // Set sensors_config_, image_width_, image_height_, image_pixels_
        sensor_layout_str_ = Hexitec::default_sensors_layout_map;
        parse_sensor_layout_map(sensor_layout_str_);
        extended_packet_header_ = true;
        if (extended_packet_header_)
            packet_header_size_ = sizeof(Hexitec::PacketExtendedHeader);
        else
            packet_header_size_ = sizeof(Hexitec::PacketHeader);
    }

    void HexitecFrameSimulatorPlugin::populate_options(po::options_description& config) {

        FrameSimulatorPluginUDP::populate_options(config);

        opt_image_pattern_json.add_option_to(config);
        opt_hdf_file_path.add_option_to(config);
        opt_hdf_dataset.add_option_to(config);
        opt_hdf_frames.add_option_to(config);
        opt_sensor_layout.add_option_to(config);
    }

    bool HexitecFrameSimulatorPlugin::setup(const po::variables_map& vm) {
        LOG4CXX_DEBUG(logger_, "Setting Up Hexitec Frame Simulator Plugin");

        // Extract sensor layout optional argument for this plugin
        boost::optional<std::string> detector_sensor_layout;

        opt_sensor_layout.get_val(vm, detector_sensor_layout);
        if (detector_sensor_layout)
        {
            sensor_layout_str_ = detector_sensor_layout.get();
            int parsed_sensors = parse_sensor_layout_map(sensor_layout_str_);
            if (parsed_sensors > 0)
            {
                LOG4CXX_DEBUG(logger_, "Sensor layout is: " << sensor_layout_str_ << " : "
                                        << image_height_ << " by " << image_width_ << " pixels");
            }
            else
            {
                LOG4CXX_ERROR(logger_, "Couldn't parse sensor layout from string: \"" << sensor_layout_str_ << "\"");
                return false;
            }
        }
        else
        {
            LOG4CXX_WARN(logger_, "No sensor_layout argument, defaulting to 80 x 80 pixels");
            // Set sensors_config_, image_width_, image_height_, image_pixels_
            parse_sensor_layout_map("1x1");
        }

        //Extract image pattern JSON and HDF file arguments for this plugin
        boost::optional<std::string> image_pattern_json;
        boost::optional<std::string> hdf_file_path;

        opt_image_pattern_json.get_val(vm, image_pattern_json);
        opt_hdf_file_path.get_val(vm, hdf_file_path);

        if (image_pattern_json && hdf_file_path)
        {
            LOG4CXX_ERROR(logger_, "Cannot specify both image pattern JSON and HDF file path");
            return false;
        }
        else if(image_pattern_json)
        {
            image_pattern_json_path_ = image_pattern_json.get();
            LOG4CXX_INFO(logger_, "Using image pattern from file: " << image_pattern_json_path_);

            if (!load_image_pattern_json(image_pattern_json_path_))
            {
                LOG4CXX_ERROR(logger_, "Failed to load image pattern JSON file: " << image_pattern_json_path_);
                return false;
            }

        }
        else if(hdf_file_path)
        {
            hdf_file_path_ = hdf_file_path.get();
            LOG4CXX_INFO(logger_, "Using HDF file: " << hdf_file_path_);

            boost::optional<std::string> hdf_dataset;
            opt_hdf_dataset.get_val(vm, hdf_dataset);
            if (hdf_dataset)
            {
                hdf_dataset_ = hdf_dataset.get();
                LOG4CXX_INFO(logger_, "Using HDF dataset: " << hdf_dataset_);
            }
            else
            {
                LOG4CXX_INFO(logger_, "No HDF dataset specified, defaulting to: " << FrameSimulator::default_hdf_dataset);
                hdf_dataset_ = FrameSimulator::default_hdf_dataset;
            }

            boost::optional<unsigned int> hdf_frames;
            opt_hdf_frames.get_val(vm, hdf_frames);
            if (hdf_frames)
            {
                LOG4CXX_INFO(logger_, "Reading maximum of " << hdf_frames.get() << " frames from HDF file");
                hdf_frames_ = hdf_frames.get();
            }
            else
            {
                LOG4CXX_INFO(logger_, "Reading all frames from HDF file");
                hdf_frames_ = 0;
            }

            if (!load_hdf_file(hdf_file_path_, hdf_dataset_, hdf_frames_))
            {
                LOG4CXX_ERROR(logger_, "Failed to load HDF file: " << hdf_file_path_ << " with dataset: " << hdf_dataset_);
                return false;
            }
        }
        else
        {
            LOG4CXX_ERROR(logger_, "No image pattern JSON or HDF file path specified");
            return false;
        }

        return FrameSimulatorPluginUDP::setup(vm);
    }

    bool HexitecFrameSimulatorPlugin::load_image_pattern_json(const std::string& image_pattern_json_path)
    {

        // Read the image pattern data from the JSON file
        boost::property_tree::ptree img_tree;
        boost::property_tree::json_parser::read_json(image_pattern_json_path, img_tree);

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
            LOG4CXX_ERROR(logger_, "Image pattern file size must match dimensions set by sensor_layout (" << sensor_layout_str_ << ")");
            return false;
        }
        // Check the correct number of values read from file
        if (x < num_pixels_)
        {
            LOG4CXX_ERROR(logger_, "Requires " << num_pixels_ << " pixels but image pattern file contains only " << x);
            return false;
        }

        // Only one frame is loaded from the image pattern JSON file
        frames_loaded_ = 1;

        return true;
    }

    bool HexitecFrameSimulatorPlugin::load_hdf_file(
        const std::string& hdf_file_path, const std::string& hdf_dataset, unsigned int hdf_frames)
    {
        // Open the HDF5 file
        hid_t file_id = H5Fopen(hdf_file_path.c_str(), H5F_ACC_RDONLY, H5P_DEFAULT);
        if (file_id < 0)
        {
            LOG4CXX_ERROR(logger_, "Failed to open HDF5 file: " << hdf_file_path);
            return false;
        }

        // Open the dataset
        hid_t dataset_id = H5Dopen(file_id, hdf_dataset.c_str(), H5P_DEFAULT);
        if (dataset_id < 0)
        {
            LOG4CXX_ERROR(logger_, "Failed to open dataset: " << hdf_dataset << " in HDF5 file: " << hdf_file_path);
            H5Fclose(file_id);
            return false;
        }

        // Get the dataspace and dimensions
        hid_t dataspace_id = H5Dget_space(dataset_id);
        int ndims = H5Sget_simple_extent_ndims(dataspace_id);
        if (ndims != 3)
        {
            LOG4CXX_ERROR(logger_, "Dataset must be 3-dimensional (frames, height, width)");
            H5Sclose(dataspace_id);
            H5Dclose(dataset_id);
            H5Fclose(file_id);
            return false;
        }

        hsize_t dims[3];
        H5Sget_simple_extent_dims(dataspace_id, dims, NULL);
        unsigned int ds_frames = static_cast<unsigned int>(dims[0]);
        unsigned int ds_height = static_cast<unsigned int>(dims[1]);
        unsigned int ds_width = static_cast<unsigned int>(dims[2]);

        LOG4CXX_DEBUG(logger_, "Dataset dimensions: " << ds_frames << " frames, " << ds_height << " height, " << ds_width << " width");

        if (ds_height != image_height_ || ds_width != image_width_)
        {
            LOG4CXX_ERROR(logger_, "Dataset dimensions (" << ds_height << "x" << ds_width << ") do not match expected dimensions (" << image_height_ << "x" << image_width_ << ")");
            H5Sclose(dataspace_id);
            H5Dclose(dataset_id);
            H5Fclose(file_id);
            return false;
        }

        unsigned int num_frames = ds_frames;
        if (hdf_frames > 0)
        {
            num_frames = std::min(ds_frames, hdf_frames);
        }
        LOG4CXX_INFO(logger_, "Reading " << num_frames << " frames from HDF5 dataset: " << hdf_dataset);

        // Allocate memory for pixel data
        pixel_data_ = new uint16_t[num_pixels_ * num_frames];

        // Select num_frames frames from the dataset with a hyperslab
        hsize_t start[3] = {0, 0, 0};
        hsize_t count[3] = {num_frames, ds_height, ds_width};
        if (H5Sselect_hyperslab(dataspace_id, H5S_SELECT_SET, start, nullptr, count, nullptr) < 0)
        {
            LOG4CXX_ERROR(logger_, "Failed to select hyperslab for dataset: " << hdf_dataset);
            delete[] pixel_data_;
            pixel_data_ = nullptr;
            H5Sclose(dataspace_id);
            H5Dclose(dataset_id);
            H5Fclose(file_id);
            return false;
        }

        // Create a memory dataspace for the selected frames
        hsize_t mem_dims[3] = {num_frames, ds_height, ds_width};
        hid_t memspace_id = H5Screate_simple(3, mem_dims, nullptr);
        if (memspace_id < 0)
        {
            LOG4CXX_ERROR(logger_, "Failed to create memory dataspace for dataset: " << hdf_dataset);
            delete[] pixel_data_;
            pixel_data_ = nullptr;
            H5Sclose(dataspace_id);
            H5Dclose(dataset_id);
            H5Fclose(file_id);
            return false;
        }

        // Read num_frames frames of data from the dataset into pixel_data_
        herr_t status = H5Dread(dataset_id, H5T_NATIVE_UINT16, memspace_id, dataspace_id, H5P_DEFAULT, pixel_data_);
        if (status < 0)
        {
            LOG4CXX_ERROR(logger_, "Failed to read dataset: " << hdf_dataset << " from HDF5 file: " << hdf_file_path);
            delete[] pixel_data_;
            pixel_data_ = nullptr;
            H5Sclose(dataspace_id);
            H5Dclose(dataset_id);
            H5Fclose(file_id);
            return false;
        }

        // Set the number of frames loaded
        frames_loaded_ = num_frames;

        // Clean up
        H5Sclose(dataspace_id);
        H5Dclose(dataset_id);
        H5Fclose(file_id);

        return true;
    }

    /** Extracts the frames from the pcap data file buffer
     * \param[in] data - pcap data
     * \param[in] size
     */
    void HexitecFrameSimulatorPlugin::extract_frames(const u_char *data, const int &size) {

        LOG4CXX_DEBUG(logger_, "Extracting Frame(s) from packet");
        // Get first 8 or 64 (extended header) bytes, turn into header
        // check header flags
        if (extended_packet_header_)
            extract_extended_header(data);
        else
            extract_normal_header(data);

        // Create new packet, copy packet data and push into frame
        boost::shared_ptr<Packet> pkt(new Packet());
        unsigned char *datacp = new unsigned char[size];
        memcpy(datacp, data, size);
        pkt->data = datacp;
        pkt->size = size;
        frames_[frames_.size() - 1].packets.push_back(pkt);

        total_packets++;
    }

    void HexitecFrameSimulatorPlugin::extract_normal_header(const u_char *data) {

        const Hexitec::PacketHeader* packet_hdr = reinterpret_cast<const Hexitec::PacketHeader*>(data);

        uint32_t frame_number = packet_hdr->frame_number;
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

    void HexitecFrameSimulatorPlugin::extract_extended_header(const u_char *data) {

        const Hexitec::PacketExtendedHeader* packet_hdr = reinterpret_cast<const Hexitec::PacketExtendedHeader*>(data);

        uint64_t frame_number = packet_hdr->frame_number;
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

        // Loop over specified number of frames to generate packet and frame data
        for (int frame = 0; frame < num_frames; frame++) {

            std::size_t frame_offset = (frame % frames_loaded_) * image_bytes;
            u_char* data_ptr = reinterpret_cast<u_char*>(pixel_data_) + frame_offset;

            uint32_t packet_number = 0;
            uint32_t packet_flags = 0;
            for (int i=0; i < (Hexitec::num_primary_packets[sensor_config_]-1); i++)
            {
                // Setup Head Packet Header
                if (extended_packet_header_)
                {
                    Hexitec::PacketExtendedHeader* head_packet_header =
                        reinterpret_cast<Hexitec::PacketExtendedHeader*>(head_packet_data);

                    packet_flags = 0;
                    // Add SoF if this is the first packet of the frame
                    if (packet_number == 0)
                        packet_flags = packet_flags | Hexitec::start_of_frame_mask;

                    head_packet_header->frame_number = frame;
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

                    head_packet_header->frame_number = frame;
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
            if (extended_packet_header_)
            {
                Hexitec::PacketExtendedHeader* tail_packet_header =
                    reinterpret_cast<Hexitec::PacketExtendedHeader*>(head_packet_data);
                packet_flags = Hexitec::end_of_frame_mask;
                tail_packet_header->frame_number = frame;
                tail_packet_header->packet_number = packet_number;
                tail_packet_header->packet_flags = packet_flags;
            }
            else
            {
                Hexitec::PacketHeader* tail_packet_header =
                    reinterpret_cast<Hexitec::PacketHeader*>(head_packet_data);
                packet_flags =
                    (packet_number & Hexitec::packet_number_mask) | Hexitec::end_of_frame_mask;
                tail_packet_header->frame_number = frame;
                tail_packet_header->packet_number_flags = packet_flags;
            }

            // Copy data into Head Packet
            memcpy((head_packet_data + packet_header_size_), data_ptr, Hexitec::tail_packet_size[sensor_config_]);

            // Pass head packet to Frame Extraction
            this->extract_frames(head_packet_data, Hexitec::tail_packet_size[sensor_config_] + packet_header_size_);
        }

        delete [] head_packet_data;
        delete [] pixel_data_;
    }

    /** Parse the number of sensors map configuration string.
     *
     * This method parses a configuration string containing number of sensors mapping information,
     * which is expected to be of the format "NxM" e.g, 2x2. The map is saved in a member
     * variable.
     *
     * \param[in] sensor_layout_str - string of number of sensors configured
     * \return number of valid map entries parsed from string
     */
    std::size_t HexitecFrameSimulatorPlugin::parse_sensor_layout_map(const std::string sensor_layout_str)
    {
        // Clear the current map
        sensor_layout_.clear();

        // Define entry and port:idx delimiters
        const std::string entry_delimiter("x");

        // Vector to hold entries split from map
        std::vector<std::string> map_entries;

        // Split into entries
        boost::split(map_entries, sensor_layout_str, boost::is_any_of(entry_delimiter));

        // If a valid entry is found, save into the map
        if (map_entries.size() == 2)
        {
            int sensor_rows = static_cast<int>(strtol(map_entries[0].c_str(), NULL, 10));
            int sensor_columns = static_cast<int>(strtol(map_entries[1].c_str(), NULL, 10));

            if ((sensor_rows > 0) && (sensor_columns > 0))
            {
                sensor_layout_[0] = Hexitec::HexitecSensorLayoutMapEntry(sensor_rows, sensor_columns);
                image_width_ = sensor_layout_[0].sensor_columns_ * Hexitec::pixel_columns_per_sensor;
                image_height_ = sensor_layout_[0].sensor_rows_ * Hexitec::pixel_rows_per_sensor;
                num_pixels_ = image_width_ * image_height_;
                // Successfully parsed, update sensors_config too
                set_sensor_config(sensor_layout_[0].sensor_rows_, sensor_layout_[0].sensor_columns_);
            }
            else
            {
                LOG4CXX_ERROR(logger_, "Couldn't parse sensor_layout argument");
            }
        }

        // Return the number of valid entries parsed
        return sensor_layout_.size();
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
    bool HexitecFrameSimulatorPlugin::set_sensor_config(int sensor_rows, int sensor_columns) {

        bool parseOK = false;

        if ((sensor_rows == 1) && (sensor_columns == 1))
        {
            // Single sensor, i.e. 1x1
            sensor_config_ = Hexitec::sensorConfigOne;
            parseOK = true;
        }
        if (sensor_rows == 2)
        {
            if (sensor_columns == 2)
            {
                // 2x2
                sensor_config_ = Hexitec::sensorConfigTwo;
                parseOK = true;
            }
            else if (sensor_columns == 6)
            {
                // 2x6
                sensor_config_ = Hexitec::sensorConfigThree;
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
