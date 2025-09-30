/*
 * HexitecFrameDecoder.h
 *
 *  Created on: Jul 11, 2018
 *      Author: Christian Angelsen, STFC Application Engineering Group
 */

#ifndef INCLUDE_HEXITECFRAMEDECODER_H_
#define INCLUDE_HEXITECFRAMEDECODER_H_

#include "FrameDecoderUDP.h"
#include "HexitecDefinitions.h"
#include <iostream>
#include <map>
#include <stdint.h>
#include <time.h>

#define ILLEGAL_FEM_IDX -1

const std::string default_sensors_layout_map = Hexitec::default_sensors_layout_map;

namespace FrameReceiver
{
  typedef struct HexitecSensorLayoutMapEntry
  {
    unsigned int sensor_rows_;
    unsigned int sensor_columns_;

    HexitecSensorLayoutMapEntry(int sensor_rows=ILLEGAL_FEM_IDX, int sensor_columns=ILLEGAL_FEM_IDX) :
      sensor_rows_(sensor_rows),
      sensor_columns_(sensor_columns)
    {};
  } HexitecSensorLayoutMapEntry;

  typedef std::map<int, HexitecSensorLayoutMapEntry> HexitecSensorLayoutMap;

  class HexitecFrameDecoder : public FrameDecoderUDP
  {
  public:

    HexitecFrameDecoder();
    ~HexitecFrameDecoder();

    int get_version_major();
    int get_version_minor();
    int get_version_patch();
    std::string get_version_short();
    std::string get_version_long();

    void init(LoggerPtr& logger, OdinData::IpcMessage& config_msg);
    void request_configuration(const std::string param_prefix, OdinData::IpcMessage& config_reply);

    const size_t get_frame_buffer_size(void) const;
    const size_t get_frame_header_size(void) const;

    inline const bool requires_header_peek(void) const
    {
      return true;
    };

    const size_t get_packet_header_size(void) const;
    void process_packet_header (size_t bytes_received, int port,
        struct sockaddr_in* from_addr);

    void* get_next_payload_buffer(void) const;
    size_t get_next_payload_size(void) const;
    FrameDecoder::FrameReceiveState process_packet (size_t bytes_received,
    		int port, struct sockaddr_in* from_addr);

    void monitor_buffers(void);
    void get_status(const std::string param_prefix, OdinData::IpcMessage& status_msg);
    void reset_statistics(void);

    void* get_packet_header_buffer(void);

    uint64_t get_frame_number(void) const;
    uint32_t get_packet_number(void) const;
    bool get_start_of_frame_marker(void) const;
    bool get_end_of_frame_marker(void) const;

  private:

    void initialise_frame_header(Hexitec::FrameHeader* header_ptr);
    unsigned int elapsed_ms(struct timespec& start, struct timespec& end);
    void parse_sensors_layout_map(const std::string sensors_layout_str);

    Hexitec::SensorConfigNumber sensors_config_;
    boost::shared_ptr<void> current_packet_header_;
    boost::shared_ptr<void> dropped_frame_buffer_;
    std::string sensors_layout_str_;
    HexitecSensorLayoutMap sensors_layout_;
    bool extended_packet_header_;
    int packet_header_size_;

    int current_frame_seen_;
    int current_frame_buffer_id_;
    void* current_frame_buffer_;
    Hexitec::FrameHeader* current_frame_header_;

    bool dropping_frame_data_;
    uint32_t packets_lost_;
    uint32_t fem_packets_lost_;

    static const std::string CONFIG_SENSORS_LAYOUT;
    static const std::string CONFIG_EXTENDED_PACKET_HEADER;
  };

} // namespace FrameReceiver

#endif /* INCLUDE_HEXITECFRAMEDECODER_H_ */
