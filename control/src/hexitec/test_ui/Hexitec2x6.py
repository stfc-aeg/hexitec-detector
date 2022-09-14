"""
Hexitec2x6: Exercises UDP control plane.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import sys
from RdmaUDP import RdmaUDP
from ast import literal_eval
import socket
import struct
import time  # DEBUGGING only


class Hexitec2x6():
    """
    Hexitec 2x6 class.

    Test we can access scratch registers in the KinteX FPGA.
    """

    def __init__(self, esdg_lab=False, debug=False, unique_cmd_no=False):
        """."""
        self.debug = debug
        self.unique_cmd_no = unique_cmd_no
        if esdg_lab:
            # Control IP addresses - MR
            self.local_ip = "192.168.4.1"  # Network card
            self.rdma_ip = "192.168.4.2"   # Hexitec 2x6 interface
        else:
            # Control IP addresses - CA
            self.local_ip = "10.0.3.1"  # Network card
            self.rdma_ip = "10.0.3.2"   # Hexitec 2x6 interface
        self.local_port = 61649
        self.rdma_port = 61648
        self.x10g_rdma = None

    def __del__(self):
        """."""
        self.x10g_rdma.close()

    def connect(self):
        """Connect to the 10 G UDP control channel."""
        self.x10g_rdma = RdmaUDP(self.local_ip, self.local_port,
                                 self.rdma_ip, self.rdma_port,
                                 9000, 1, self.debug,
                                 unique_cmd_no)
        self.x10g_rdma.setDebug(self.debug)
        self.x10g_rdma.ack = False  # True
        return self.x10g_rdma.error_OK

    def disconnect(self):
        """."""
        self.x10g_rdma.close()

    def read_scratch_registers(self):
        """Read scratch registers."""
        scratch0 = self.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
        # # print(scratch0)
        # scratch1 = self.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
        # # print(scratch1)
        # scratch2 = self.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
        # scratch3 = self.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
        # print("Scratch: 0x{0:08x}{1:08x}{2:08x}{3:08X}".format(scratch3, scratch2, scratch1, scratch0))
        print("Scratch: 0x{0:08x}".format(scratch0))

    def write_scratch_registers(self):
        """Write values to the four scratch registers."""
        self.x10g_rdma.write(0x8030, 0x12345678, "New Scratch Register1 value")
        self.x10g_rdma.write(0x8034, 0x9ABCDEF1, "New Scratch Register2 value")
        self.x10g_rdma.write(0x8038, 0xAAAAAAAA, "New Scratch Register3 value")
        self.x10g_rdma.write(0x803C, 0x60054003, "New Scratch Register4 value")

    def read_fpga_dna_registers(self):
        """Read the three DNA registers."""
        fpga_dna0 = self.x10g_rdma.read(0x0000800C, 'Read FPGA DNA part 1')
        fpga_dna1 = self.x10g_rdma.read(0x00008010, 'Read FPGA DNA part 2')
        fpga_dna2 = self.x10g_rdma.read(0x00008014, 'Read FPGA DNA part 3')
        print("FPGA DNA: 0x{0:08X} {1:08X} {2:08X}".format(fpga_dna2, fpga_dna1, fpga_dna0))

    def get_ambient_temperature(self, hex_val):
        """Calculate ambient temperature."""
        try:
            return ((int(hex_val, 16) * 175.72) / 65536) - 46.84
        except ValueError as e:
            print("Error converting ambient temperature: %s" % e)
            return -100

    def get_humidity(self, hex_val):
        """Calculate humidity."""
        try:
            return ((int(hex_val, 16) * 125) / 65535) - 6
        except ValueError as e:
            print("Error converting humidity: %s" % e)
            return -100

    def get_asic_temperature(self, hex_val):
        """Calculate ASIC temperature."""
        try:
            return int(hex_val, 16) * 0.0625
        except ValueError as e:
            print("Error converting ASIC temperature: %s" % e)
            return -100

    def get_adc_temperature(self, hex_val):
        """Calculate ADC Temperature."""
        try:
            return int(hex_val, 16) * 0.0625
        except ValueError as e:
            print("Error converting ADC temperature: %s" % e)
            return -100


if __name__ == '__main__':  # pragma: no cover
    if (len(sys.argv) != 4):
        print("Correct usage: ")
        print("python Hexitec2x6.py <esdg_lab> <debug> <unique_cmd_no>")
        print(" i.e. to not use esdg_lab addresses but enable debugging, and unique headers:")
        print("python Hexitec2x6.py False True True")
        sys.exit(-1)

    esdg_lab = literal_eval(sys.argv[1])
    debug = literal_eval(sys.argv[2])
    unique_cmd_no = literal_eval(sys.argv[3])
    hxt = Hexitec2x6(esdg_lab=esdg_lab, debug=debug, unique_cmd_no=unique_cmd_no)
    hxt.connect()
    # hxt.read_scratch_registers()

    try:
        # # Testing out translated tickle script #
        # # as_uart_tx 0xFF 0xF7 "" 0x0  0
        # print("Calling uart_tx(0xFF, 0xF7)")
        # hxt.x10g_rdma.uart_tx([0xFF, 0xF7])
        # time.sleep(0.25)
        # read_sensors = hxt.x10g_rdma.uart_rx(0x0)
        # print("Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))

        # Scratch Registers; Writing, Reading
        hxt.x10g_rdma.write(0x8030, 0x10203040, burst_len=1, comment="Set Scratch Reg1 value")
        scratch0 = hxt.x10g_rdma.read(0x00008030, comment='Read Scratch Register 1')
        print("Reg   1: {0:08X}".format(scratch0[0]))

        # hxt.x10g_rdma.write(0x8030, 0x4000003320000011, burst_len=2, comment="Set Scratch Reg12 value")
        # scratch12 = hxt.x10g_rdma.read(0x00008030, burst_len=2, comment='Read Scratch Register 1 2')
        # print("Reg  12: {}".format(', '.join("{0:8X}".format(x) for x in scratch12)))

        # hxt.x10g_rdma.write(0x8030, 0x600005554000033322200001, burst_len=3, comment="Set Scratch Reg123 value")
        # scratch123 = hxt.x10g_rdma.read(0x00008030, burst_len=3, comment='Read Scratch Register 1 2 3')
        # print("Reg 123: {}".format(', '.join("{0:8X}".format(x) for x in scratch123)))

        # hxt.x10g_rdma.write(0x8030, 0x81657777666600054444000322220001, burst_len=4, comment="Set Scratch Reg1234 value")
        # scratch1234 = hxt.x10g_rdma.read(0x00008030, burst_len=4, comment='Read Scratch Register 1 2 3 4')
        # print("Reg1234: {}".format(', '.join("{0:8X}".format(x) for x in scratch1234)))
        pass
    except (socket.error, struct.error) as e:
        print(" *** Scratch register error: {} ***".format(e))

    # # Request and receive environmental data #
    # print("Calling uart_tx(0x90, 0x52, \"\", 0x0)")
    # hxt.x10g_rdma.uart_tx([0x90, 0x52])
    # time.sleep(0.25)
    # read_sensors = hxt.x10g_rdma.uart_rx(0x0)
    # print("Received ({}) from UART: {}".format(len(read_sensors), ' '.join("0x{0:02X}".format(x) for x in read_sensors)))
    # # Display the environmentals values
    # read_sensors = read_sensors[1:]     # Omit start of sequence character, matching existing 2x2 source code formatting
    # sensors_values = "{}".format(''.join([chr(x) for x in read_sensors]))   # Turn list of integers into ASCII string
    # print(" ASCII string: {}".format(sensors_values))
    # ambient_hex = sensors_values[1:5]
    # humidity_hex = sensors_values[5:9]
    # asic1_hex = sensors_values[9:13]
    # asic2_hex = sensors_values[13:17]
    # adc_hex = sensors_values[17:21]
    # print(" * ambient_hex:  {} -> {} Celsius".format(sensors_values[1:5], hxt.get_ambient_temperature(sensors_values[1:5])))
    # print(" * humidity_hex: {} -> {}".format(sensors_values[5:9], hxt.get_humidity(sensors_values[5:9])))
    # print(" * asic1_hex:    {} -> {} Celsius".format(sensors_values[9:13], hxt.get_asic_temperature(sensors_values[9:13])))
    # print(" * asic2_hex:    {} -> {} Celsius".format(sensors_values[13:17], hxt.get_asic_temperature(sensors_values[13:17])))
    # print(" * adc_hex:      {} -> {} Celsius".format(sensors_values[17:21], hxt.get_adc_temperature(sensors_values[17:21])))

    # for index in range(100):
    #     print(index)
    #     hxt.x10g_rdma.write(0x8030, 0x81657777666600054444000322220001, burst_len=4, comment="New Scratch Register1234 value")
    #     scratch1234 = hxt.x10g_rdma.read(0x00008030, burst_len=4, comment='Read Scratch Register 1, 2, 3, 4')

    #     hxt.x10g_rdma.write(0x8030, 0x10203040, "New Scratch Register1 value")
    #     scratch0 = hxt.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
    #     # print("Reg1: {0:08X}".format(scratch0))
    #     hxt.x10g_rdma.write(0x8034, 0x71625344, "New Scratch Register2 value")
    #     scratch1 = hxt.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
    #     # print("Reg2: {0:08X}".format(scratch1))
    #     hxt.x10g_rdma.write(0x8038, 0xBEEFBEEF, "New Scratch Register3 value")
    #     scratch2 = hxt.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
    #     # print("Reg3: {0:08X}".format(scratch2))
    #     hxt.x10g_rdma.write(0x803C, 0xDEADDEAD, "New Scratch Register4 value")
    #     scratch3 = hxt.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
    #     print("{4:000} Scratch: 0x{0:08X}{1:08X}{2:08X}{3:08X}".format(scratch3, scratch2, scratch1, scratch0, index))
    #     break
    #     # # This matches writes made by rdma.py:
    #     # hxt.x10g_rdma.write(0x8030, 0xBAB00EFE, "New Scratch Register1 value")
    #     # scratch0 = hxt.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
    #     # print("Reg1: {0:08X}".format(scratch0))
    #     # hxt.x10g_rdma.write(0x8034, 0x23232323, "New Scratch Register2 value")
    #     # scratch1 = hxt.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
    #     # print("Reg2: {0:08X}".format(scratch1))
    #     # hxt.x10g_rdma.write(0x8038, 0x45454545, "New Scratch Register3 value")
    #     # scratch2 = hxt.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
    #     # print("Reg3: {0:08X}".format(scratch2))
    #     # hxt.x10g_rdma.write(0x803C, 0x67676767, "New Scratch Register4 value")
    #     # scratch3 = hxt.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
    #     # print("Scratch: 0x{0:08X}{1:08X}{2:08X}{3:08X}".format(scratch3, scratch2, scratch1, scratch0))
    #     # break

    hxt.disconnect()
