/*
 * HexitecDefinitions.h
 *
 *  Created on: Jul 11, 2018
 *      Author: Christian Angelsen, STFC Application Engineering Group
 */

#ifndef INCLUDE_HEXITECDEFINITIONS_H_
#define INCLUDE_HEXITECDEFINITIONS_H_

#define ILLEGAL_FEM_IDX -1

namespace Hexitec {

  static const size_t num_sensors = 3;
  typedef enum {
    sensorConfigUnknown = -1,
    sensorConfigOne = 0,			// 1 x 1 sensors
    sensorConfigTwo = 1,			// 2 x 2 sensors
    sensorConfigThree = 2			// 2 x 6 sensors
  } SensorConfigNumber;

  typedef struct HexitecSensorLayoutMapEntry
  {
    int sensor_rows_;
    int sensor_columns_;

    HexitecSensorLayoutMapEntry(int sensor_rows=ILLEGAL_FEM_IDX, int sensor_columns=ILLEGAL_FEM_IDX) :
      sensor_rows_(sensor_rows),
      sensor_columns_(sensor_columns)
    {};
  } HexitecSensorLayoutMapEntry;

  const std::string default_sensors_layout_map = "2x6";

  // A Hexitec sensor is 80x80 pixels large
  static const uint16_t pixel_columns_per_sensor = 80;
  static const uint16_t pixel_rows_per_sensor =  80;

  static const size_t primary_packet_size = 7680;
  static const size_t num_primary_packets[num_sensors] = {1, 6, 20};
  static const size_t max_primary_packets = 20;
  static const size_t tail_packet_size[num_sensors]	= {4800, 3200, 7680};
  static const size_t num_tail_packets 		= 0;

  static const uint32_t start_of_frame_mask = 1 << 31;
  static const uint32_t end_of_frame_mask   = 1 << 30;
  static const uint32_t packet_number_mask  = 0x3FFFFFFF;

  static const int32_t default_frame_number = -1;

  typedef struct
  {
    uint32_t frame_number;
    uint32_t packet_number_flags;
  } PacketHeader;

  typedef struct
  {
    uint64_t frame_number;
    uint32_t packet_number;
    uint32_t packet_flags;
  } PacketExtendedHeader;

  typedef struct
  {
    uint32_t packets_received;
    uint8_t  sof_marker_count;
    uint8_t  eof_marker_count;
    uint8_t  packet_state[max_primary_packets + num_tail_packets];
  } FemReceiveState;

  typedef struct
  {
    uint32_t frame_number;
    uint32_t frame_state;
    struct timespec frame_start_time;
    uint32_t total_packets_received;
    uint8_t total_sof_marker_count;
    uint8_t total_eof_marker_count;
    uint8_t active_fem_idx;
    FemReceiveState fem_rx_state;
  } FrameHeader;


  inline const std::size_t frame_size(const SensorConfigNumber sensor_config)
  {
    std::size_t frame_size = (primary_packet_size * num_primary_packets[sensor_config]) +
        (tail_packet_size[sensor_config] * num_tail_packets);
    return frame_size;
  }

  inline const std::size_t max_frame_size(const SensorConfigNumber sensor_config)
  {
    std::size_t max_frame_size = sizeof(FrameHeader) + frame_size(sensor_config);
    return max_frame_size;
  }

  inline const std::size_t num_fem_frame_packets(const SensorConfigNumber sensor_config)
  {
    std::size_t num_fem_frame_packets = (num_primary_packets[sensor_config] + num_tail_packets);
    return num_fem_frame_packets;
  }
}

#endif /* INCLUDE_HEXITECDEFINITIONS_H_ */
