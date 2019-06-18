/*
 * HexitecDefinitions.h
 *
 *  Created on: Jul 11, 2018
 *      Author: Christian Angelsen, STFC Application Engineering Group
 */

#ifndef INCLUDE_HEXITECDEFINITIONS_H_
#define INCLUDE_HEXITECDEFINITIONS_H_

namespace Hexitec {

		static const size_t num_sensors = 2;
		typedef enum {
			sensorConfigUnknown = -1,
			sensorConfigOne = 0,			// 1 x 1 sensors
			sensorConfigTwo = 1				// 2 x 2 sensors
		} SensorConfigNumber;

    static const size_t primary_packet_size = 8000;
    static const size_t num_primary_packets[num_sensors] = {1, 6};
    static const size_t max_primary_packets = 6;
    static const size_t tail_packet_size[num_sensors]	= {4800, 3200};
    static const size_t num_tail_packets 		= 1;

    static const uint32_t start_of_frame_mask = 1 << 31;
    static const uint32_t end_of_frame_mask   = 1 << 30;
    static const uint32_t packet_number_mask  = 0x3FFFFFFF;

    static const int32_t default_frame_number = -1;

    typedef struct
    {
    	uint32_t frame_counter;
    	uint32_t packet_number_flags;
    } PacketHeader;

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
