"""
HexitecBias.py: Script for enabling, setting, disabling, HV bias.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

import sys
from RdmaUDP import RdmaUDP
from ast import literal_eval
import socket
import struct
import time  # DEBUGGING only


class HexitecBias():
    """
    Hexitec 2x6 class.

    Test we can control HV bias.
    """

    HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                      0x41, 0x42, 0x43, 0x44, 0x45, 0x46]

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
        self.vsr_addr = 0x90

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

    def send_cmd(self, cmd):
        """Send a command string to the microcontroller."""
        # print("... sending: {}".format(' '.join("0x{0:02X}".format(x) for x in cmd)))
        self.x10g_rdma.uart_tx(cmd)

    def read_response(self):
        """Read a VSR's microcontroller response, passed on by the FEM."""
        counter = 0
        rx_pkt_done = 0
        # print("uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done")
        while not rx_pkt_done:
            uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = self.x10g_rdma.read_uart_status()
            # print("     {0:X}          {1:X}             {2:X}              {3:X}          {4:X}            {5:X}".format(
            #     uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done))
            counter += 1
            if counter == 15001:
                break
        response = self.x10g_rdma.uart_rx(0x0)
        # print("R: {}. {}".format(response, counter))
        # print("... receiving: {} ({})".format(' '.join("0x{0:02X}".format(x) for x in response), counter))
        return response
        # return self.x10g_rdma.uart_rx(0x0)

    def convert_to_hv(self, hex_value):
        """Convert hexadecimal value into HV voltage."""
        return (hex_value / 0xFFF) * 1250

    def convert_to_hex(self, hv_value):
        """Convert HV voltage into hexadecimal value."""
        return int((hv_value / 1250) * 0xFFF)

    def convert_to_aspect_format(self, value):
        """Convert integer to Aspect's hexadecimal notation e.g. 31 (0x1F) -> 0x31, 0x46."""
        hex_string = "{:02x}".format(value)
        high_string = hex_string[0]
        low_string = hex_string[1]
        high_int = int(high_string, 16)
        low_int = int(low_string, 16)
        high_encoded = self.HEX_ASCII_CODE[high_int]
        low_encoded = self.HEX_ASCII_CODE[low_int]
        return high_encoded, low_encoded

    def convert_bias_to_dac_values(self, hv):
        """Convert bias level to DAC formatted values.

        I.e. 21 V -> 0x0041 (0x30, 0x30, 0x34, 0x31)
        """
        hv_hex = hxt.convert_to_hex(hv)
        print(" Selected hv: {0}. Converted to hex: {1:04X}".format(hv, hv_hex))
        hv_hex_msb = hv_hex >> 8
        hv_hex_lsb = hv_hex & 0xFF
        hv_msb = hxt.convert_to_aspect_format(hv_hex_msb)
        hv_lsb = hxt.convert_to_aspect_format(hv_hex_lsb)
        # print(" Conv'd to aSp_M: {}".format(hv_msb))
        # print(" Conv'd to aSp_L: {}".format(hv_lsb))
        return hv_msb, hv_lsb


if __name__ == '__main__':  # pragma: no cover
    if (len(sys.argv) != 4):
        print("Correct usage: ")
        print("python HexitecBias.py <esdg_lab> <debug> <unique_cmd_no>")
        print(" i.e. to not use esdg_lab addresses but enable debugging, and unique headers:")
        print("python HexitecBias.py False True True")
        sys.exit(-1)

    esdg_lab = literal_eval(sys.argv[1])
    debug = literal_eval(sys.argv[2])
    unique_cmd_no = literal_eval(sys.argv[3])
    hxt = HexitecBias(esdg_lab=esdg_lab, debug=debug, unique_cmd_no=unique_cmd_no)
    hxt.connect()
    beginning = time.time()
    try:
        # Bias will be negative but the Software and aS_PWR_TRIG_HV board
        # deals with positive values
        hv = 30
        print("Going to set HV bias to -{} volts".format(hv))
        hv_msb, hv_lsb = hxt.convert_bias_to_dac_values(hv)

        print("Testing aS_PWR_TRIG_HV board")
        print("Get PWR Status: [0x49]")
        hxt.x10g_rdma.uart_tx([0xC0, 0x49])
        time.sleep(0.5)
        reply = hxt.x10g_rdma.uart_rx(0x0)
        # print("reply: {}".format(reply))
        print(" ->            ({}) from UART: {}. Raw: {}".format(len(reply), ''.join([chr(x) for x in reply[2:-1]]), reply))

        # TODO: WHY DOESN'T THIS WORK: ???
        # print(" Compare with calling as_power_status()")
        # reply = hxt.x10g_rdma.as_power_status()
        # print(" ->            ({}) from UART: {}. Raw: {}".format(len(reply), ''.join([chr(x) for x in reply[2:-1]]), reply))

        print("Get Status: [0x20]")
        hxt.x10g_rdma.uart_tx([0xC0, 0x20])
        time.sleep(0.5)
        reply = hxt.x10g_rdma.uart_rx(0x0)
        print(" ->            ({}) from UART: {}. Raw: {}".format(len(reply), ''.join([chr(x) for x in reply[2:-1]]), reply))

        print("Enable: [0xE3]")
        hxt.x10g_rdma.uart_tx([0xC0, 0xE3])
        time.sleep(0.5)

        print("Write DAC: [0x54]")
        # 0x0000 -> 0V HV, 0x0CCC -> -1000V, 0x0FFF -> -1250V
        # (hex_value/0xFFF) * 1250 = HV
        # 0x042 -> -20.14652014652015V
        # hv_msb = 0x30, 0x30
        # hv_lsb = 0x34, 0x32
        hxt.x10g_rdma.uart_tx([0xC0, 0x54, 0x30, 0x30, 0x30, 0x30,
                               0x30, 0x30, 0x30, 0x30,
                               0x30, 0x30, 0x30, 0x30,
                               hv_msb[0], hv_msb[1], hv_lsb[0], hv_lsb[1],
                               0x30, 0x30, 0x30, 0x30,
                               0x30, 0x30, 0x30, 0x30,
                               0x30, 0x30, 0x30, 0x30,
                               0x30, 0x30, 0x30, 0x30])
        time.sleep(0.5)
        reply = hxt.x10g_rdma.uart_rx(0x0)
        # print("reply: {}".format(reply))
        print(" ->            ({}) from UART: {}. Raw: {}".format(len(reply), ''.join([chr(x) for x in reply[2:-1]]), reply))

        delay = 15
        print("enabled, bias level set - waiting {} seconds..".format(delay))
        time.sleep(delay)

        print("Disable: [0xE2]")
        hxt.x10g_rdma.uart_tx([0xC0, 0xE2])
        print("disabled, all done!")

    except (socket.error, struct.error) as e:
        print(" *** Caught Exception: {} ***".format(e))

    hxt.disconnect()
