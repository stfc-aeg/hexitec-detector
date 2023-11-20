"""
Takes a pcapng file and analysis packets' payload.

Will detect any packet loss(es), missing frame(s) by examining each packet's header.

Not a foolproof check, more detailed analysis available through Wireshark, either of:

> Statistics -> IO Graph
> Analyze -> Expert Info

Created on November 15, 2023

@author: Christian Angelsen
"""

from __future__ import print_function

import argparse
from scapy.all import PcapReader, UDP
import numpy as np
import datetime
import sys
import os


class HexitecAnalysis(object):
    """Read packet by packet from file and examine their headers."""

    def __init__(self, extended_headers, rows, columns, filename):
        """Initialise object with command line argument."""
        self.SOF = 1 << 63
        self.EOF = 1 << 62
        self.extended_headers = extended_headers
        self.NROWS = rows
        self.NCOLS = columns
        self.filename = filename
        if self.extended_headers:
            self.HEADER_SIZE = 16
        else:
            self.HEADER_SIZE = 8

        if os.access(self.filename, os.R_OK):
            print("Starting PCAP File Analysis", datetime.datetime.now())
            self.decode_pcap()
            print("Completed PCAP File Analysis", datetime.datetime.now())
        else:
            print("Unable to open: {}. Does it exist?".format(self.filename))
            sys.exit(1)

    def extract_packet_number(self, header):
        """Extract packet number from header."""
        packet_number = 0
        index = 0
        if self.extended_headers:
            index = 1
            packet_number = int(header[index]) & 0xFF
        return packet_number

    def count_lost_packets(self, previous_packet_number, current_packet_number):
        """Determine how many packets are missing between the two packet numbers."""
        if (current_packet_number < previous_packet_number):
            current_packet_number += 20
        # Ex: If packet 5 gone, previous_packet_number = 4, current_packet_number = 6 and
        # current_packet_number - previous_packet_number = 2 (but only 1 packet lost),
        # hence increase previous_packet_number by 1
        previous_packet_number += 1
        number_lost_packets = (current_packet_number - previous_packet_number)
        return number_lost_packets

    def decode_pcap(self):
        """Extract extended header-sized UDP data from file."""
        # Initialise frame list and counters
        num_packets = 0
        previous_packet_number = -1
        current_packet_number = 0
        previous_frame_number = -1
        current_frame_number = 0
        frame_interval = -1
        frame_counter = 0
        frame_number = -1
        check_frame_interval = False
        number_lost_packets = 0

        print(" Type  Current {0:6}/{1:6} Last {0:6}/{1:6}".format("Packet", "Frame"))

        # Create a PCAP reader instance
        packets = PcapReader(self.filename)

        # Iterate through packets in reader
        for packet in packets:

            # Extract UDP packet payload
            payload = bytes(packet[UDP].payload)
            # Read frame header
            header = np.frombuffer(payload[:self.HEADER_SIZE], dtype=np.uint64)
            current_packet_number = self.extract_packet_number(header)
            frame_number = int(header[0]) & 0xFFFFFFFF

            if (current_frame_number != frame_number):
                # New frame - Check interval between this and last frame number
                check_frame_interval = True
            current_frame_number = frame_number

            if previous_frame_number != -1 and (check_frame_interval):
                check_frame_interval = False
                difference = current_frame_number - previous_frame_number
                if frame_counter == 0:
                    # Comparing first and second frame, no previous interval available
                    frame_interval = difference
                else:
                    if difference != frame_interval:
                        print(" {0}           {1:6} {2:5}       {3:6} {4:5}  {5}".format("Frm",
                            "", current_frame_number, "", previous_frame_number,
                            "Gap: {0} != {1}.".format(difference, frame_interval)
                        ))

            # Packet number follow last packet numbers or it's a new frame?
            if (current_packet_number - 1) == previous_packet_number:
                pass
            elif (previous_packet_number == 19) and (current_packet_number == 0):
                pass
            else:
                print(" {0}           {1:6}/{2:5}       {3:6}/{4:5}".format("Pkt",
                    current_packet_number, current_frame_number,
                    previous_packet_number, previous_frame_number))
                number_lost_packets += self.count_lost_packets(previous_packet_number,
                                                               current_packet_number)

            if (previous_packet_number > current_packet_number):
                frame_counter += 1

            previous_packet_number = current_packet_number
            previous_frame_number = current_frame_number
            num_packets += 1

        print("Counted {} frames from {} packets in PCAP file {}".format(
             frame_counter+1, num_packets, self.filename))
        if number_lost_packets > 0:
            print(f"Found {number_lost_packets} missing packet")


if __name__ == '__main__':

    desc = "HexitecAnalysis - Examine pcapng file for missing packet(s), frame(s)"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--extended_headers', "-e", action="store_true",
                        help="Extended headers (16 bytes, or 8 bytes)")
    parser.add_argument('--rows', '-r', type=int, default=160,
                        help='set number of rows in frame')
    parser.add_argument('--columns', '-c', type=int, default=160,
                        help='set number of columns in frame')
    parser.add_argument(
        'filename',
        default="hexitec_triangle_100G.pcapng",
        help='PCAPNG (Wireshark or tcpdump) file to load'
    )

    args = parser.parse_args()

    producer = HexitecAnalysis(**vars(args))
