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

    READ_REG_VALUE = 0x41
    SET_REG_BIT = 0x42
    SEND_REG_BURST = 0x44

    VSR_ADDRESS = [
        0x90,
        0x91
    ]

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

    def await_uart_ready(self):
        """Wait until uart has received incoming data."""
        rx_pkt_done = 0
        counter = 0
        while not rx_pkt_done:
            uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = hxt.x10g_rdma.read_uart_status()
            counter += 1
            if counter > 15000:
                raise Exception("Timed out waiting for UART data")
        print("{0:05} UART: {1:08X} tx_buff_full: {2:0X} tx_buff_empty: {3:0X} rx_buff_full: {4:0X} rx_buff_empty: {5:0X} rx_pkt_done: {6:0X}".format(
            counter, uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done))

    def send_cmd(self, cmd):
        """Send a command string to the microcontroller."""
        print("... sending: {}".format(' '.join("0x{0:02X}".format(x) for x in cmd)))
        self.x10g_rdma.uart_tx(cmd)

    def read_response(self):
        """Read a VSR's microcontroller response, passed on by the FEM."""
        counter = 0
        rx_pkt_done = 0
        while not rx_pkt_done:
            uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = self.x10g_rdma.read_uart_status()
            counter += 1
            if counter == 15001:
                break
        response = self.x10g_rdma.uart_rx(0x0)
        print("... receiving: {} ({})".format(' '.join("0x{0:02X}".format(x) for x in response), counter))
        return response
        # return self.x10g_rdma.uart_rx(0x0)

    def module_mask(self, module):
        """Bit manipulation for VSR/HV control functions."""
        return ((1 << (module - 1)) | (1 << (module + 8 - 1)))

    def negative_module_mask(self, module):
        """Bit manipulation for VSR/HV control functions."""
        return ~(1 << (module - 1)) | (1 << (module + 8 - 1))

    enable_vsrs_mask = 0x3F
    hvs_bit_mask = 0x3F00
    vsr_ctrl_offset = 0x18
    ENABLE_VSR = 0xE3
    DISABLE_VSR = 0xE2

    def enable_vsr_or_hv(self, vsr_number, bit_mask):
        """Control a single VSR's power."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(vsr_number)
        cmd_mask = bit_mask
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("VSR {} enabled".format(vsr_number))

    def enable_vsr(self, vsr_number):
        """Control a single VSR's power."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(vsr_number)
        cmd_mask = Hexitec2x6.enable_vsrs_mask
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("VSR {} enabled".format(vsr_number))

    def disable_vsr(self, vsr_number):
        """Control a single VSR's power."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl disable $::vsr_target_idx
        mod_mask = self.negative_module_mask(vsr_number)
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        # print("read_value: {}".format(read_value))
        # print("mod_mask: {}".format(mod_mask))
        masked_value = read_value & mod_mask
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + vsr_number
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.DISABLE_VSR])
        print("VSR {} disabled".format(vsr_number))

    def enable_all_vsrs(self):
        """Switch all VSRs on."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | 0x3F    # Switching all six VSRs on, i.e. set 6 bits on
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all VSRs on")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("All VSRs enabled")

    def enable_all_hv(self):
        """Switch all HVs on."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | Hexitec2x6.hvs_bit_mask     # Switching all six HVs on
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all HVs on")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("All HVs on")

    def enable_hv(self, hv_number):
        """Switch on a single VSR's power."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        # STEP 1: vsr_ctrl enable $::vsr_target_idx
        mod_mask = self.module_mask(hv_number)
        cmd_mask = Hexitec2x6.hvs_bit_mask
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value | (cmd_mask & mod_mask)
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch selected VSR on")
        time.sleep(1)
        # STEP 2: as_uart_tx $vsr_addr $vsr_cmd "$vsr_data" $uart_addr $lines $hw_axi_idx
        vsr_address = 0x89 + hv_number
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.ENABLE_VSR])
        print("HV {} on".format(hv_number))

    def disable_all_hv(self):
        """Switch all HVs off."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value & 0x3F    # Switching all six HVs off
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all HVs off")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.DISABLE_VSR])
        print("All HVs off")

    def disable_all_vsrs(self):
        """Switch all VSRs off."""
        vsr_ctrl_addr = Hexitec2x6.vsr_ctrl_offset
        read_value = self.x10g_rdma.read(vsr_ctrl_addr, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        masked_value = read_value & Hexitec2x6.hvs_bit_mask  # Switching all six VSRs off
        self.x10g_rdma.write(vsr_ctrl_addr, masked_value, burst_len=1, comment="Switch all VSRs off")
        time.sleep(1)
        vsr_address = 0xFF
        self.x10g_rdma.uart_tx([vsr_address, Hexitec2x6.DISABLE_VSR])
        print("All VSRs disabled")

    def power_status(self):
        """Read out the status register to check what is switched on and off."""
        read_value = self.x10g_rdma.read(Hexitec2x6.vsr_ctrl_offset, burst_len=1, comment='Read vsr_ctrl_addr current value')
        read_value = read_value[0]
        print(" *** Register status: 0x{0:08X}".format(read_value))


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

    try:
        vsr_number = 0x90

        # # Enable VSR(s)..
        # hxt.enable_vsr_or_hv(1, Hexitec2x6.enable_vsrs_mask)  # Switches a single VSR on
        # hxt.enable_vsr_or_hv(1, Hexitec2x6.hvs_bit_mask)  # Switches a single HV on
        # hxt.enable_vsr_or_hv(2, Hexitec2x6.enable_vsrs_mask)

        # hxt.disable_all_hv()    # Working
        hxt.disable_all_vsrs()  # Working
        time.sleep(1)
        # hxt.disable_all_hv()
        hxt.power_status()
        # time.sleep(1)
        hxt.enable_all_vsrs()
        # hxt.enable_vsr(1)  # Switches a single VSR on
        # time.sleep(1)
        # hxt.enable_vsr(2)
        # time.sleep(1)
        # hxt.enable_vsr(3)  # Switches a single VSR on
        # time.sleep(1)
        # hxt.enable_vsr(4)  # Switches a single VSR on
        # time.sleep(1)
        # hxt.enable_vsr(5)  # Switches a single VSR on
        # time.sleep(1)
        # hxt.enable_vsr(6)  # Switches a single VSR on
        # time.sleep(1)
        hxt.power_status()
        # hxt.power_status()
        # hxt.disable_vsr(1)
        # # hxt.enable_all_hv()
        # hxt.enable_hv(1)
        # hxt.power_status()
        # hxt.power_status()
        # hxt.enable_vsr(2)
        # hxt.power_status()

    except (socket.error, struct.error) as e:
        print(" *** Scratch register error: {} ***".format(e))

    hxt.disconnect()
