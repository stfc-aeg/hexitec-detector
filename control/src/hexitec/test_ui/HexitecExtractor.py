"""
Takes a pcapng file and extracts packets' payload.

Takes 2x2 sensors data, 8008/3208 packet sizes, and saves it to disk
as .h5 format.

Created on November 14, 2022

@author: Christian Angelsen
"""

from __future__ import print_function

import argparse
from scapy.all import PcapReader, UDP
import numpy as np
import h5py
import sys
import os


class HexitecExtractorError(Exception):
    """Customised exception class."""

    def __init__(self, msg):
        """Initialise."""
        self.msg = msg

    def __str__(self):
        """MagicMethod."""
        return repr(self.msg)


class HexitecExtractor(object):
    """Produce and transmit specified UDP frames."""

    def __init__(self, filename):
        """Initialise object with command line argument."""
        self.SOF = 1 << 63
        self.EOF = 1 << 62
        self.filename = filename
        self.filename_h5 = self.determine_h5_file(filename)
        self.HEADER_SIZE = 8

        if os.access(self.filename, os.R_OK):
            self.file_contents = self.decode_pcap()
            self.write_data_to_disc()
        else:
            print("Unable to open: {}. Does it exist?".format(self.filename))
            sys.exit(1)

    def determine_h5_file(self, file):
        """Determine .h5 filename from file."""
        extension = file.find(".pcapng")
        h5_file = file[:extension] + ".h5"
        return h5_file

    def decode_pcap(self):
        """Extract extended header-sized UDP data from file."""
        # Initialise frame list and counters
        frames = []
        num_packets = 0
        num_frames = 0

        # Create a PCAP reader instance
        packets = PcapReader(self.filename)
        frame_data = bytes()
        # Iterate through packets in reader
        for packet in packets:

            # Extract UDP packet payload
            payload = bytes(packet[UDP].payload)
            # Read frame header
            header = np.frombuffer(payload[:self.HEADER_SIZE], dtype=np.uint64)

            # If this is a start of frame packet, reset frame data
            if int(header[0]) & self.SOF:
                frame_data = bytes()

            # Append frame payload to frame data, without header
            frame_data += payload[self.HEADER_SIZE:]

            # If this is an end of frame packet, convert frame data to numpy array and append to frame list
            if int(header[0]) & self.EOF:
                frame = np.frombuffer(frame_data, dtype=np.uint16)
                frames.append(frame)
                num_frames += 1
            num_packets += 1

        # Convert frame list to 3D numpy array
        frames = np.array(frames)   # , dtype=object)

        print("Decoded {} frames from {} packets in PCAP file {}".format(num_frames, num_packets, self.filename))

        return frames

    def write_data_to_disc(self):
        """Write data to h5 file."""
        # print("Size: {} {}".format(len(self.file_contents), self.file_contents.shape))
        try:
            hdf_file = h5py.File(self.filename_h5, 'w')
        except IOError as e:
            print("ERROR: Couldn't open '{}' : {}".format(self.filename_h5, e))
            return
        dshape = self.file_contents.shape
        try:
            # dset = hdf_file.create_dataset("raw_frames", (10, 160, 160), '<u2')
            hdf_file.create_dataset("raw_frames", shape=(dshape[0], 160, 160), data=self.file_contents)
        except ValueError as e:
            print("Error Writing dataset to disk: {}".format(e))
        hdf_file.close()


if __name__ == '__main__':

    desc = "HexitecExtractor - Save pcapng file's UDP data to h5 file"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        'filename',
        default="hexitec_triangle_100G.pcapng",
        help='PCAPNG (Wireshark) file to load'
    )

    args = parser.parse_args()

    producer = HexitecExtractor(**vars(args))
