# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.
"""Classes and functions to connect to, and interact with `board_cfg_status` VHDL library based registers.

.. important::

   Requires memory mapped :obj:`dict` imported from :mod:`rdma_control.RDMA_REGISTERS` and helper functions
   imported from: :mod:`rdma_control.rdma_register_helpers`.

   :mod:`rdma_control.RDMA_REGISTERS` is generated from XML2VHDL output, regenerated at FPGA synthesis time. Please
   ensure the latest version is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure compatibility with the
   register map in the current FPGA bitstream.

"""
try:
    from rdma_control.RDMA_REGISTERS import *
    from rdma_control.rdma_register_helpers import *

except ModuleNotFoundError:
    from RDMA_REGISTERS import *
    from rdma_register_helpers import *


class BoardCfgStatus(object):
    """Class to manage and interact with `board_cfg_status` VHDL library memory mapped registers.

    Args:
        rdma_ctrl_iface (:obj:`rdma_control.RdmaUdp`): A configured connection to communicate with the `RDMA` `UDP`
            Ethernet interface.

    Attributes:
        fpga_fw_version (:obj:`str`): FPGA firmware version number, stored in :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_SRC_VERSION`.
        fpga_fw_build_date (:obj:`str`): FPGA firmware build date, stored in :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_BUILD_DATE`.
        fpga_fw_build_time (:obj:`str`): FPGA firmware build time, stored in :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_BUILD_TIME`.
        fpga_dna (:obj:`str`): The :func:`hex()` representation of the FPGA DNA, stored in:
            :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_DNA_0`,
            :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_DNA_1`, and
            :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_DNA_2`.
        fpga_fw_git_hash (:obj:`str`): The :func:`hex()` representation of the 32 bit git hash for current FPGA firmware build.
        scratch_regs (:obj:`list` of :obj:`int`): Representation of the FPGA DNA, stored in:
            :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_SCRATCH_1`,
            :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_SCRATCH_2`,
            :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_SCRATCH_3`, and
            :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_SCRATCH_4`.

    """
    def __init__(self, rdma_ctrl_iface):
        self._rdma_ctrl_iface = rdma_ctrl_iface
        self.fpga_fw_version = self.read_fpga_fw_version()
        self.fpga_fw_build_date, self.fpga_fw_build_time = self.read_fpga_build_info()
        self.fpga_dna = self.read_fpga_dna()
        self.fpga_fw_git_hash = self.read_fpga_fw_git_hash()
        self.scratch_regs = self.read_scratch_regs(size=4)


    def read_fpga_fw_version(self):
        """Performs an `RDMA` read to retrieve the FPGA version number.

        Returns:
            :obj:`str`: in the form: `v<major>.<minor>.<micro>`.
        """
        fw_version = self._rdma_ctrl_iface.udp_rdma_read(address=BOARD_BUILD_INFO_SRC_VERSION['addr'],
                                                         burst_len=1, cmd_no=0,
                                                         comment=BOARD_BUILD_INFO_SRC_VERSION['description'])
        return decode_fw_version(fw_version, as_str=True)


    def read_fpga_build_info(self):
        """Performs an `RDMA` read to retrieve the FPGA firmware build date and time.

        Returns:
            :obj:`tuple`: A :obj:`tuple`: containing: :obj:`str`, :obj:`str`.
            - (year <:obj:`int`>, month <:obj:`int`>, day <:obj:`int`>), (hour <:obj:`int`>, minutes <:obj:`int`>, seconds <:obj:`int`>).
            - (`"<YYYY>-<MM>-<DD>"`, `"<HH>:<MM>:<SS>"`).
        """
        build_info = self._rdma_ctrl_iface.udp_rdma_read(address=BOARD_BUILD_INFO_BUILD_DATE['addr'],
                                                         burst_len=2, cmd_no=0,
                                                         comment=BOARD_BUILD_INFO_BUILD_DATE['description'])
        return decode_build_info(build_info, as_str=True)


    def read_fpga_dna(self):
        """Performs an `RDMA` read to retrieve the FPGA DNA identifier.

        Returns:
            :obj:`str`: Hex representation of the FPGA DNA in the form: `0x<DNA>`.
        """
        dna = self._rdma_ctrl_iface.udp_rdma_read(address=BOARD_BUILD_INFO_DNA_0['addr'],
                                                  burst_len=3, cmd_no=0,
                                                  comment=BOARD_BUILD_INFO_DNA_0['description'])
        return construct_fpga_dna(dna, full=False)


    def get_info_header(self):
        """Constructs and returns a header containing all the build information.

        Useful for info messages and debugging systems.

        Returns:
            :obj:`str`: In the form: `[<DNA>|<FIRMWARE VERSION>|<BUILD DATE>>|<BUILD TIME>>]`.
        """
        return f"[{self.fpga_dna}|{self.fpga_fw_version}|{self.fpga_fw_build_date}|{self.fpga_fw_build_time}]"


    def read_fpga_fw_git_hash(self):
        """Performs an `RDMA` read to retrieve the FPGA firmware git hash.

        Returns:
            (:obj:`str`): The :func:`hex()` representation of the 32 bit git hash for current FPGA firmware build.
        """
        git_hash = self._rdma_ctrl_iface.udp_rdma_read(address=BOARD_BUILD_INFO_GIT_HASH['addr'],
                                                         burst_len=1, cmd_no=0,
                                                         comment=BOARD_BUILD_INFO_GIT_HASH['description'])
        return f"0x{git_hash[0]:X}"


    def get_fpga_fw_version(self):
        """Gets the FPGA firmware version without re-reading from the `RDMA` interface.

        Returns:
            :obj:`str`: in the form: `"v<major>.<minor>.<micro>"`.
        """
        return self.fpga_fw_version


    def get_fpga_build_date(self):
        """Gets the FPGA firmware build date without re-reading from the `RDMA` interface.

        Returns:
            :obj:`str`: in the form: `"<YYYY>-<MM>-<DD>"`.
        """
        return self.fpga_fw_build_date


    def get_fpga_build_time(self):
        """Gets the FPGA firmware build time without re-reading from the `RDMA` interface.

        Returns:
            :obj:`str`: in the form: `"<HH>:<MM>:<SS>"`.
        """
        return self.fpga_fw_build_time


    def get_fpga_dna(self):
        """Gets the FPGA DNA identifier without re-reading from the `RDMA` interface.

        Returns:
            :obj:`str`: The :func:`hex()` representation of the FPGA DNA.
        """
        return self.fpga_dna


    def get_fpga_fw_git_hash(self):
        """Gets the FPGA firmware git hash without re-reading from the `RDMA` interface.

        Returns:
            (:obj:`str`): The :func:`hex()` representation of the 32 bit git hash for current FPGA firmware build.
        """
        return self.fpga_fw_git_hash


    def read_scratch_regs(self, size=4):
        """Performs an `RDMA` read to retrieve the values from *n* consecutive scratch register(s).

        .. note::

           The scratch registers are not connected to any down-stream logic, so it is safe to read and write to
           these registers without impacting design functionality.

        Args:
            size (:obj:`int`): Number of consecutive scratch resisters to read from. Default: `4`.

        Returns:
            :obj:`list` of :obj:`int`: where each element of the :obj:`list` is the corresponding value from the
            scratch register.
        """
        scratches = self._rdma_ctrl_iface.udp_rdma_read(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                                        burst_len=size, cmd_no=0,
                                                        comment=BOARD_BUILD_INFO_SCRATCH_1['description'])
        return scratches


    def write_scratch_regs(self, wr_d, max_size=4):
        """Performs an `RDMA` write to store the values in the scratch register(s).

        .. note::

           The scratch registers are not connected to any down-stream logic, so it is safe to read and write to
           these registers without impacting design functionality.

        Args:
            wr_d (:obj:`list` of :obj:`str`): where each element of the :obj:`list` is the corresponding value to
                block write to the scratch register(s), up to a maximum writes defined by :attr:`max_size`.
            max_size (:obj:`int`0): Maximum number of consecutive scratch resisters supported. Default: `4`.

        Returns:
            Nothing.
        """
        capped_rw_d = wr_d[0:max_size - 1] if len(wr_d) > max_size else wr_d
        self._rdma_ctrl_iface.udp_rdma_write(address=BOARD_BUILD_INFO_SCRATCH_1['addr'],
                                             data=capped_rw_d, burst_len=len(capped_rw_d), cmd_no=0,
                                             comment=BOARD_BUILD_INFO_SCRATCH_1['description'])


def decode_fw_version(fw_version, as_str=False):
    """Function to decode firmware version stored in a single 32 bit register.

    Firmware version is defined using ``<MAJOR>.<MINOR>.<MICRO>`` notation, and extracted from the following
    XML2VHDL register :obj:`dict` reference(s):

    - :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_SRC_VERSION`

    Args:
        `fw_version` (:obj:`int`) or (:obj:`list` of :obj:`int`): firmware version (returned from hardware firmware
            single register read). The first element of a :obj:`list` will be used.
        `as_str` (:obj:`bool`, optional): return as formatted string instead of :obj:`tuple`. Default: ``False``.

    If :attr:`as_str` is ``True`` a fully constructed :obj:`str` in the form: `v<major>.<minor>.<micro>` will be
    returned instead of :obj:`tuple`.

    Returns:
        :obj:`tuple`: A :obj:`tuple` containing: (:obj:`int`, :obj:`int, :obj:`int``) if :attr:`as_str` is `False` otherwise a
        :obj:`str`  in the form: `v<major>.<minor>.<micro>`.
            - (major <:obj:`int`>, minor <:obj:`int`>, micro <:obj:`int`>)
            - `v<major>.<minor>.<micro>`
    """
    if isinstance(fw_version, list):
        fw_version = fw_version[0]

    fw_version_micro = decode_field(BOARD_BUILD_INFO_SRC_VERSION, 'MICRO', fw_version)
    fw_version_minor = decode_field(BOARD_BUILD_INFO_SRC_VERSION, 'MINOR', fw_version)
    fw_version_major = decode_field(BOARD_BUILD_INFO_SRC_VERSION, 'MAJOR', fw_version)

    if as_str:
        return f"v{fw_version_major}.{fw_version_minor}.{fw_version_micro}"
    else:
        return fw_version_major, fw_version_minor, fw_version_micro


def decode_build_info(build_info, as_str=False):
    """Function to decode firmware build date and time stored in a two consecutive 32 bit registers.

    Firmware build date is defined using `<YYYY>-<MM>-<DD>` notation and build time is defined using `<HH>:<MM>:<SS>`
    notation, and extracted from the following XML2VHDL register :obj:`dict` reference(s):

    - :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_BUILD_DATE`
    - :const:`rdma_control.RDMA_REGISTERS.BOARD_BUILD_INFO_BUILD_TIME`

    Args:
        build_info (:obj:`list` of :obj:`int`): first element is date, second is time (returned from hardware firmware
            register block read *<size=2>*).
        as_str (:obj:`bool`, optional): return a :obj:`tuple` of formatted :obj:`str` instead of
            :obj:`tuple` of :obj:`tuple`. Default: `False`.

    Returns:
        :obj:`tuple`: A :obj:`tuple` containing: (:obj:`tuple`, :obj:`tuple`) if :attr:`as_str` is `False` otherwise a
        :obj:`tuple` containing: (:obj:`str`, :obj:`str`).
            - (year <:obj:`int`>, month <:obj:`int`>, day <:obj:`int`>), (hour <:obj:`int`>, minutes <:obj:`int`>, seconds <:obj:`int`>).
            - (`"<YYYY>-<MM>-<DD>"`, `"<HH>:<MM>:<SS>"`).
    """
    fw_build_date = build_info[0]
    fw_build_time = build_info[1]
    year = hex(decode_field(BOARD_BUILD_INFO_BUILD_DATE, 'YEAR', fw_build_date))[2:].zfill(4)
    month = hex(decode_field(BOARD_BUILD_INFO_BUILD_DATE, 'MONTH', fw_build_date))[2:].zfill(2)
    day = hex(decode_field(BOARD_BUILD_INFO_BUILD_DATE, 'DAY', fw_build_date))[2:].zfill(2)
    hour = hex(decode_field(BOARD_BUILD_INFO_BUILD_TIME, 'HOUR', fw_build_time))[2:].zfill(2)
    minute = hex(decode_field(BOARD_BUILD_INFO_BUILD_TIME, 'MINUTE', fw_build_time))[2:].zfill(2)
    seconds = hex(decode_field(BOARD_BUILD_INFO_BUILD_TIME, 'SECONDS', fw_build_time))[2:].zfill(2)

    build_date_str = f"{year}-{month}-{day}"
    build_time_str = f"{hour}:{minute}:{seconds}"
    if as_str:
        return build_date_str, build_time_str
    else:
        return (year, month, day), (hour, minute, seconds)


def construct_fpga_dna(dna, full=False):
    """Takes a :obj:`list` containing slices of complete FPGA DNA and returns a single hex string.

    Operates on *N* 32 bit registers.

    Args:
        dna (:obj:`list` of :obj:`int`): each element is a 32 bit slice of the complete FPGA DNA (returned from
            hardware firmware register block read <size=\ *N*\ >).
        full (:obj:`bool`, optional): Include zero padding in generated output :obj:`str`. Default: `False`.

    Returns:
        :obj:`str`: Fully constructed FPGA DNA as hex string.
    """
    dna.reverse()
    dna_str = ''
    if isinstance(dna, list):
        for w in dna:
            dna_str += f"{w:08X}"
    if full:
        return '0x' + dna_str
    else:
        return '0x' + dna_str.lstrip('0')
