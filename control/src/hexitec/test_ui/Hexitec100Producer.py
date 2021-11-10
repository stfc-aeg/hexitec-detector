"""Takes a binary file and transmits specified number of frames.

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


class Hexitec100ProducerError(Exception):
    """Customised exception class."""

    def __init__(self, msg):
        """Initialise."""
        self.msg = msg

    def __str__(self):
        """MagicMethod."""
        return repr(self.msg)


class Hexitec100ProducerDefaults(object):
    """Holds default values for frame producer parameters."""

    def __init__(self):
        """Initialise defaults."""
        self.ip_addr = 'localhost'
        self.port_list = [61651]
        self.num_frames = 0
        self.tx_interval = 0
        self.drop_frac = 0
        self.drop_list = None

        self.filename = 'sample.bin'


class Hexitec100Producer(object):
    """Produce and transmit specified UDP frames."""

    def __init__(self, host, port, frames, sensorrows, sensorcolumns,
                 interval, display, quiet, filename):
        """Initialise object with command line arguments."""
        pixelsPerRow = 80
        pixelsPerColumn = 80
        self.host = host
        self.port = port
        self.frames = frames
        self.pixelrows = sensorrows * pixelsPerRow
        self.pixelcolumns = sensorcolumns * pixelsPerColumn
        self.interval = interval
        self.display = display
        self.quiet = quiet
        self.filename = filename

        pixelsToRead = self.frames * (self.pixelrows * self.pixelcolumns)
        bytesPerPixel = 2
        bytesToRead = pixelsToRead * bytesPerPixel

        # Workout number of primary packets, size of trailing packet

        totalFrameSize = (self.pixelrows * self.pixelcolumns) * bytesPerPixel
        self.primaryPackets = totalFrameSize // 8000
        self.trailingPacketSize = totalFrameSize % 8000
        print("Rows: {} Columns: {}. Primary packets: {} Trailing Packet Size: {}".format(self.pixelrows, self.pixelcolumns, self.primaryPackets, self.trailingPacketSize))

        if os.access(self.filename, os.R_OK):
            print("Selected", self.frames, "frames, ", bytesToRead, "bytes.")
            file_contents = self.decode_pcap()
            self.byteStream = file_contents.tobytes()
        else:
            print("Unable to open: {}. Does it exist?".format(self.filename))
            sys.exit(1)

    # Extracts extended header-sized udp data from file
    def decode_pcap(self):

        SOF = 1<<63
        EOF = 1<<62
        NCOLS = 80
        NROWS = 80
        NPIXELS = NCOLS * NROWS
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
            #print([hex(val) for val in header])
            assert header[0] == num_frames

            # If this is a start of frame packet, reset frame data
            if int(header[1]) & SOF:
                frame_data = bytes()

            # Append frame payload to frame data, discarding header
            frame_data += payload[HEADER_SIZE:]

            # If this is an end of frame packet, convert frame data to numpy array and append to frame list
            if int(header[1]) & EOF:
                frame = np.frombuffer(frame_data, dtype=np.uint16).reshape((80, 80))
                assert frame.size == NPIXELS
                frames.append(frame)
                num_frames += 1

        # Convert frame list to 3D numpy array
        frames = np.array(frames)

        print("Decoded {} frames from {} packets in PCAP file {}".format(num_frames, num_packets, self.filename))

        return frames

    def run(self):
        """Transmit data to address, port."""
        self.payloadLen = 8000
        startOfFrame = 0x80000000
        endOfFrame = 0x40000000

        print("Transmitting Hexitec data to address {} port {} ...".format(self.host, self.port))

        # Open UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Create packet header
        header = np.zeros(2, dtype=np.uint32)

        self.framesSent = 0
        self.packetsSent = 0
        self.totalBytesSent = 0

        streamPosn = 0

        runStartTime = time.time()

        # Loop over selected number of frame(s)
        for frame in range(self.frames):

            bytesRemaining = len(self.byteStream)

            packetCounter = 0
            bytesSent = 0

            frameStartTime = time.time()

            # Loop over packets within current frame
            while (packetCounter < (self.primaryPackets + 1)):
                header[0] = frame
                header[1] = 0

                if (packetCounter < self.primaryPackets):
                    bytesToSend = 8000
                    if (packetCounter == 0):
                        header[1] = packetCounter | startOfFrame
                    else:
                        header[1] = packetCounter
                else:
                    bytesToSend = self.trailingPacketSize
                    header[1] = packetCounter | endOfFrame

                # Prepend header to current packet
                packet = header.tobytes() + self.byteStream[streamPosn:streamPosn + bytesToSend]

                # print("Header: 0x{0:08x} 0x{1:08x}".format(header[0], header[1]))
                if not self.quiet:
                    print("bytesRemaining: {0:8} Sent: {1:8}".format(bytesRemaining, bytesSent),
                          "Sending data {0:8} through {1:8}..".format(streamPosn,
                                                                      streamPosn + bytesToSend))

                # Transmit packet
                bytesSent += sock.sendto(packet, (self.host, self.port))

                bytesRemaining -= bytesToSend
                packetCounter += 1
                streamPosn += bytesToSend

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

    desc = "Hexitec100Producer - generate UDP data stream from bin file"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help="Hostname or IP address to transmit UDP frame data to")
    parser.add_argument('--port', type=int, default=61651,
                        help='select destination host IP port')
    parser.add_argument('--frames', '-n', type=int, default=1,
                        help='select number of frames to transmit')
    parser.add_argument('--sensorrows', '-r', type=int, default=1,
                        help='number of sensors per row')
    parser.add_argument('--sensorcolumns', '-c', type=int, default=1,
                        help='number of sensors per column')
    parser.add_argument('--interval', '-t', type=float, default=0.1,
                        help="select frame interval in seconds")
    parser.add_argument('--display', "-d", action='store_true',
                        help="Enable diagnostic display of generated image")
    parser.add_argument('--quiet', "-q", action="store_true",
                        help="Suppress detailed print during operation")
    parser.add_argument(
        'filename',
        default="sample.bin",
        help='Bin file to load'
    )

    args = parser.parse_args()

    producer = Hexitec100Producer(**vars(args))
    producer.run()
