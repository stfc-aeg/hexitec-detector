"""
Hexitec2x6: Exercises UDP control plane.

Christian Angelsen, STFC Detector Systems Software Group, 2022.
"""

from RdmaUDP import RdmaUDP
import time

class Hexitec2x6():
    """
    Hexitec 2x6 class.

    Test we can access scratch registers in the KinteX FPGA.
    """

    def __init__(self, debug=False):
        self.debug = debug
        # Control IP addresses
        self.server_ctrl_ip_addr = "10.0.3.1"  # Network card
        self.camera_ctrl_ip_addr = "10.0.3.2"  # Hexitec 2x6 interface
        self.x10g_rdma = None

    def __del__(self):
        self.x10g_rdma.close()

    def connect(self):
        """Connect to the 10 G UDP control channel."""
        self.x10g_rdma = RdmaUDP(self.server_ctrl_ip_addr, 61649, self.server_ctrl_ip_addr, 61648,
                                 self.camera_ctrl_ip_addr, 61648, 2000000, 9000, 20, self.debug)
        self.x10g_rdma.setDebug(self.debug)
        self.x10g_rdma.ack = True
        return self.x10g_rdma.error_OK

    def read_scratch_registers(self):
        """Read scratch registers."""
        scratch0 = self.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
        scratch1 = self.x10g_rdma.read(0x00008034, 'Read Scratch Register 2')
        scratch2 = self.x10g_rdma.read(0x00008038, 'Read Scratch Register 3')
        scratch3 = self.x10g_rdma.read(0x0000803C, 'Read Scratch Register 4')
        print("Scratch: 0x{0:08x} {1:08x} {2:08x} {3:08X}".format(scratch3, scratch2, scratch1, scratch0))

    def write_scratch_registers(self):
        """Write values to the four scratch registers."""
        # self.x10g_rdma.write(0x8030, 0x12345678, "New Scratch Register1 value")
        time.sleep(1)
        self.x10g_rdma.write(0x8034, 0x9A0000F1, "New Scratch Register2 value")
        time.sleep(1)
        # self.x10g_rdma.write(0x8038, 0xAAAAAAAA, "New Scratch Register3 value")
        # time.sleep(1)
        # self.x10g_rdma.write(0x803C, 0x60054003, "New Scratch Register4 value")
        # time.sleep(1)

    def read_fpga_dna_registers(self):
        """Read the three DNA registers."""
        fpga_dna0 = self.x10g_rdma.read(0x0000800C, 'Read FPGA DNA part 1')
        fpga_dna1 = self.x10g_rdma.read(0x00008010, 'Read FPGA DNA part 2')
        fpga_dna2 = self.x10g_rdma.read(0x00008014, 'Read FPGA DNA part 3')
        print("FPGA DNA: 0x{0:08x} {1:08x} {2:08x}".format(fpga_dna2, fpga_dna1, fpga_dna0))

    def disconnect(self):
        """."""
        self.x10g_rdma.close()

# Testing functionality for Matt Robert 's scripting
def prod_list(bytes):
    """."""
    bytes_list = []
    for idx in range(len(bytes)):
        bytes_list.append(bytes[idx])
    return bytes_list

def display_register_information(name, read_bytes):
    r"""Take a bytes object, display its name, length, address and value.

    I.e. b"\x02\x00\x00\x01\x04\x00\x02\x00\x00b\x00\x00'\xb8`\xb4"
    Contain address: 0x00020004, Value: 0x00006200, Length: 16
    """
    bytes_list = prod_list(read_bytes)
    print("Reg: {}, length: {}".format(name, len(read_bytes)))
    print("     address: 0x{0:02x}{1:02x}{2:02x}{3:02x}".format(bytes_list[7], bytes_list[6], bytes_list[5], bytes_list[4]))
    print("       Value: 0x{0:02x}{1:02x}{2:02x}{3:02x}".format(bytes_list[11], bytes_list[10], bytes_list[9], bytes_list[8]))


if __name__ == '__main__':  # pragma: no cover

    hxt = Hexitec2x6(True)
    hxt.connect()
    # hxt.read_scratch_registers()
    hxt.write_scratch_registers()
    hxt.read_scratch_registers()
    # hxt.read_fpga_dna_registers()
    hxt.disconnect()
    print("All done!")

    # A few example bytes objects, converted into human readable format

    # # #Scratch register 1
    # # #*** READ, Going to send:
    # # #b'\x02\x00\x00\x010\x80\x00\x00'
    # # #Read Back Data:
    # sr1 =	b'\x02\x00\x00\x010\x80\x00\x00\x11\x11\x11\x11\xef\xbe\xad\xde'
    # display_register_information("sr1", sr1)

    # # #Scratch Register 2
    # # #*** READ, Going to send:
    # # # b'\x02\x00\x00\x014\x80\x00\x00'
    # # # Read Back Data:
    # sr2 = b'\x02\x00\x00\x014\x80\x00\x00\xef\xbe\xad\xde3333'
    # display_register_information("sr2", sr2)

    # # # Scratch Register 3
    # # # *** READ, Going to send:
    # # # b'\x02\x00\x00\x018\x80\x00\x00'
    # # # Read Back Data:
    # sr3 = b'\x02\x00\x00\x018\x80\x00\x003333DDDD'
    # display_register_information("sr3", sr3)

    # # # Scratch Register 4
    # # # *** READ, Going to send:
    # # # b'\x02\x00\x00\x01<\x80\x00\x00'
    # # # Read Back Data:
    # sr4 = b'\x02\x00\x00\x01<\x80\x00\x00DDDD\x00\x00\x00\x00'
    # display_register_information("sr4", sr4)

    # # Source Mac address, lower
    # # *** READ, Going to send:
    # # b'\x02\x00\x00\x01\x00\x00\x02\x00'
    # # Read Back Data:
    # sml = b'\x02\x00\x00\x01\x00\x00\x02\x00\x04\x00\x00\x00\x00b\x00\x00'
    # display_register_information("sml", sml)

    # # Source Mac address, upper
    # # *** READ, Going to send:
    # # b'\x02\x00\x00\x01\x04\x00\x02\x00'
    # # Read Back Data:
    # smu = b"\x02\x00\x00\x01\x04\x00\x02\x00\x00b\x00\x00'\xb8`\xb4"
    # display_register_information("smu", smu)
