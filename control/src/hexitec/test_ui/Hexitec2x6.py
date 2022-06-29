"""
HexitecFEM for Hexitec ODIN control.

Christian Angelsen, STFC Detector Systems Software Group, 2019.
"""

from RdmaUDP import RdmaUDP


class Hexitec2x6():
    """
    Hexitec 2x6 class.

    Test we can access scratch registers in the KinteX FPGA.
    """

    def __init__(self, debug=False):
        self.debug = debug
        # Control IP addresses
        self.server_ctrl_ip_addr = "10.0.3.1" # Network card
        self.camera_ctrl_ip_addr = "10.0.3.2" # Hexitec 2x6 interface
        self.x10g_rdma = None

    def __del__(self):
        self.x10g_rdma.close()

    def connect(self):
        # # SRC UDP Port: 61648
        # # DST UDP Port: 61649
        # write_axi 0x2002C 0xF0D1F0D0
        self.x10g_rdma = RdmaUDP(self.server_ctrl_ip_addr, 61649, self.server_ctrl_ip_addr, 61648,
                                 self.camera_ctrl_ip_addr, 61648, 2000000, 9000, 20, self.debug)
        self.x10g_rdma.setDebug(self.debug)
        self.x10g_rdma.ack = True
        return self.x10g_rdma.error_OK

    def read_scratch_registers(self):
        # self.x10g_rdma.write(0x8030, 0xAAA00555, "New Scratch Register1 value")
        # Read the Scratch registers:
        scratch0 = self.x10g_rdma.read(0x00008030, 'Read Scratch Register 1')
        print("Scratch: 0x{0:08x}".format(scratch0))
        # scratch1 = self.x10g_rdma.read(0x00008038, 'Read Scratch Register 2')
        # scratch2 = self.x10g_rdma.read(0x0000803C, 'Read Scratch Register 3')
        # print("Scratch: 0x{0:08x} {1:08x} {2:08x}".format(scratch2, scratch1, scratch0))

    def read_fpga_dna_registers(self):
        # Read the three DNA registers:
        fpga_dna0 = self.x10g_rdma.read(0x0000800C, 'Read FPGA DNA part 1')
        fpga_dna1 = self.x10g_rdma.read(0x00008010, 'Read FPGA DNA part 2')
        fpga_dna2 = self.x10g_rdma.read(0x00008014, 'Read FPGA DNA part 3')
        print("FPGA DNA: 0x{0:08x} {1:08x} {2:08x}".format(fpga_dna2, fpga_dna1, fpga_dna0))

    def disconnect(self):
        self.x10g_rdma.close()


if __name__ == '__main__':  # pragma: no cover

    hxt = Hexitec2x6(True)
    hxt.connect()
    hxt.read_scratch_registers()
    # hxt.read_fpga_dna_registers()
    hxt.disconnect()
    print("All done!")