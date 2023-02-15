"""
Takes data from an h5 file and transmits specified number of frames.

Reads the data contents, creates headers and packetises
according to defined dimensions, sending to targeted host.

Created on November 14, 2022

@author: Christian Angelsen
"""

from __future__ import print_function

import argparse
import numpy as np
import socket
import h5py
import time
import sys
import os


class HexitecSender(object):
    """Produce and transmit specified UDP frames."""

    def __init__(self, host, port, frames, rows, columns,
                 size, extended_headers, interval, quiet, filename):
        """Initialise object with command line arguments."""
        self.SOF = 1 << 63
        self.EOF = 1 << 62
        # Default IP address?
        if host == "127.0.0.1":
            self.host = [host]
        else:
            self.host = host
        print("  self.host: {} ({})".format(self.host, type(self.host)))
        #  Default port/user didn't specify?
        if port == 61651:
            self.port = [port]
        else:
            self.port = port
        self.frames = frames
        self.extended_headers = extended_headers
        self.NROWS = rows
        self.NCOLS = columns
        self.NPIXELS = self.NROWS * self.NCOLS
        self.packet_size = size
        self.interval = interval
        self.quiet = quiet
        self.filename = filename
        if self.extended_headers:
            self.HEADER_SIZE = 64
        else:
            self.HEADER_SIZE = 8

        bytesPerPixel = 2
        bytesToRead = self.NPIXELS * bytesPerPixel

        # Workout number of primary packets, size of trailing packet

        totalFrameSize = self.NPIXELS * bytesPerPixel
        self.primaryPackets = totalFrameSize // self.packet_size
        self.trailingPacketSize = totalFrameSize % self.packet_size
        self.trailingPackets = 0
        if self.trailingPacketSize > 0:
            self.trailingPackets = 1
        self.totalPackets = self.primaryPackets + self.trailingPackets
        print("primaryPackets: {} trailingPacketSize: {}".format(
            self.primaryPackets, self.trailingPacketSize))
        print("totalFrameSize: {}".format(totalFrameSize))
        # print("totalPackets: {}".format(self.totalPackets))

        if os.access(self.filename, os.R_OK):
            print("Selected", self.frames, "frames, ", bytesToRead, "bytes.")
            file_contents = self.open_file()
            (images, rows, columns) = file_contents.shape
            self.totalBytesRead = images * rows * columns * bytesPerPixel
            print("Read {} image(s), {} rows x {} columns totalling {} Bytes.".format(
                images, rows, columns, self.totalBytesRead))
            self.byteStream = file_contents.tobytes()
        else:
            print("Unable to open: {}. Does it exist?".format(self.filename))
            sys.exit(1)

    def open_file(self):
        """Extract data from file."""
        # Initialise frame list and counters
        frames = None
        with h5py.File(self.filename, "r") as data_file:
            # print("Keys: {}".format(data_file.keys()))
            frames = np.array(data_file["raw_frames"], dtype=np.uint16)
        return frames

    def build_header(self, frame, packetCounter, packetCounterFlags):
        """Build selected header size."""
        if self.extended_headers:
            packet_flags = ((packetCounter << 0) | (packetCounterFlags))
            header_list = [frame, packet_flags]
        else:
            packet_flags = (frame) | ((packetCounter << 32) | (packetCounterFlags << (0)))
            header_list = [packet_flags]
        header = np.array(header_list, dtype=np.uint64)
        return header

    def run(self):
        """Transmit data to address, port."""
        print("Transmitting Hexitec data to address {} port {} ...".format(self.host, self.port))

        # Open UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.framesSent = 0
        self.packetsSent = 0
        self.totalBytesSent = 0

        streamPosn = 0

        runStartTime = time.time()

        bytesRemaining = len(self.byteStream)
        nodes = len(self.host)

        # Loop over selected number of frame(s)
        for frame in range(self.frames):

            packetCounter = 0
            bytesSent = 0

            frameStartTime = time.time()

            # Loop over packets within current frame
            while (packetCounter < (self.primaryPackets + self.trailingPackets)):

                packetCounterFlags = 0
                # If this is a start of frame packet, reset frame data and flag(s)
                if (packetCounter % self.totalPackets) == 0:
                    packetCounterFlags = self.SOF
                    packetCounter = 0
                elif (packetCounter % self.totalPackets) == (self.totalPackets-1):
                    packetCounterFlags = self.EOF
                # Build header matching requested data dimensions:
                header = self.build_header(frame, packetCounter, packetCounterFlags)
                # Display as bytes string:
                # built_integer = int(header).to_bytes(self.HEADER_SIZE, 'little')

                if (packetCounter < self.primaryPackets):
                    bytesToSend = self.packet_size
                else:
                    bytesToSend = self.trailingPacketSize

                # Prepend header to current packet
                packet = bytes(header) + self.byteStream[streamPosn:streamPosn + bytesToSend]
                # if (frame < 2):
                #     print(" header: {0}".format(' '.join("0x{0:016X}".format(x) for x in header)))

                if not self.quiet:
                    print("bytesRemaining: {0:8} Sent: {1:8}".format(bytesRemaining, bytesSent),
                          "Sending data {0:8} through {1:8}..".format(streamPosn,
                                                                      streamPosn + bytesToSend))

                # Transmit packet
                bytesSent += sock.sendto(packet, (self.host[frame % nodes], self.port[0]))

                bytesRemaining -= bytesToSend
                packetCounter += 1
                streamPosn += bytesToSend
                if streamPosn == self.totalBytesRead:
                    # bytesRemaining = len(self.byteStream)
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

        print("%d frames completed (%dx%d Pixels), %d bytes (including headers) sent in %.3f secs" %
              (self.framesSent, self.NROWS, self.NCOLS, self.totalBytesSent, runTime))


if __name__ == '__main__':

    desc = "HexitecSender - generate UDP data stream from pcap file"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--host', nargs='+', type=str, default='127.0.0.1',
                        help="Hostname(s) or IP(s) address to transmit UDP frame data to")
    parser.add_argument('--port', nargs='+', type=int, default=61651,
                        help='select destination port(s)')
    parser.add_argument('--frames', '-n', type=int, default=1,
                        help='select number of frames to transmit')
    parser.add_argument('--extended_headers', "-e", action="store_true",
                        help="Extended headers (64 bytes, or 8 bytes)")
    parser.add_argument('--rows', '-r', type=int, default=160,
                        help='set number of rows in frame')
    parser.add_argument('--columns', '-c', type=int, default=160,
                        help='set number of columns in frame')
    parser.add_argument('--size', '-s', type=int, default=8000,
                        help='set packet size')
    parser.add_argument('--interval', '-t', type=float, default=0.01,
                        help="select frame interval in seconds")
    parser.add_argument('--quiet', "-q", action="store_true",
                        help="Suppress detailed print during operation")
    parser.add_argument(
        'filename',
        default="sample.h5",
        help='H5 file to load'
    )

    args = parser.parse_args()

    producer = HexitecSender(**vars(args))
    producer.run()
