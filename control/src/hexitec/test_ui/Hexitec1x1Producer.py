"""
Takes a pcap file and transmits specified number of frames.

Supports 1x1 sensors, 7744/5184 packet sizes, extracts headers from PCAPNG file.

Created on Nov 08, 2021

@author: Christian Angelsen
"""

from __future__ import print_function

import argparse
from scapy.all import PcapReader, UDP
import numpy as np
import socket
import time
import sys
import os


class HexitecUdpProducerError(Exception):
    """Customised exception class."""

    def __init__(self, msg):
        """Initialise."""
        self.msg = msg

    def __str__(self):
        """MagicMethod."""
        return repr(self.msg)


class HexitecUdpProducerDefaults(object):
    """Holds default values for frame producer parameters."""

    def __init__(self):
        """Initialise defaults."""
        self.ip_addr = 'localhost'
        self.num_frames = 0
        self.tx_interval = 0
        self.drop_frac = 0
        self.drop_list = None

        self.filename = 'hexitec_triangle_100G.pcapng'


class HexitecUdpProducer(object):
    """Produce and transmit specified UDP frames."""

    def __init__(self, host, port, frames,
                 interval, quiet, filename):
        """Initialise object with command line arguments."""
        self.SOF = 1 << 63
        self.EOF = 1 << 62
        self.host = host
        self.port = port
        self.frames = frames
        self.NROWS = 80
        self.NCOLS = 80
        self.NPIXELS = self.NROWS * self.NCOLS
        self.interval = interval
        self.quiet = quiet
        self.filename = filename

        bytesPerPixel = 2
        bytesToRead = self.NPIXELS * bytesPerPixel

        # Workout number of primary packets, size of trailing packet

        totalFrameSize = self.NPIXELS * bytesPerPixel
        self.primaryPackets = totalFrameSize // 7680
        self.trailingPacketSize = totalFrameSize % 7680
        # print("primary: {} trailingPacketSize: {}.".format(self.primaryPackets, self.trailingPacketSize))

        if os.access(self.filename, os.R_OK):
            print("Selected", self.frames, "frames, ", bytesToRead, "bytes.")
            file_contents = self.decode_pcap()
            self.byteStream = file_contents.tobytes()
        else:
            print("Unable to open: {}. Does it exist?".format(self.filename))
            sys.exit(1)

    def decode_pcap(self):
        """Extract extended header-sized UDP data from file."""
        HEADER_SIZE = 64

        # Initialise frame list and counters
        frames = []
        num_packets = 0
        num_frames = 0

        # Create a PCAP reader instance
        packets = PcapReader(self.filename)

        # Iterate through packets in reader
        for packet in packets:
            num_packets += 1

            # Extract UDP packet payload
            payload = bytes(packet[UDP].payload)

            # Read frame header
            header = np.frombuffer(payload[:HEADER_SIZE], dtype=np.uint64)
            # print([hex(val) for val in header])
            # assert header[0] == num_frames    # Assumes PCAPNG file begins from frame 0

            # If this is a start of frame packet, reset frame data
            if int(header[1]) & self.SOF:
                frame_data = bytes()

            # # Packet flags extracted from data:
            # SoF = int(header[1]) & self.SOF
            # EoF = int(header[1]) & self.EOF
            # print(len(payload), len(payload[HEADER_SIZE:]), SoF, EoF)

            # Append frame payload to frame data, including header
            frame_data += payload

            # If this is an end of frame packet, convert frame data to numpy array and append to frame list
            if int(header[1]) & self.EOF:
                frame = np.frombuffer(frame_data, dtype=np.uint16)
                # assert frame.size == self.NPIXELS
                frames.append(frame)
                num_frames += 1

        # Convert frame list to 3D numpy array
        frames = np.array(frames)

        print("Decoded {} frames from {} packets in PCAP file {}".format(num_frames, num_packets, self.filename))

        return frames

    def run(self):
        """Transmit data to address, port."""
        HEADER_SIZE = 64
        print("Transmitting Hexitec data to address {} port {} ...".format(self.host, self.port))

        # Open UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Create packet header
        # header = np.zeros(8, dtype=np.uint64)

        self.framesSent = 0
        self.packetsSent = 0
        self.totalBytesSent = 0

        streamPosn = 0

        runStartTime = time.time()

        bytesRemaining = len(self.byteStream)
        # Loop over selected number of frame(s)
        for frame in range(self.frames):

            packetCounter = 0
            bytesSent = 0

            frameStartTime = time.time()

            # Loop over packets within current frame
            while (packetCounter < (self.primaryPackets + 1)):
                # header[0] = frame
                # header[1] = 0

                if (packetCounter < self.primaryPackets):
                    bytesToSend = 7744  # 8000
                    # if (packetCounter == 0):
                    #     header[1] = packetCounter | self.SOF
                    # else:
                    #     header[1] = packetCounter
                else:
                    bytesToSend = self.trailingPacketSize + HEADER_SIZE
                    # header[1] = packetCounter | self.EOF

                # Prepend header to current packet
                packet = self.byteStream[streamPosn:streamPosn + bytesToSend]
                # print(["{:02x}".format(val) for val in packet[:]])
                # print("1x1 sending {} bytes".format(len(packet)))

                # print("Constructed Header: 0x{0:08x} 0x{1:08x}".format(header[0], header[1]))
                # dheader = np.frombuffer(self.byteStream[streamPosn:streamPosn+HEADER_SIZE], dtype=np.uint64)
                # print("decoded     Header: 0x{0:08x} 0x{1:08x}".format(dheader[0], dheader[1]))
                # Transmit packet
                bytesSent += sock.sendto(packet, (self.host, self.port))

                if not self.quiet:
                    print("bytesRemaining: {0:8} Sent: {1:8}".format(bytesRemaining, bytesSent),
                          "Sending data {0:8} through {1:8}..".format(streamPosn,
                                                                      streamPosn + bytesToSend))

                bytesRemaining -= bytesToSend
                packetCounter += 1
                streamPosn += bytesToSend
                # Start over if out of data to send
                if (bytesRemaining == 0):
                    bytesRemaining = len(self.byteStream)
                    streamPosn = 0

            if not self.quiet:
                print("  Sent frame {} packets {} bytes {}".format(frame, packetCounter, bytesSent))

            self.framesSent += 1
            self.packetsSent += packetCounter
            self.totalBytesSent += bytesSent

            # Calculate wait time and sleep so that frames are sent at requested intervals
            frameEndTime = time.time()
            waitTime = (frameStartTime + self.interval) - frameEndTime
            if waitTime > 0:
                time.sleep(waitTime)

        runTime = time.time() - runStartTime

        # Close socket
        sock.close()

        print("%d frames completed, %d bytes (including headers) sent in %.3f secs" %
              (self.framesSent, self.totalBytesSent, runTime))


if __name__ == '__main__':

    desc = "HexitecUdpProducer - generate UDP data stream from pcap file"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help="Hostname or IP address to transmit UDP frame data to")
    parser.add_argument('--port', type=int, default=61651,
                        help='select destination host IP port')
    parser.add_argument('--frames', '-n', type=int, default=1,
                        help='select number of frames to transmit')
    parser.add_argument('--interval', '-t', type=float, default=0.1,
                        help="select frame interval in seconds")
    parser.add_argument('--quiet', "-q", action="store_true",
                        help="Suppress detailed print during operation")
    parser.add_argument(
        'filename',
        default="hexitec_triangle_100G.pcapng",
        help='PCAP (Wireshark) file to load'
    )

    args = parser.parse_args()

    producer = HexitecUdpProducer(**vars(args))
    producer.run()
