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

    SEND_REG_VALUE = 0x40   # Verified to work with UART
    READ_REG_VALUE = 0x41   # Verified to work with UART
    SET_REG_BIT = 0x42      # Avoid
    CLR_REG_BIT = 0x43      # Not verified, tolerated twice, see enable_adc, "Enable Vcal"
    SEND_REG_BURST = 0x44   # Avoid

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
        self.error_list = []
        self.error_count = 0

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
        while not rx_pkt_done:
            uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done = self.x10g_rdma.read_uart_status()
            counter += 1
            if counter == 15001:
                print("\n\t read_response() timed out waiting for uart!\n")
                break
        response = self.x10g_rdma.uart_rx(0x0)
        # print("... receiving: {}. {}".format(response, counter))
        # print("... receiving: {} ({})".format(' '.join("0x{0:02X}".format(x) for x in response), counter))
        return response

    def read_and_response(self, vsr, address_h, address_l):
        """Send a read and read the reply."""
        self.delaying()
        self.send_cmd([vsr, 0x41, address_h, address_l])
        self.delaying()
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        reply = resp[2:-1]                                      # Omit start char, vsr address and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" RR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        return resp, reply

    def delaying(self):
        # time.sleep(0.2)
        pass

    def write_and_response(self, vsr, address_h, address_l, value_h, value_l, masked=True, delay=False):
        """Write value_h, value_l to address_h, address_l of vsr, if not masked then register value overwritten."""
        self.delaying()
        resp, reply = self.read_and_response(vsr, address_h, address_l)
        # if delay:
        #     print("   WaR Rd1: resp: {} reply: {} ".format(resp, reply))
        resp = resp[2:-1]   # Extract payload
        if masked:
            value_h = value_h | resp[0]     # Mask existing value with new value
            value_l = value_l | resp[1]     # Mask existing value with new value
        # print("   WaR Write: {} {} {} {} {}".format(vsr, address_h, address_l, value_h, value_l))
        self.delaying()
        self.send_cmd([vsr, 0x40, address_h, address_l, value_h, value_l])
        if delay:
            time.sleep(0.2)
        self.delaying()
        resp = self.read_response()                             # ie resp = [42, 144, 48, 49, 13]
        if delay:
            # print("   WaR Rd2: resp: {} reply: {} ".format(resp, reply))
            time.sleep(0.2)
        reply = resp[4:-1]                                      # Omit start char, vsr & register addresses, and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(" WR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        if ((resp[4] != value_h) or (resp[5] != value_l)):
            print("H? {} L? {}".format(resp[4] == value_h, resp[5] == value_l))
            print("WaR. reply: {} (resp: {}) VERSUS value_h: {} value_l: {}".format(reply, resp, value_h, value_l))
            print("WaR. (resp: {} {}) VERSUS value_h: {} value_l: {}".format(resp[4], resp[5], value_h, value_l))
            raise HexitecFemError("Readback value did not match written!")
        return resp, reply

    def block_write_custom_length(self, vsr, number_registers, address_h, address_l, write_values):
        """Write write_values starting with address_h, address_l of vsr, spanning number_registers."""
        if (number_registers * 2) != len(write_values):
            print("Mismatch! number_registers ({}) isn't half of write_values ({}).".format(number_registers, len(write_values)))
            return -1
        values_list = write_values.copy()
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        for index in range(number_registers):
            value_h = values_list.pop(0)
            value_l = values_list.pop(0)
            # print("   BWCL Write: {0:X} {1:X} {2:X} {3:X} {4:X}".format(vsr, most_significant[index], least_significant[index], value_h, value_l))
            self.write_and_response(vsr, most_significant[index], least_significant[index], value_h, value_l, False, False)

    def burst_write(self, vsr, number_registers, address_h, address_l, write_values):
        """Write bytes to multiple registers."""
        command = [vsr, 0x44, address_h, address_l]
        for entry in write_values:
            command.append(entry)
        self.send_cmd(command)
        resp = self.read_response()
        reply = resp[4:-1]
        reply = "{}".format(''.join([chr(x) for x in reply]))
        # print(" BR. reply: {} (resp: {})".format(reply, resp))
        return resp, reply

    def expand_addresses(self, number_registers, address_h, address_l):
        """Expand addresses by the number_registers specified.

        ie If (number_registers, address_h, address_l) = (10, 0x36, 0x31)
        would produce 10 addresses of:
        (0x36 0x31) (0x36 0x32) (0x36 0x33) (0x36 0x34) (0x36 0x35)
        (0x36 0x36) (0x36 0x37) (0x36 0x38) (0x36 0x39) (0x36 0x41)
        """
        most_significant = []
        least_significant = []
        for index in range(address_l, address_l+number_registers):
            most_significant.append(address_h)
            least_significant.append(address_l)
            address_l += 1
            if address_l == 0x3A:
                address_l = 0x41
            if address_l == 0x47:
                address_h += 1
                if address_h == 0x3A:
                    address_h = 0x41
                address_l = 0x30
        return most_significant, least_significant

    def block_read_and_response(self, vsr, number_registers, address_h, address_l):
        """Read from address_h, address_l of vsr, covering number_registers registers."""
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        resp_list = []
        reply_list = []
        for index in range(number_registers):
            resp, reply = self.read_and_response(vsr, most_significant[index], least_significant[index])
            resp_list.append(resp[2:-1])
            reply_list.append(reply)
        # print(" BRaR, resp_list: {} reply_list {}".format(resp_list, reply_list))
        # raise Exception("Premature!")
        return resp_list, reply_list

    def enables_write_and_read_verify(self, vsr, address_h, address_l, write_list):
        """Write and read to verify correct bytes written to register."""
        number_registers = 10
        self.block_write_custom_length(vsr, number_registers, address_h, address_l, write_list)
        # self.burst_write(vsr, number_registers, address_h, address_l, write_list)

        resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
        read_list = []
        for a, b in resp_list:
            read_list.append(a)
            read_list.append(b)
        # print("read_list : {}".format(read_list))
        if not (write_list == read_list):
            print(" Register 0x{0}{1}: Error".format(chr(address_h), chr(address_l)))
            print("     Wrote: {}".format(write_list))
            print("     Read : {}".format(read_list))
            # raise HexitecFemError("Exiting upon inaccurate read back")
            # self.error_list.append(" VSR {2:X} Register 0x{0}{1}: ERROR".format(chr(address_h), chr(address_l), vsr))
            # self.error_list.append("     Wrote: {}".format(write_list))
            # self.error_list.append("     Read : {}".format(read_list))
            # self.error_count += 1
            # Check again:
            resp_list, reply_list = self.block_read_and_response(vsr, number_registers, address_h, address_l)
            read_list = []
            for a, b in resp_list:
                read_list.append(a)
                read_list.append(b)
            if not (write_list == read_list):
                print(" ** Readback value still inaccurate:")
                print(" **    Wrote: {}".format(write_list))
                print(" **    Read : {}".format(read_list))
                self.error_list.append(" VSR {2:X} Register 0x{0}{1}: ERROR".format(chr(address_h), chr(address_l), vsr))
                self.error_list.append("     Wrote: {}".format(write_list))
                self.error_list.append("     Read : {}".format(read_list))
                self.error_count += 1
            else:
                print("Error NOT repeated in second readback(!)")


class HexitecFemError(Exception):
    """Simple exception class for HexitecFem to wrap lower-level exceptions."""

    pass


if __name__ == '__main__':  # noqa: C901
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
    beginning = time.time()
    try:
        # VSR_ADDRESS = range(0x90, 0x96)
        # hxt.x10g_rdma.enable_all_vsrs()     # Switches all VSRs on
        VSR_ADDRESS = [0x90]
        hxt.x10g_rdma.enable_vsr(1)  # Switches a single VSR on

        this_delay = 10
        print("VSR(s) powered; Waiting {} seconds".format(this_delay))
        time.sleep(this_delay)

        print("Send E3 to all VSR..")
        hxt.x10g_rdma.uart_tx([0xFF, 0xE3])
        print("Wait 5 sec")
        time.sleep(5)
        beginning = time.time()

        for vsr in VSR_ADDRESS:
            # Register 0x61 - Column Read Enable ASIC
            address_h, address_l = 0x36, 0x31
            for index in range(0, 100):
                if index % 10 == 0:
                    print(index)
                write_list = [70, 57, 51, 70, 52, 69, 70, 70, 68, 49, 69, 55, 56, 70, 67, 65, 55, 67, 70, 66]
                hxt.enables_write_and_read_verify(vsr, address_h, address_l, write_list)
                write_list = [56, 56, 55, 57, 65, 56, 56, 48, 55, 50, 56, 67, 53, 56, 56, 69, 52, 57, 66, 48]
                hxt.enables_write_and_read_verify(vsr, address_h, address_l, write_list)

        ending = time.time()
        print("That took: {}".format(ending - beginning))

        print("___________________ FINISHED ___________________")
        if hxt.error_count > 0:
            print(" Detected {} errors in the read back.".format(hxt.error_count))
            for index in hxt.error_list:
                print(index)

    except (socket.error, struct.error) as e:
        print(" *** Caught Exception: {} ***".format(e))

    hxt.disconnect()