# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.
"""Classes and functions to connect to, and interact with aSpect VSR modules in Hexitec 2x\ `N` based systems.

.. important::

   Requires memory mapped :obj:`dict` imported from the following modules:
    - :mod:`rdma_control.RDMA_REGISTERS`,
    - :mod:`rdma_control.VSR_FPGA_REGISTERS`
   Also requires the corresponding helper functions imported from :mod:`rdma_control.rdma_register_helpers` to access
   and modify the dictionary entries defining the registers.

   :mod:`rdma_control.RDMA_REGISTERS` and :mod:`rdma_control.VSR_FPGA_REGISTERS` are generated from
   `XML2VHDL` output, regenerated at FPGA synthesis time. Please
   ensure the latest version is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure compatibility with the
   register map in the current FPGA bitstream.
"""
import time
import sys

try:
    from rdma_control.RDMA_REGISTERS import *
    from rdma_control.VSR_FPGA_REGISTERS import *
    from rdma_control.rdma_register_helpers import *
except ModuleNotFoundError:
    from RDMA_REGISTERS import *
    from VSR_FPGA_REGISTERS import *
    from rdma_register_helpers import *


def get_vsr_cmd_char(code):
    """Converts operation into corresponding VSR command character.

        Args:
            code (:obj:`str`): from:
                `"start"`, `"end"`, `"resp"`, `"bcast"`, `"whois"`, `"get_env"`, '"enable"', '"disable"',
                `"adc_dac_ctrl"`, `"fpga_reg_write"`, `"fpga_reg_read"`, `"fpga_reg_set_bit"`, `"fpga_reg_clr_bit"`,
                `"fpga_reg_write_burst"`, `"fpga_reg_write_stream"`, `"fpga_active_reg_readback"`, `"write_dac_values"`,
                `"write_dac_values"`

        Returns:
            :obj:`int`: cmd/character to place in VSR UART command sequences, can also be used to validate command responses.
        """
    if code.lower() == "start":
        return 0x23
    elif code.lower() == "end":
        return 0x0D
    elif code.lower() == "resp":
        return 0x2A
    elif code.lower() == "bcast":
        return 0xFF
    elif code.lower() == "whois":
        return 0xF7
    elif code.lower() == "get_pwr":
        return 0x50
    elif code.lower() == "get_env":
        return 0x52
    elif code.lower() == "enable":
        return 0xE3
    elif code.lower() == "disable":
        return 0xE2
    elif code.lower() == "adc_dac_ctrl":
        return 0x55
    elif code.lower() == "fpga_reg_write":
        return 0x40
    elif code.lower() == "fpga_reg_read":
        return 0x41
    elif code.lower() == "fpga_reg_set_bit":
        return 0x42
    elif code.lower() == "fpga_reg_clr_bit":
        return 0x43
    elif code.lower() == "fpga_reg_write_burst":
        return 0x44
    elif code.lower() == "fpga_reg_write_stream":
        return 0x46
    elif code.lower() == "fpga_active_reg_readback":
        return 0x51
    elif code.lower() == "write_dac_values":
        return 0x54
    elif code.lower() == "write_adc_values":
        return 0x53
    else:
        return 0x23


def convert_from_ascii(d):
    """Converts an ASCII representation of a :obj:`hex` string into its :obj:`int` equivalent.

    Args:
        d (:obj:`str`): An ASCII representation of an :obj:`int` to convert.

    Returns:
        :obj:`int`
    """
    return int("".join([chr(c) for c in d]), 16)


def convert_to_ascii(d, zero_pad=False):
    """Converts an integer into a :obj:`list` of :obj`int` ASCII representations of the :obj:`hex` equivalent.

    Args:
        d (:obj:`int`): Value to convert.
        zero_pad (:obj:`bool`, optional): Add ASCII zero padding to left-hand side of generated :obj:`'list.
            Default: `False`.

    Returns:
        :obj:`list` of :obj:`int`: Values of ASCII equivalents, for each of the :obj:`hex` characters required
        to represent the :attr:`d`.
    """
    unpadded = [ord(c) for c in hex(d).upper()[2:]]
    if zero_pad:
        return zero_pad_ascii_byte(unpadded)
    else:
        return unpadded


def zero_pad_ascii_byte(ascii_byte):
    # Zero (ASCII) pad if returned ASCII conversion list length is 1:
    if len(ascii_byte) == 1:
        ascii_byte = [0x30, *ascii_byte]
    return ascii_byte


def set_row_column_mask(all=True, max_elements=80, reg_size=8):
    """Generates a mask to set the selected elements of a Row or Column.

    Args:
        all (:obj:`bool`, optional): Sets all bits in the generated mask. Default: `True`.
        max_elements (:obj:`int`, optional): number of elements in the generated mask. Default: `80`.
        reg_size (:obj:`int`, optional): size, in bits, of the register(s) storing masked values. Default: `8` bit.
    Returns:
        :obj:`list` of :obj:`int` of values, where each element in the :obj:`list` represents the masked values
        of each of the 8 bit registers required to describe the complete mask.
    """
    tmp_list = list()
    full_reg_mask = (2 ** reg_size) - 1
    if all:
        for i in range(0, max_elements // reg_size):
            tmp_list.append(full_reg_mask)
    return tmp_list

def clr_row_column_mask(all=True, max_elements=80, reg_size=8):
    """Generates a mask to clear the selected elements of a Row or Column.

    Args:
        all (:obj:`bool`, optional): Sets all bits in the generated mask. Default: `True`.
        max_elements (:obj:`int`, optional): number of elements in the generated mask. Default: `80`.
        reg_size (:obj:`int`, optional): size, in bits, of the register(s) storing masked values. Default: `8` bit.
    Returns:
        :obj:`list` of :obj:`int` of values, where each element in the :obj:`list` represents the masked values
        of each of the 8 bit registers required to describe the complete mask.
    """
    tmp_list = list()
    full_reg_mask = 0
    if all:
        for i in range(0, max_elements // reg_size):
            tmp_list.append(full_reg_mask)
    return tmp_list

def unpack_data_for_vsr_write(dat, mask=0xFFF, nof_bytes=2):
    """Unpacks words, greater than 1 byte and unpacks them into multiple bytes for writing to the VSR.

    Args:
        dat (:obj:`int`): Data to unpack.
        mask (:obj:`int`, optional): Mask to limit the number of ASCII characters to unpack data to.
            Default: `0xFFF`, 12 bits.
        nof_bytes (:obj:`int`): Number of bytes to unpack :argument:`dat` to. Default: `2`.

    Returns:
        :obj:`list` of ASCII coded hex values for :argument:`dat`.
    """
    unpacked_dat = list()
    for i in range(0, bytes):
        shifted = ((dat & mask) >> (i * 8)) & 0xFF
        unpacked_dat = [*(convert_to_ascii(shifted, zero_pad=True)), *unpacked_dat]
    return unpacked_dat

class VsrAssembly(object):
    """Class for globally controlling all VSR modules on a Hexitec assembly.

    .. important::

       Requires memory mapped :obj:`dict` imported from the following modules:
        - :mod:`rdma_control.RDMA_REGISTERS`,
        - :mod:`rdma_control.VSR_FPGA_REGISTERS`
       Also requires the corresponding helper functions imported from :mod:`rdma_control.rdma_register_helpers` to access
       and modify the dictionary entries defining the registers.

       :mod:`rdma_control.RDMA_REGISTERS` and :mod:`rdma_control.VSR_FPGA_REGISTERS` are generated from
       `XML2VHDL` output, regenerated at FPGA synthesis time. Please
       ensure the latest version is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure compatibility with the
       register map in the current FPGA bitstream.

    .. warning::

       Not supplying a :attr:`addr_mapping` :obj:`dict`, :class:`VsrAssembly` will perform a :meth:`VsrAssembly.lookup` to
       determine the configuration of the attached system. This is a time-consuming operation so should be avoided
       whenever possible by supplying a pre-determined configuration matching the target system.

    Args:
        rdma_ctrl_iface (:obj:`rdma_control.RdmaUdp`): A configured connection to communicate with the `RDMA` `UDP`
            Ethernet interface.
        slot (:obj:`int`, optional): Slot should only be set via child class(es). Leave set to `0`. Default: `0`.
        init_time(:obj:`int`, optional): Time, in seconds, to wait for VSR to power up and FPGA to initialise.
            Default: `15` seconds.
        addr_mapping (:obj:`dict`, optional): Key/value pairs cross-referencing :attr:`slot` with hardware address of the
            corresponding VSR module. Default: `None`. If an address mapping is not supplied the :obj:`VsrAssembly` will
            perform a :meth:`VsrAssembly.lookup` to determine the configuration of the attached system.

    Attributes:
        addr_mapping (:obj:`dict`): A copy of the address mapping configuration, either provided or determined at
            initialisation.
        slot (:obj:`int`): Slot number. Set to '0' for global addressing and control.
        addr (:obj:`int`): Hardware address of VSR module, hard-coded on each VSR module.
    """
    def __init__(self, rdma_ctrl_iface, slot=0, init_time=15, addr_mapping=None):
        self._rdma_ctrl_iface = rdma_ctrl_iface
        self.slot = slot
        self.init_time = init_time
        if addr_mapping is None:
            self.addr_mapping = self.lookup(init_time=self.init_time)
        else:
            self.addr_mapping = addr_mapping
        self.addr = self.get_addr()
        self._adc_enabled_flag = False
        self._dac_enabled_flag = False

    def __del__(self):
        pass
        # print(f"(Slot: {self.slot} address: 0x{self.addr:X}) Wrapping up, NOT disabling modules/HV")
        # self.hv_disable()
        # self.disable_module()


    def get_slot(self):
        """Returns the slot number, hosting the VSR module.

        .. note::

           :attr:`slot` = 0 has a special meaning, where :attr:`addr` will be set to the VSR broadcast address.
           Otherwise, positional location of the VSR module (indexed from '1'). Used by the host FPGA to control power
           and high-voltage, and to determine which :mod:`rdma_control.RDMA_REGISTERS` to associate with the VSR module.

        Returns:
            :obj:`int`:
        """
        return self.slot

    def get_addr(self):
        """Returns the hardware address of the VSR.

        .. note::

            :attr:`slot` = `0` has a special meaning, where :attr:`addr` will be set to the VSR broadcast address.
            Otherwise, the physical VSR address, hard-coded onto the VSR module.

        Returns:
            :obj:`int`:
        """
        addr = get_vsr_cmd_char("bcast") if self.slot == 0 else self.addr_mapping[self.slot]
        return addr

    def set_init_time(self, init_time):
        """Sets the initialisation delay for the VSR.

        Args:
            init_time(:obj:`int`): Time, in seconds, to wait for VSR to power up and FPGA to initialise.

        Returns:
            Nothing.
        """
        self.init_time = init_time

    def _fpga_reg_read(self, fgpa_reg_addr, cmd_no=0):
        """Constructs a VSR FPGA register read command and transmits the request via the UART connection to the VSR module.

        Args:
            fgpa_reg_addr (:obj:`int`): Single FPGA register address to read from.

        Returns:
            :obj:`int`: Value read from :attr:`fgpa_reg_addr`.
        """
        ascii_reg_addr = convert_to_ascii(fgpa_reg_addr, zero_pad=True)
        read_cmd = get_vsr_cmd_char("fpga_reg_read")
        self._uart_write(self.addr, read_cmd, ascii_reg_addr, cmd_no=cmd_no)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        if resp:
            resp = self._check_uart_response(resp)
            rd_data = convert_from_ascii(resp[0:2])
            return rd_data
        else:
            print(f"[ERROR]: No response reading from VSR FPGA Register: {hex(fgpa_reg_addr)}")
            return 0

    def _fpga_reg_write(self, fpga_reg_addr, wr_data, cmd_no=0):
        """Constructs a VSR FPGA register write command and transmits the request via the UART connection to the VSR module.

        Args:
            fpga_reg_addr (:obj:`int`): Single FPGA register address to write to.
            wr_data (:obj:`int`): Byte, to write.

        Returns:
            Nothing.
        """
        wr_cmd = list()
        wr_cmd.extend(convert_to_ascii(fpga_reg_addr, zero_pad=True))
        wr_cmd.extend(convert_to_ascii(wr_data, zero_pad=True))
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_write"), wr_cmd, cmd_no=cmd_no)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)

    def _fpga_reg_set_bit(self, fgpa_reg_addr, mask, cmd_no=0):
        """Constructs a VSR FPGA register set bit command and transmits the request via the UART connection to the VSR module.

        Args:
            fgpa_reg_addr (:obj:`int`): Single FPGA register address to write to.
            mask (:obj:`int`): Mask to select bits in the register to set, unmasked bits will remain unchanged.
        Returns:
            Nothing.
        """
        wr_cmd = list()
        wr_cmd.extend(convert_to_ascii(fgpa_reg_addr, zero_pad=True))
        wr_cmd.extend(convert_to_ascii(mask, zero_pad=True))
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_set_bit"), wr_cmd, cmd_no=cmd_no)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)

    def _fpga_reg_clr_bit(self, fpga_reg_addr, mask, cmd_no=0):
        """Constructs a VSR FPGA register clear bit command and transmits the request via the UART connection to the VSR module.

        Args:
            fpga_reg_addr (:obj:`int`): Single FPGA register address to write to.
            mask (:obj:`int`): Mask to select bits in the register to clear, unmasked bits will remain unchanged.
        Returns:
            Nothing.
        """
        wr_cmd = list()
        wr_cmd.extend(convert_to_ascii(fpga_reg_addr, zero_pad=True))
        wr_cmd.extend(convert_to_ascii(mask, zero_pad=True))
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_clr_bit"), wr_cmd, cmd_no=cmd_no)
        # flush the response from the UART Rx FIFO:
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)

    def _fpga_reg_write_burst(self, fpga_reg_addr, wr_data, cmd_no=0):
        """Constructs a VSR FPGA register write burst command and transmits the request via the UART connection to the VSR module.

        .. note::

           Maximum burst size is `125`.

        Args:
            fpga_reg_addr (:obj:`int`): FPGA register address to start write burst from.
            wr_data (:obj:`list` of :obj:`int`): Bytes, to burst write.
        Returns:
            Nothing.
        """
        wr_cmd = list()
        wr_cmd.extend(convert_to_ascii(fpga_reg_addr, zero_pad=True))
        [wr_cmd.extend(convert_to_ascii(d, zero_pad=True)) for d in wr_data]
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_write_burst"), wr_cmd, cmd_no=cmd_no)
        # flush the response from the UART Rx FIFO:
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)

    def _fpga_reg_write_stream(self, addr_data_pairs, cmd_no=0):
        """Constructs a VSR FPGA register write stream command and transmits the request via the UART connection to the VSR module.

        Args:
            addr_data_pairs (:obj:`dict` of :obj:`int` key and :obj:`int` value pairs): where the key is the FPGA
                register address and the value is the data to write to the key's address.

        Returns:
            Nothing.
        """
        wr_dat = list()
        wr_cmd = get_vsr_cmd_char("fpga_reg_write_stream")
        wr_dat.extend(convert_to_ascii(len(addr_data_pairs), zero_pad=True))
        for k, v in addr_data_pairs.items():
            wr_dat.extend(convert_to_ascii(k, zero_pad=True))
            wr_dat.extend(convert_to_ascii(v, zero_pad=True))
        self._uart_write(self.addr, wr_cmd, wr_dat, cmd_no=cmd_no)
        # flush the response from the UART Rx FIFO:
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)

    def _fpga_change_active_reg_readout_fpga_reg_write(self, fpga_reg_addr, cmd_no=0):
        """Constructs a VSR change active FPGA register readback command and transmits the request via the UART connection to the VSR module.

        Args:
            fpga_reg_addr (:obj:`int`): Single FPGA register address to change active readback to.

        Returns:
            Nothing.
        """
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_active_reg_readback"),
                         convert_to_ascii(fpga_reg_addr, zero_pad=True), cmd_no=cmd_no)
        # flush the response from the UART Rx FIFO:
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)

    def _uart_write(self, vsr_a, vsr_cmd, wr_d, cmd_no=0):
        """Wraps UART Tx data with a VSR command header for writing to aSpect based VSR modules.
        """
        wr_cmd = list()
        wr_cmd.append(get_vsr_cmd_char("start"))
        wr_cmd.append(vsr_a)
        wr_cmd.append(vsr_cmd)

        for d in wr_d:
            wr_cmd.append(d)
        wr_cmd.append(get_vsr_cmd_char("end"))
        # print(f"[DEBUG]: rdmaVsrMod._uart_write: {[ hex(c) for c in wr_cmd ]}")
        self._rdma_ctrl_iface.uart_write(wr_cmd, cmd_no=cmd_no)

    def _get_status(self, vsr_mod=None, hv=False, all_vsrs=False, cmd_no=0):
        """Returns status of power/high-voltage enable signals for the selected VSR(s).

        Args:
            vsr_mod (:obj:`int`, optional): VSR module to control, indexed from 1. If not set, will use the :attr:`slot`
                to set the VSR module number. Default: `None`.
            hv (:obj:`bool`, optional): Report High Voltage on status, otherwise report power on status to the VSR.
                Default: `False`.
            all_vsrs (:obj:`bool`, optional): Report on all VSR modules. Default: `False`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`list`: Status of requested VSR enable signal(s), represented as :obj:`str` with the values `"ENABLED"`
            or `"DISABLED"`.
        """
        # use the VSR_EN field to set the total number of VSR modules in the system:
        vsr_en_field = get_field(HEXITEC_2X6_VSR_CTRL, 'VSR_EN')
        nof_modules = vsr_en_field['nof_bits']
        en_mask_offset = vsr_en_field['shiftr']
        vsr_status = list()
        hv_status = list()

        if all_vsrs:
            vsr_mod = range(1, nof_modules + 1)
        elif vsr_mod is not None:
            vsr_mod = [vsr_mod]
        else:
            if self.slot > nof_modules:
                print(
                    f"[ERROR]: Requested VSR module: <{self.slot}> exceeds total number of modules available: <{nof_modules}>")
                return 0
            else:
                vsr_mod = [self.slot]

        vsr_ctrl_reg = self._rdma_ctrl_iface.udp_rdma_read(HEXITEC_2X6_VSR_CTRL['addr'],
                                                           burst_len=1, cmd_no=cmd_no,
                                                           comment=HEXITEC_2X6_VSR_CTRL['description'])[0]
        vsr_en = decode_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg)
        vsr_hv_en = decode_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg)

        for vsr in vsr_mod:
            mod_stat = "ENABLED" if vsr_en & (1 << (vsr - 1)) else "DISABLED"
            mod_hv_en = "ENABLED" if vsr_hv_en & (1 << (vsr - 1)) else "DISABLED"
            vsr_status.append(mod_stat)
            hv_status.append(mod_hv_en)

        return hv_status if hv else vsr_status

    def get_module_status(self, cmd_no=0):
        """Returns status of VSR enable signals for the selected VSR(s).

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`list`: Status of requested VSR enable signal(s), represented as :obj:`str` with the values `"ENABLED"
            or `"DISABLED"`.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._get_status(hv=False, all_vsrs=all_vsrs, cmd_no=cmd_no)

    def get_hv_status(self, cmd_no=0):
        """Returns status of high-voltage enable signals for the selected VSR(s).

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`list`: Status of requested VSR enable signal(s), represented as :obj:`str` with the values `"ENABLED"
            or `"DISABLED"`.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._get_status(hv=True, all_vsrs=all_vsrs, cmd_no=cmd_no)

    def who_is(self, cmd_no=0):
        """Sends a VSR `who_is?` command.

        Will check the response to see of the Power/HV module is connected. The Power/HV response and end of `who_is?`
        character will be stripped from the response.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`list`: of VSR :obj:`int`: Addresses of enabled VSR modules returned by `who_is?` command.
        """
        vsr_d  = list() # empty VSR data list to pass to: :meth:`_vsr_uart_write()`
        hv_power_module_id = [0xc0, 0x31]
        whois_end_char = 0x34
        vsr_addrs = list()
        self._uart_write(get_vsr_cmd_char("bcast"), get_vsr_cmd_char("whois"), vsr_d, cmd_no=cmd_no)
        time.sleep(5)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        # check response:
        if resp[-2:] == hv_power_module_id:
            if len(resp) > len(hv_power_module_id):
                stripped_resp = resp[:-2]
                if stripped_resp[-1] == whois_end_char:
                    vsr_addrs = stripped_resp[:-1]
                else:
                    print(f"[ERROR]: VSR address response: <FAILED>")
        else:
            print(f"[ERROR]: Power/HV module response: <FAILED>")
        return vsr_addrs

    def lookup(self, init_time=15, cmd_no=0):
        """Cycle through each possible VSR module slot and return the VSR address for the module in each slot.

        Each VSR module has its address hard-coded on the VSR module. The position of VSRs isn't guaranteed between
        hardware assemblies. This routine can be executed once per assembly with the results stored externally.

        Args:
            init_time (:obj:`int`, optional): Time, in seconds, to allow VSR FPGA to initialise. Default: `15` seconds.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`dict`: The hardware configuration of the `Hexitec` assembly. Where the key is the VSR slot idx and the
            value is the :obj:`int` VSR address. Set to `None` if there is no `who_is?` response from the corresponding slot.
        """
        # use the VSR_EN field to set the total number of VSR modules in the system:
        vsr_en_field = get_field(HEXITEC_2X6_VSR_CTRL, 'VSR_EN')
        nof_modules = vsr_en_field['nof_bits']
        vsr_addr_map = dict()
        for v in range(0, nof_modules):
            self._ctrl(vsr_mod=v + 1, op="enable", init_time=init_time, cmd_no=cmd_no)
            self._get_status(vsr_mod=v + 1, cmd_no=cmd_no)
            tmp_addr = self.who_is(cmd_no=cmd_no)
            vsr_addr_map[v+1] = tmp_addr[0] if tmp_addr else None
            self._ctrl(vsr_mod=v + 1, op="disable", init_time=0, cmd_no=cmd_no)
            self._get_status(vsr_mod=v + 1, cmd_no=cmd_no)
        print(f"[INFO]: Address mapping from lookup: {vsr_addr_map}")
        return vsr_addr_map

    def _ctrl(self, vsr_mod=None, all_vsrs=False, op="disable", init_time=15, cmd_no=0):
        """Control the selected VSR modules(s).

        This controls the power and high-voltage enable signals between the FPGA and VSR module slots.

        Args:
            vsr_mod (:obj:`int`, optional): VSR module to control, indexed from 1. If not set, will use the :attr:`slot`
                to set the VSR module number. Default: `None`.
            all_vsrs (:obj:`bool`, optional): Control all VSR modules. Default: `False`.
            op (:obj:`str`, optional): Operation to perform. From: `enable`, `disable`, `hv_enable`, `hv_disable`.
                Default: `disable`.
            init_time(:obj:`int`, optional): Time, in seconds, to wait for VSR to power up and FPGA to initialise.
                Default: `15` seconds.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`: `1` on success, `0` on failure.
        """
        # use the VSR_EN field to set the total number of VSR modules in the system:
        vsr_en_field = get_field(HEXITEC_2X6_VSR_CTRL, 'VSR_EN')
        hv_en_field = get_field(HEXITEC_2X6_VSR_CTRL, 'HV_EN')
        nof_modules = vsr_en_field['nof_bits']

        if self.slot > nof_modules:
            print(f"[ERROR]: Requested VSR module: <{self.slot}> exceeds total number of modules available: <{nof_modules}>")
            return 0

        if all_vsrs:
            en_mask = (2 ** nof_modules) - 1
        elif vsr_mod is not None:
            en_mask = 1 << (vsr_mod - 1)
        else:
            en_mask = 1 << (self.slot - 1)

        vsr_ctrl_reg = self._rdma_ctrl_iface.udp_rdma_read(HEXITEC_2X6_VSR_CTRL['addr'],
                                                           burst_len=1, cmd_no=cmd_no,
                                                           comment=HEXITEC_2X6_VSR_CTRL['description'])[0]
        if op.lower() == "enable":
            vsr_status = decode_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg)
            vsr_status = vsr_status | en_mask
            vsr_ctrl_reg = set_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg, vsr_status)
            self._rdma_ctrl_iface.udp_rdma_write(HEXITEC_2X6_VSR_CTRL['addr'], [vsr_ctrl_reg])
            print(f"[INFO]: Waiting {init_time} second(s) for VSR(s) to initialise...")
            time.sleep(init_time)
        elif op.lower() == "hv_enable":
            vsr_status = decode_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg)
            vsr_status = vsr_status | en_mask
            vsr_ctrl_reg = set_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg, vsr_status)
            self._rdma_ctrl_iface.udp_rdma_write(HEXITEC_2X6_VSR_CTRL['addr'], [vsr_ctrl_reg])
        elif op.lower() == "disable":
            vsr_status = decode_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg)
            vsr_status = vsr_status & ~ en_mask
            vsr_ctrl_reg = set_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg, vsr_status)
            self._rdma_ctrl_iface.udp_rdma_write(HEXITEC_2X6_VSR_CTRL['addr'], [vsr_ctrl_reg])
        elif op.lower() == "hv_disable":
            vsr_status = decode_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg)
            vsr_status = vsr_status & ~ en_mask
            vsr_ctrl_reg = set_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg, vsr_status)
            self._rdma_ctrl_iface.udp_rdma_write(HEXITEC_2X6_VSR_CTRL['addr'], [vsr_ctrl_reg])
        else:
            print(f"[ERROR]: Unsupported operation: {op}")
            return 0
        return 1

    def enable_module(self):
        """Enable power to the VSR module.

        Returns:
            :obj:`int`: The value `1` on success, `0` on failure.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._ctrl(all_vsrs=all_vsrs, op="enable", init_time=self.init_time, cmd_no=0)

    def hv_enable(self):
        """Enable High-Voltage to the VSR module.

        Returns:
            :obj:`int`: The value `1` on success, `0` on failure.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._ctrl(all_vsrs=all_vsrs, op="hv_enable", init_time=0, cmd_no=0)

    def disable_module(self):
        """Disable power to the VSR module.

        Returns:
            :obj:`int`: The value `1` on success, `0` on failure.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._ctrl(all_vsrs=all_vsrs, op="disable", init_time=0, cmd_no=0)

    def hv_disable(self):
        """Disable High-Voltage to the VSR module.

        Returns:
            :obj:`int`: The value `1` on success, `0` on failure.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._ctrl(all_vsrs=all_vsrs, op="hv_disable", init_time=0, cmd_no=0)

    def enable_vsr(self, init_time=15, cmd_no=0):
        """Starts the default power-up/init sequence of VSR module.

        Default values will be written to VSR modules FPGA and the ADC and DAC will be enabled.

        Average picture will be taken and the state-machine will start for continuous readout with dark correction.

        Args:
            init_time (:obj:`int`, optional): wait time, in seconds, to allow each VSR to initialise after being sent
                the `"enable"` command.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        vsr_d = list()  # empty VSR data list to pass to: :meth:`_vsr_uart_write()`
        self._uart_write(self.addr, get_vsr_cmd_char("enable"), vsr_d, cmd_no=cmd_no)
        time.sleep(init_time)

    def disable_vsr(self, cmd_no=0):
        """Stops the state-machine, and disables ADC and DAC, also stops the PLL in the VSR modules FPGA.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        vsr_d = list()  # empty VSR data list to pass to: :meth:`_vsr_uart_write()`
        self._uart_write(self.addr, get_vsr_cmd_char("disable"), vsr_d, cmd_no=cmd_no)

    def _ctrl_converters(self, adc=False, dac=False, cmd_no=0):
        """Controls the VSR modules ADC and DAC.

        Args:
            adc (:obj:`bool`, optional): State to set the ADC. `True` is enabled, `False` is disabled. Default: `False`.
            dac (:obj:`bool`, optional): State to set the DAC. `True` is enabled, `False` is disabled. Default: `False`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        adc_ctrl_bit = 0 if adc else 1
        dac_ctrl_bit = 0 if dac else 1
        ctrl_byte = (dac_ctrl_bit << 1) + adc_ctrl_bit
        self._uart_write(self.addr, get_vsr_cmd_char("adc_dac_ctrl"), [ctrl_byte], cmd_no=cmd_no)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)
        return 1 if resp[0] == ctrl_byte else 0

    def enable_adc(self, cmd_no=0):
        """Enables the VSR module ADC, leaves the DAC unchanged.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=True, dac=self._dac_enabled_flag, cmd_no=cmd_no) == 1:
            self._adc_enabled_flag = True
            return 1
        else:
            return 0

    def enable_dac(self, cmd_no=0):
        """Enables the VSR module DAC, leaves the ADC unchanged.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=self._adc_enabled_flag, dac=True, cmd_no=cmd_no) == 1:
            self._dac_enabled_flag = True
            return 1
        else:
            return 0

    def enable_adc_and_dac(self, cmd_no=0):
        """Enables the VSR module ADC and DAC.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=True, dac=True, cmd_no=cmd_no) == 1:
            self._adc_enabled_flag = True
            self._dac_enabled_flag = True
            return 1
        else:
            return 0

    def disable_adc(self, cmd_no=0):
        """Disables the VSR module ADC, leaves the DAC unchanged.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=False, dac=self._dac_enabled_flag, cmd_no=cmd_no) == 1:
            self._adc_enabled_flag = False
            return 1
        else:
            return 0

    def disable_dac(self, cmd_no=0):
        """Disables the VSR module DAC, leaves the ADC unchanged.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=self._adc_enabled_flag, dac=False, cmd_no=cmd_no) == 1:
            self._dac_enabled_flag = False
            return 1
        else:
            return 0

    def disable_adc_and_dac(self, cmd_no=0):
        """Disables the VSR module ADC and DAC.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=False, dac=False, cmd_no=cmd_no) == 1:
            self._adc_enabled_flag = False
            self._dac_enabled_flag = False
            return 1
        else:
            return 0

    def get_adc_status(self):
        """Gets the current status of the VSR module ADC.

        Returns:
            :obj:`str`: Status of the VSR module ADC, with the values `"ENABLED"` or `"DISABLED"`.
        """
        return "ENABLED" if self._adc_enabled_flag else "DISABLED"

    def get_dac_status(self):
        """Gets the current status of the VSR module DAC.

        Returns:
            :obj:`str`: Status of the VSR module DAC, with the values `"ENABLED"` or `"DISABLED"`.
        """
        return "ENABLED" if self._dac_enabled_flag else "DISABLED"

    def _check_uart_response(self, rx_d):
        """Takes an incoming :obj:`list` of bytes received from the VSR UART and validates the start and end characters.

        Args:
            rx_d (:obj:`list` of :obj:`int`): full byte-by-byte response from VSR UART.

        Returns:
            :obj:`list` of :obj:`int`: Parses :attr:`rx_d` by removing the start of response; address; and end character.
        """
        # d = rx_d
        if rx_d[0] == get_vsr_cmd_char("resp"):
            rx_d = rx_d[1:]
        if rx_d[0] == self.addr:
            rx_d = rx_d[1:]
        if rx_d[-1] == get_vsr_cmd_char("end"):
            rx_d = rx_d[:-2]
        # print(" _check_uart_response, changes   {}  into  {}".format(d, rx_d))
        return rx_d

class VsrModule(VsrAssembly):
    """A child class, which inherits methods and attributes from :class:`rdma_control.VsrAssembly`. Used for describing and controlling individual VSR modules.

    .. important::

       Requires memory mapped :obj:`dict` imported from the following modules:
        - :mod:`rdma_control.RDMA_REGISTERS`,
        - :mod:`rdma_control.VSR_FPGA_REGISTERS`
       Also requires the corresponding helper functions imported from :mod:`rdma_control.rdma_register_helpers` to access
       and modify the dictionary entries defining the registers.

       :mod:`rdma_control.RDMA_REGISTERS` and :mod:`rdma_control.VSR_FPGA_REGISTERS` are generated from
       `XML2VHDL` output, regenerated at FPGA synthesis time. Please
       ensure the latest version is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure compatibility with the
       register map in the current FPGA bitstream.

    .. warning::

       Not supplying a :attr:`addr_mapping` :obj:`dict`, :class:`VsrModule` will perform a :meth:`VsrModule.lookup` to
       determine the configuration of the attached system. This is a time-consuming operation so should be avoided
       whenever possible by supplying a pre-determined configuration matching the target system.

    Args:
        rdma_ctrl_iface (:obj:`rdma_control.RdmaUdp`): A configured connection to communicate with the `RDMA` `UDP`
            Ethernet interface.
        slot (:obj:`int`, optional): Slot index, indexed from `1`, of the VSR module. Default: `1`.
        init_time(:obj:`int`, optional): Time, in seconds, to wait for VSR to power up and FPGA to initialise.
            Default: `15` seconds.
        addr_mapping (:obj:`dict`, optional): Key/value pairs cross-referencing :attr:`slot` with hardware address of the
            corresponding VSR module. Default: `None`. If an address mapping is not supplied the :obj:`VsrModule` will
            perform a :meth:`VsrModule.lookup` to determine the configuration of the attached system.

    Attributes:
        addr_mapping (:obj:`dict`): A copy of the address mapping configuration, either provided or determined at
            initialisation.
        slot (:obj:`int`): Slot number for corresponding VSR module, indexed from '1'.
        addr (:obj:`int`): Hardware address of VSR module, hard-coded on each VSR module.
        rows1_clock (:obj:`int`): A 16 bit :obj:`int` representing the `RowS1 Clock` value. Default: `1`.
        s1sph (:obj:`int`): A 6 bit :obj:`int` representing the `S1Sph` value. Default: `1`.
        sphs2 (:obj:`int`): A 6 bit :obj:`int` representing the `SphS2` value. Default: `6`.
        gain (:obj:`str`): `"high"` or `"low"` `gain`. Default: `"low"`.
        adc_clock_delay (:obj:`int`): A 5 bit :obj:`int` representing the `ADC Clock Delay` value. Default: `2`.
        adc_signal_delay (:obj:`int`): A 8 bit :obj:`int` representing the `ADC Signal Delay` value. Controls the
            F\ :sub:`val` and L\ :sub:`val` delays. Default: `10`.
        sm_vcal_clock (:obj:`int`): A 15 bit :obj:`int` representing the `State-Machine` V\ :sub:`cal` `Clock` value.
            Default: `0`.
        sm_row_wait_clock (:obj:`int`): A 8 bit :obj:`int` representing the `State-Machine Row Wait Clock` value.
            Default: `8`.
        dac_vcal (:obj:`int`): A 12 bit :obj:`int` representing the `DAC` V\ :sub:`cal` value. Default: `0x111`.
        dac_umid (:obj:`int`): A 12 bit :obj:`int` representing the `DAC` U\ :sub:`mid` value. Default: `0x555`.
        dac_hv (:obj:`int`): A 12 bit :obj:`int` representing the `DAC High-Voltage` value. Note that in the
            documentation this field is referred to as `reserve1`. Default: `0x0`.
        dac_det_ctrl (:obj:`int`): A 12 bit :obj:`int` representing the `DAC DET control` value. Default: `0x0`.
        dac_reserve2 (:obj:`int`): A 12 bit :obj:`int` representing the `DAC Reserved` value. Default: `0x8E8`.
        adc_output_phase (:obj:`str`) Output phase of the VSR AD9252 ADC. Default: "540" degrees.
    """
    def __init__(self, rdma_ctrl_iface, slot=1, init_time=15, addr_mapping=None):
        super().__init__(rdma_ctrl_iface, slot=slot, init_time=init_time, addr_mapping=addr_mapping)
        self.rows1_clock = 1
        self.s1sph = 1
        self.sphs2 = 6
        self.gain = "low"
        self.adc_clock_delay = 2
        self.adc_signal_delay = 10
        self.sm_vcal_clock = 0
        self.sm_row_wait_clock = 8
        self.dac_vcal = 0x111
        self.dac_umid = 0x555
        self.dac_hv = 0x0
        self.dac_det_ctrl = 0x0
        self.dac_reserve2 = 0x8E8
        self.set_adc_output_phase("540")

    def _get_env_sensors(self, cmd_no=0):
        vsr_d = list()  # empty VSR data list to pass to: self.uart_write()
        self._uart_write(self.addr, get_vsr_cmd_char("get_env"), vsr_d, cmd_no=cmd_no)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)
        calc_ambient_temp = round(((convert_from_ascii(resp[0:4]) / 2 ** 16) * 175.72) - 46.85, 3)
        calc_humidity = round(((convert_from_ascii(resp[4:8]) / 2 ** 16) * 125) + 6, 3)
        calc_asic1_temp = round(convert_from_ascii(resp[8:12]) * 0.0625, 2)
        calc_asic2_temp = round(convert_from_ascii(resp[12:16]) * 0.0625, 2)
        calc_adc_temp = round(convert_from_ascii(resp[16:20]) * 0.0625, 2)
        return f"{calc_ambient_temp}�C", f"{calc_humidity}%", f"{calc_asic1_temp}�C", f"{calc_asic2_temp}�C", f"{calc_adc_temp}�C"

    def _get_power_sensors(self, cmd_no=0):
        vsr_d = list()
        self._uart_write(self.addr, get_vsr_cmd_char("get_pwr"), vsr_d, cmd_no=cmd_no)
        resp = self._read_response(cmd_no)
        sensors_values = self._check_uart_response(resp)
        hv_value = self.get_hv_value(sensors_values, None)
        return hv_value

    def get_hv_value(self, sensors_values, vsr):
        """Take the full string of voltages and extract the HV value."""
        try:
            # Calculate V10, the 3.3V reference voltage
            reference_voltage = convert_from_ascii(sensors_values[36:40]) * (2.048 / 4095)
            # Calculate HV rails
            u1 = convert_from_ascii(sensors_values[:4]) * (reference_voltage / 2**12)
            # Apply conversion gain # Added 56V following HV tests
            hv_monitoring_voltage = u1 * 1621.65 - 1043.22 + 56
            # print("hv value: {}".format(hv_monitoring_voltage))
            return hv_monitoring_voltage
        except ValueError as e:
            print("VSR %s: Error obtaining HV value: %s" %
                          (format(vsr, '#02x'), e))
            return -1

    def get_temperature(self, cmd_no=0):
        """Gets the current temperature of the VSR module.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`str`: Formatted temperature.
        """
        return self._get_env_sensors(cmd_no=cmd_no)[0]

    def get_humidity(self, cmd_no=0):
        """Gets the current relative humidity of the VSR module.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`str`: Formatted relative humidity.
        """
        return self._get_env_sensors(cmd_no=cmd_no)[1]

    def get_asic_temperature(self, idx=1, cmd_no=0):
        """Gets the current temperature of the selected `Hexitec` ASIC hosted on the VSR module.

        Args:
            idx (:obj:`int`, optional): Index of the Hexitec ASIC to return, indexed from `1`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`str`: Formatted temperature.
        """
        if idx == 0 or idx > 2:
            print(f"[ERROR] ASIC index out of range <{idx}>. Must be '1' or '2'.")
        else:
            idx += 1
        return self._get_env_sensors(cmd_no=cmd_no)[idx]

    def get_adc_temperature(self, cmd_no=0):
        """Gets the current temperature of the VSR module ADC.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`str`: Formatted temperature.
        """
        return self._get_env_sensors(cmd_no=cmd_no)[4]

    def get_firmware_version(self, cmd_no=0):
        """Gets the VSR FPGA firmware version

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`str`: Formatted FPGA version.
        """
        return self._fpga_reg_read(REG130['addr'], cmd_no=cmd_no)

    def get_customer_id(self, cmd_no=0):
        """Gets the VSR Customer ID

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`str`: Formatted Customer ID.
        """
        return self._fpga_reg_read(REG128['addr'], cmd_no=cmd_no)

    def get_project_id(self, cmd_no=0):
        """Gets the VSR Project ID.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`str`: Formatted Project ID.
        """
        return self._fpga_reg_read(REG129['addr'], cmd_no=cmd_no)

    def set_rows1_clock(self, val):
        """Sets the value of `RowS1 Clock` *without* writing to VSR FPGA registers.

        .. warning::
           This method *DOES NOT* load the `RowS1 Clock` value into the VSR FPGA registers.
           Use :meth:`write_rows1_clock` to write :attr:`rows1_clock` to the VSR FPGA registers.

        Args:
            val (:obj:`int`): A 16 bit :obj:`int` representing the `RowS1 Clock` value.

        Returns:
            Nothing.
        """
        self.rows1_clock = val

    def write_rows1_clock(self, cmd_no=0):
        """Writes the `RowS1 Clock` value from :attr:`rows1_clock` to the VSR FPGA registers.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        wr_data = [self.rows1_clock & REG2['mask'], ((self.rows1_clock >> 8) & REG3['mask'])]
        addr = REG2['addr']
        self._fpga_reg_write_burst(addr, wr_data, cmd_no=cmd_no)

    def get_rows1_clock(self):
        """Gets the `RowS1 Clock` value of the :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `RowS1 Clock` value from the VSR FPGA registers. Use :meth:`read_rows1_clock`
           to read the :attr:`rows1_clock` attribute from the VSR FPGA registers.

        Returns:
            :obj:`int`: 16 bit :obj:`int` for the :attr:`rows1_clock`.
        """
        return self.rows1_clock

    def read_rows1_clock(self, cmd_no=0):
        """Reads the `RowS1 Clock` value from the corresponding VSR FPGA registers.

        .. warning::
           This method *DOES NOT* modify the :attr:`rows1_clock` attribute. Use :meth:`set_rows1_clock`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`: Constructed value from the `RowS1 Clock` low and high byte registers.
        """
        rows1_clock_l = self._fpga_reg_read(REG2['addr'], cmd_no=cmd_no)
        rows1_clock_h = self._fpga_reg_read(REG3['addr'], cmd_no=cmd_no)
        return int(f"0x{rows1_clock_h:02X}{rows1_clock_l:02X}", 16)

    def set_s1sph(self, val):
        """Sets the value of the `S1Sph` attribute *without* writing to the VSR FPGA register.

        .. warning::
           This method *DOES NOT* load the `S1Sph` value into the VSR FPGA register. Use :meth:`write_s1sph` to
           write :attr:`s1sph` attribute to the VSR FPGA register.

        Args:
            val (:obj:`int`): A 6 bit :obj:`int` representing the `S1Sph` value.

        Returns:
            Nothing.
        """
        self.s1sph = val & REG4['mask']

    def get_s1sph(self):
        """Gets the `S1Sph` attribute value of the :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `S1Sph` value from the VSR FPGA register. Use :meth:`read_s1sph` to
           read the current :attr:`s1sph` value from the VSR FPGA register.

        Returns:
            :obj:`int`: 6 bit :obj:`int` for the :attr:`s1sph`.
        """
        return self.s1sph

    def write_s1sph(self, cmd_no=0):
        """Writes the `S1Sph` value from :attr:`s1sph` attribute to the VSR FPGA register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        wr_data = self.s1sph & REG4['mask']
        addr = REG4['addr']
        self._fpga_reg_write(addr, wr_data, cmd_no=cmd_no)

    def read_s1sph(self, cmd_no=0):
        """Reads the `S1Sph` value from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`s1sph` attribute. Use :meth:`set_s1sph`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`: Value from the `S1Sph` VSR FPGA register.
        """
        return self._fpga_reg_read(REG4['addr'], cmd_no=cmd_no)

    def set_sphs2(self, val):
        """Sets the value of `SphS2` attribute *without* writing to the VSR FPGA register.

        .. warning::
           This method *DOES NOT* load the `SphS2` value into the VSR FPGA register. Use :meth:`write_sphs2` to
           write :attr:`sphs2` attribute to the VSR FPGA register.

        Args:
            val (:obj:`int`): A 6 bit :obj:`int` representing the `SphS2` value.

        Returns:
            Nothing.
        """
        self.sphs2 = val & REG5['mask']

    def get_sphs2(self):
        """Gets the `SphS2` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `SphS2` value from the VSR FPGA register. Use :meth:`read_sphs2` to
           read the current :attr:`sphs2` value from the VSR FPGA register.

        Returns:
            :obj:`int`: 6 bit :obj:`int` for the :attr:`sphs2` attribute.
        """
        return self.sphs2

    def write_sphs2(self, cmd_no=0):
        """Writes the `SphS2` value from :attr:`sphs2` attribute to the corresponding VSR FPGA register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        wr_data = self.sphs2 & REG5['mask']
        addr = REG5['addr']
        self._fpga_reg_write(addr, wr_data, cmd_no=cmd_no)

    def read_sph2(self, cmd_no=0):
        """Reads the `SphS2` value from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`sphs2` attribute. Use :meth:`set_sphs2`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`: Value from the `SphS2` VSR FPGA register.
        """
        return self._fpga_reg_read(REG5['addr'], cmd_no=cmd_no)

    def _write_high_gain(self, cmd_no=0):
        ctrl_reg = clr_field(REG6, "GAIN_SEL", self.read_gain(cmd_no=cmd_no))
        self._fpga_reg_write(REG6['addr'], ctrl_reg, cmd_no=cmd_no)

    def _write_low_gain(self, cmd_no=0):
        ctrl_reg = set_field(REG6, "GAIN_SEL", self.read_gain(cmd_no=cmd_no), 1)
        self._fpga_reg_write(REG6['addr'], ctrl_reg, cmd_no=cmd_no)

    def read_gain(self, cmd_no=0):
        """Reads the `gain` setting bit from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`gain` attribute. Use :meth:`set_gain`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`str`: Either `high` or `low`.
        """
        return self._fpga_reg_read(REG6['addr'], cmd_no=cmd_no)

    def set_gain(self, val):
        """Sets the `gain` attribute of :obj:`VsrModule` *without* writing to the VSR FPGA register.

        .. warning::
           This method *DOES NOT* load the `gain` setting into the VSR FPGA register. Use :meth:`write_gain` to
           write the :attr:`gain` attribute value to the VSR FPGA register.

        Args:
            val (:obj:`str`): From either: `high` or `low`.

        Returns:
            Nothing.
        """
        if val.lower() == "high" or val.lower() == "low":
            self.gain = val.lower()
        else:
            print(f"[ERROR]: Unknown gain. Should be from either: 'high' or 'low'.")

    def write_gain(self, cmd_no=0):
        """Writes the `gain` bit based on the :attr:`gain` attribute to the corresponding VSR FPGA register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        if self.gain.lower() == "low":
            self._write_low_gain(cmd_no=cmd_no)
        elif self.gain.lower() == "high":
            self._write_high_gain(cmd_no=cmd_no)

    def get_gain(self):
        """Gets the `gain` attribute setting for the :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `gain` setting from the VSR FPGA register. Use :meth:`read_gain` to
           read the current :attr:`gain` setting from the VSR FPGA register.

        Returns:
            :obj:`str`: The :attr:`gain` attribute of the :obj:`VsrModule`. Either `high` or `low`.
        """
        return self.gain

    def set_adc_clock_delay(self, val):
        """Sets the value of `ADC Clock Delay` to either of the :attr:`adc_clock_delay` attribute *without* writing to the VSR FPGA register.

        .. warning::
           This method *DOES NOT* load the `ADC Clock Delay` value into the VSR FPGA register.
           Use :meth:`write_adc_clock_delay` to write :attr:`adc_clock_delay` attribute to the VSR FPGA register.

        Args:
            val (:obj:`int`): A 5 bit :obj:`int` representing the `ADC Clock Delay` value.

        Returns:
            Nothing.
        """
        self.adc_clock_delay = val & REG9['mask']

    def get_adc_clock_delay(self):
        """Gets the `ADC Clock Delay` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `ADC Clock Delay` value from the VSR FPGA register. Use
           :meth:`read_adc_clock_delay` to read the current :attr:`adc_clock_delay` value from the VSR FPGA register.

        Returns:
            :obj:`int`: 5 bit :obj:`int` for the :attr:`adc_clock_delay` attribute.
        """
        return self.adc_clock_delay

    def write_adc_clock_delay(self, cmd_no=0):
        """Writes the `ADC Clock Delay` value from :attr:`adc_clock_delay` attribute to the corresponding VSR FPGA register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        wr_data = self.adc_clock_delay & REG9['mask']
        addr = REG9['addr']
        self._fpga_reg_write(addr, wr_data, cmd_no=cmd_no)

    def read_adc_clock_delay(self, cmd_no=0):
        """Reads the `ADC Clock Delay` value from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`adc_clock_delay` attribute. Use :meth:`set_adc_clock_delay`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`: Value from the `ADC Clock Delay` VSR FPGA register.
        """
        return self._fpga_reg_read(REG9['addr'], cmd_no=cmd_no)

    def set_adc_signal_delay(self, val):
        """Sets the value of `ADC Signal Delay` to either of the :attr:`adc_signal_delay` attribute *without* writing to the VSR FPGA register.

        `ADC Signal Delay` is described in the VSR documentation as the F\ :sub:`val` and L\ :sub`val` signals.

        .. warning::
           This method *DOES NOT* load the `ADC Signal Delay` value into the VSR FPGA register.
           Use :meth:`write_adc_signal_delay` to write :attr:`adc_signal_delay` attribute to the VSR FPGA register.

        Args:
            val (:obj:`int`): A 5 bit :obj:`int` representing the `ADC Signal Delay` value.

        Returns:
            Nothing.
        """
        self.adc_signal_delay = val & REG14['mask']

    def get_adc_signal_delay(self):
        """Gets the `ADC Clock Delay` attribute value of :obj:`VsrModule`.

        `ADC Signal Delay` is described in the VSR documentation as the F\ :sub:`val` and L\ :sub:`val` signals.

        .. warning::
           This method *DOES NOT* read the `ADC Signal Delay` value from the VSR FPGA register. Use
           :meth:`read_adc_signal_delay` to read the current :attr:`adc_signal_delay` value from the VSR FPGA register.

        Returns:
            :obj:`int`: 5 bit :obj:`int` for the :attr:`adc_signal_delay` attribute.
        """
        return self.adc_signal_delay

    def write_adc_signal_delay(self, cmd_no=0):
        """Writes the `ADC Signal Delay` value from :attr:`adc_signal_delay` attribute to the corresponding VSR FPGA register.

        `ADC Signal Delay` is described in the VSR documentation as the F\ :sub:`val` and L\ :sub:`val` signals.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        wr_data = self.adc_signal_delay & REG14['mask']
        addr = REG14['addr']
        self._fpga_reg_write(addr, wr_data, cmd_no=cmd_no)

    def read_adc_signal_delay(self, cmd_no=0):
        """Reads the `ADC Signal Delay` value from the corresponding VSR FPGA register.

        `ADC Signal Delay` is described in the VSR documentation as the F\ :sub:`val` and L\ :sub:`val` signals.

        .. warning::
           This method *DOES NOT* modify the :attr:`adc_signal_delay` attribute. Use :meth:`set_adc_signal_delay`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`: Value from the `ADC Signal Delay` VSR FPGA register.
        """
        return self._fpga_reg_read(REG14['addr'], cmd_no=cmd_no)

    def set_sm_vcal_clock(self, val):
        """Sets the value of `State-Machine` V\ :sub:`cal` `Clock` *without* writing to VSR FPGA registers.

        .. warning::
           This method *DOES NOT* load the `State-Machine` V\ :sub:`cal` `Clock` value into the VSR FPGA registers.
           Use :meth:`write_sm_vcal_clock` to write :attr:`sm_vcal_clock` to the VSR FPGA registers.

        Args:
            val (:obj:`int`): A 15 bit :obj:`int` representing the `State-Machine` V\ :sub:`cal` `Clock` value.

        Returns:
            Nothing.
        """
        self.sm_vcal_clock = val

    def write_sm_vcal_clock(self, cmd_no=0):
        """Writes the `State-Machine` V\ :sub:`cal` `Clock` value from :attr:`sm_vcal_clock` to the VSR FPGA registers.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        wr_data = [self.sm_vcal_clock & REG24['mask'], ((self.sm_vcal_clock >> 8) & REG25['mask'])]
        addr = REG24['addr']
        self._fpga_reg_write_burst(addr, wr_data, cmd_no=cmd_no)

    def get_sm_vcal_clock(self):
        """Gets the `State-Machine` V\ :sub:`cal` `Clock` value of the :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `State-Machine` V\ :sub:`cal` `Clock` value from the VSR FPGA registers.
           Use :meth:`read_sm_vcal_clock` to read the :attr:`sm_vcal_clock` attribute from the VSR FPGA registers.

        Returns:
            :obj:`int`: 15 bit :obj:`int` for the :attr:`sm_vcal_clock`.
        """
        return self.sm_vcal_clock

    def read_sm_vcal_clock(self, cmd_no=0):
        """Reads the `State-Machine` V\ :sub:`cal` `Clock` value from the corresponding VSR FPGA registers.

        .. warning::
           This method *DOES NOT* modify the :attr:`sm_vcal_clock` attribute. Use :meth:`set_sm_vcal_clock`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`: Constructed value from the `State-Machine` V\ :sub:`cal` `Clock` low and high byte registers.
        """
        sm_vcal_clock_l = self._fpga_reg_read(REG24['addr'], cmd_no=cmd_no)
        sm_vcal_clock_h = self._fpga_reg_read(REG25['addr'], cmd_no=cmd_no)
        return int(f"0x{sm_vcal_clock_h:02X}{sm_vcal_clock_l:02X}", 16)

    def set_sm_row_wait_clock(self, val):
        """Sets the value of `State-Machine Row Wait Clock` to either of the :attr:`sm_row_wait_clock` attribute *without* writing to the VSR FPGA register.

        .. warning::
           This method *DOES NOT* load the `State-Machine Row Wait Clock` value into the VSR FPGA register.
           Use :meth:`write_sm_row_wait_clock` to write :attr:`sm_row_wait_clock` attribute to the VSR FPGA register.

        Args:
            val (:obj:`int`): A 8 bit :obj:`int` representing the `State-Machine Row Wait Clock` value.

        Returns:
            Nothing.
        """
        self.sm_row_wait_clock = val & REG27['mask']

    def get_sm_row_wait_clock(self):
        """Gets the `State-Machine Row Wait Clock` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `State-Machine Row Wait Clock` value from the VSR FPGA register. Use
           :meth:`read_sm_row_wait_clock` to read the current :attr:`adc_sm_row_wait_clock` value from the VSR FPGA
           register.

        Returns:
            :obj:`int`: 8 bit :obj:`int` for the :attr:`sm_row_wait_clock` attribute.
        """
        return self.sm_row_wait_clock

    def write_sm_row_wait_clock(self, cmd_no=0):
        """Writes the `State-Machine Row Wait Clock` value from :attr:`sm_row_wait_clock` attribute to the corresponding VSR FPGA register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        wr_data = self.sm_row_wait_clock & REG27['mask']
        addr = REG27['addr']
        self._fpga_reg_write(addr, wr_data, cmd_no=cmd_no)

    def read_sm_row_wait_clock(self, cmd_no=0):
        """Reads the `State-Machine Row Wait Clock` value from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`sm_row_wait_clock` attribute. Use :meth:`set_sm_row_wait_clock`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`: Value from the `State-Machine Row Wait Clock` VSR FPGA register.
        """
        return self._fpga_reg_read(REG27['addr'], cmd_no=cmd_no)

    def select_internal_sync_clock(self, cmd_no=0):
        """Select the internal sync clock in the control register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = clr_field(VSR_FPGA_REGS_V0_5_REG1, "SYNC_CLK_SEL",
                             self._fpga_reg_read(VSR_FPGA_REGS_V0_5_REG1['addr'], cmd_no=cmd_no))
        self._fpga_reg_write(VSR_FPGA_REGS_V0_5_REG1['addr'], ctrl_reg, cmd_no=cmd_no)

    def select_external_sync_clock(self, cmd_no=0):
        """Select the external sync clock in the control register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = set_field(VSR_FPGA_REGS_V0_5_REG1, "SYNC_CLK_SEL",
                             self._fpga_reg_read(VSR_FPGA_REGS_V0_5_REG1['addr'], cmd_no=cmd_no), 1)
        self._fpga_reg_write(VSR_FPGA_REGS_V0_5_REG1['addr'], ctrl_reg, cmd_no=cmd_no)

    def deassert_serial_iface_rst(self, cmd_no=0):
        """De-asserts the Serial Interface Reset bit in the control register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = clr_field(VSR_FPGA_REGS_V0_5_REG1, "SERIAL_IFACE_RST",
                             self._fpga_reg_read(VSR_FPGA_REGS_V0_5_REG1['addr'], cmd_no=cmd_no))
        self._fpga_reg_write(VSR_FPGA_REGS_V0_5_REG1['addr'], ctrl_reg, cmd_no=cmd_no)

    def assert_serial_iface_rst(self, cmd_no=0):
        """Asserts the Serial Interface Reset bit in the control register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = set_field(VSR_FPGA_REGS_V0_5_REG1, "SERIAL_IFACE_RST",
                             self._fpga_reg_read(VSR_FPGA_REGS_V0_5_REG1['addr'], cmd_no=cmd_no), 1)
        self._fpga_reg_write(VSR_FPGA_REGS_V0_5_REG1['addr'], ctrl_reg, cmd_no=cmd_no)

    def disable_training(self, cmd_no=0):
        """De-asserts the Training Pattern Enable bit in the control register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = clr_field(VSR_FPGA_REGS_V0_5_REG1, "TRAINING_PATTERN_EN",
                             self._fpga_reg_read(VSR_FPGA_REGS_V0_5_REG1['addr'], cmd_no=cmd_no))
        self._fpga_reg_write(VSR_FPGA_REGS_V0_5_REG1['addr'], ctrl_reg, cmd_no=cmd_no)

    def enable_training(self, cmd_no=0):
        """Asserts the Training Pattern Enable bit in the control register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = set_field(VSR_FPGA_REGS_V0_5_REG1, "TRAINING_PATTERN_EN",
                             self._fpga_reg_read(VSR_FPGA_REGS_V0_5_REG1['addr'], cmd_no=cmd_no), 1)
        self._fpga_reg_write(VSR_FPGA_REGS_V0_5_REG1['addr'], ctrl_reg, cmd_no=cmd_no)

    def enable_plls(self, pll=True, adc_pll=True, cmd_no=0):
        """Enables the VSR PLLs.

        Args:
            pll (:obj:`bool`, optional): Enable the PLL, otherwise leave untouched. Default: `True`.
            adc_pll (:obj:`bool`, optional): Enable the ADC PLL, otherwise leave untouched. Default: `True`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = self._fpga_reg_read(REG7['addr'], cmd_no=cmd_no)
        if pll:
            ctrl_reg = set_field(REG7, "ENABLE_PLL", ctrl_reg, 1)
        if adc_pll:
            ctrl_reg = set_field(REG7, "ENABLE_ADC_PLL", ctrl_reg, 1)
        self._fpga_reg_write(REG7['addr'], ctrl_reg, cmd_no=cmd_no)

    def start_sm_on_rising_edge(self, cmd_no=0):
        """Start the State-Machine on the rising edge of the ADC clock.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = clr_field(REG20, "SM_START_EDGE",
                             self._fpga_reg_read(REG20['addr'], cmd_no=cmd_no))
        self._fpga_reg_write(REG20['addr'], ctrl_reg, cmd_no=cmd_no)

    def start_sm_on_falling_edge(self, cmd_no=0):
        """Start the State-Machine on the falling edge of the ADC clock.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = set_field(REG20, "SM_START_EDGE",
                             self._fpga_reg_read(REG20['addr'], cmd_no=cmd_no), 1)
        self._fpga_reg_write(REG20['addr'], ctrl_reg, cmd_no=cmd_no)

    def set_dc_control_bits(self, capt_avg_pict=True, vcal_pulse_disable=True, spectroscopic_mode_en=True, cmd_no=0):
        """Sets selected bits in the DC Control register.

        Args:
            capt_avg_pict (:obj:`bool`, optional): Sets the corresponding field, otherwise leaves it untouched.
                Default: `True`.
            vcal_pulse_disable (:obj:`bool`, optional): Sets the corresponding field, otherwise leaves it untouched.
                Default: `True`.
            spectroscopic_mode_en (:obj:`bool`, optional): Sets the corresponding field, otherwise leaves it untouched.
                Default: `True`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = self._fpga_reg_read(REG36['addr'], cmd_no=cmd_no)
        if capt_avg_pict:
            ctrl_reg = set_field(REG36, "CAPT_AVG_PICT", ctrl_reg, 1)
        if vcal_pulse_disable:
            ctrl_reg = set_field(REG36, "VCAL_PULSE_DISABLE", ctrl_reg, 1)
        if spectroscopic_mode_en:
            ctrl_reg = set_field(REG36, "SPECTROSCOPIC_MODE_EN", ctrl_reg, 1)
        self._fpga_reg_write(REG36['addr'], ctrl_reg, cmd_no=cmd_no)

    def clr_dc_control_bits(self, capt_avg_pict=True, vcal_pulse_disable=True, spectroscopic_mode_en=True, cmd_no=0):
        """Clears selected bits in the DC Control register.

        Args:
            capt_avg_pict (:obj:`bool`, optional): Clears the corresponding field, otherwise leaves it untouched.
                Default: `True`.
            vcal_pulse_disable (:obj:`bool`, optional): Clears the corresponding field, otherwise leaves it untouched.
                Default: `True`.
            spectroscopic_mode_en (:obj:`bool`, optional): Clears the corresponding field, otherwise leaves it
                untouched. Default: `True`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = self._fpga_reg_read(REG36['addr'], cmd_no=cmd_no)
        if capt_avg_pict:
            ctrl_reg = clr_field(REG36, "CAPT_AVG_PICT", ctrl_reg)
        if vcal_pulse_disable:
            ctrl_reg = clr_field(REG36, "VCAL_PULSE_DISABLE", ctrl_reg)
        if spectroscopic_mode_en:
            ctrl_reg = clr_field(REG36, "SPECTROSCOPIC_MODE_EN", ctrl_reg)
        self._fpga_reg_write(REG36['addr'], ctrl_reg, cmd_no=cmd_no)

    def enable_all_columns(self, asic=1, cmd_no=0):
        """Writes the masks to enable Read and Power for Columns of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [REG174['addr'], REG194['addr']]
        else:
            en_start_addrs = [REG77['addr'], REG97['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all=True), cmd_no=cmd_no)

    def enable_all_rows(self, asic=1, cmd_no=0):
        """Writes the masks to enable Read and Power for Rows of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [REG144['addr'], REG164['addr']]
        else:
            en_start_addrs = [REG47['addr'], REG67['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all=True), cmd_no=cmd_no)

    def disable_all_columns(self, asic=1, cmd_no=0):
        """Writes the masks to disable Read and Power for Columns of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [REG174['addr'], REG194['addr']]
        else:
            en_start_addrs = [REG77['addr'], REG97['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, clr_row_column_mask(all=True), cmd_no=cmd_no)

    def disable_all_rows(self, asic=1, cmd_no=0):
        """Writes the masks to disable Read and Power for Rows of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [REG144['addr'], REG164['addr']]
        else:
            en_start_addrs = [REG47['addr'], REG67['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, clr_row_column_mask(all=True), cmd_no=cmd_no)

    def enable_all_columns_cal(self, asic=1, cmd_no=0):
        """Writes the masks to enable Calibration for Columns of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [REG184['addr']]
        else:
            en_start_addrs = [REG87['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all=True), cmd_no=cmd_no)

    def disable_all_columns_cal(self, asic=1, cmd_no=0):
        """Writes the masks to disable Calibration for Columns of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [REG184['addr']]
        else:
            en_start_addrs = [REG87['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, clr_row_column_mask(all=True), cmd_no=cmd_no)

    def enable_all_rows_cal(self, asic=1, cmd_no=0):
        """Writes the masks to enable Calibration for Rows of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [REG57['addr']]
        else:
            en_start_addrs = [REG154['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all=True), cmd_no=cmd_no)

    def disable_all_rows_cal(self, asic=1, cmd_no=0):
        """Writes the masks to disable Calibration for Rows of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [REG57['addr']]
        else:
            en_start_addrs = [REG154['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, clr_row_column_mask(all=True), cmd_no=cmd_no)

    def configure_asic(self, asic=1, cmd_no=0):
        """Enables the target ASIC by applying the corresponding enable and calibration settings.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`. Default: `1`.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.
        Returns:
            Nothing.
        """
        self.enable_all_columns(asic=asic, cmd_no=cmd_no)
        self.disable_all_columns_cal(asic=asic, cmd_no=cmd_no)
        self.enable_all_rows(asic=asic, cmd_no=cmd_no)
        self.disable_all_rows_cal(asic=asic, cmd_no=cmd_no)

    def set_dac_vcal(self, val):
        """Sets the value of V\ :sub:`cal` attribute *without* writing to the VSR DAC.

        .. warning::
           This method *DOES NOT* load the V\ :sub:`cal` value into the VSR DAC. Use :meth:`write_dac_values` to
           write all `DAC` attributes to the VSR DAC.

        Args:
            val (:obj:`int`): A 12 bit :obj:`int` representing the DAC V\ :sub:`cal` value.

        Returns:
            Nothing.
        """
        mask = 0xFFF
        self.dac_vcal = val & mask

    def get_dac_vcal(self):
        """Gets the V\ :sub:`cal` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the V\ :sub:`cal` value from the VSR DAC. There is no method to
           read each of the current DAC values from the VSR DAC. The only way to retrieve the current values of the VSR
           DAC is to perform a :meth:`write_dac_values` and process the returned :obj:`dict`.

        Returns:
            :obj:`int`: 12 bit :obj:`int` for the :attr:`dac_vcal` attribute.
        """
        return self.dac_vcal

    def set_dac_umid(self, val):
        """Sets the value of U\ :sub:`mid` attribute *without* writing to the VSR DAC.

        .. warning::
           This method *DOES NOT* load the U\ :sub:`mid` value into the VSR DAC. Use :meth:`write_dac_values` to
           write all `DAC` attributes to the VSR DAC.

        Args:
            val (:obj:`int`): A 12 bit :obj:`int` representing the DAC U\ :sub:`mid` value.

        Returns:
            Nothing.
        """
        mask = 0xFFF
        self.dac_umid = val & mask

    def get_dac_umid(self):
        """Gets the U\ :sub:`mid` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the U\ :sub:`mid` value from the VSR DAC. There is no method to
           read each of the current DAC values from the VSR DAC. The only way to retrieve the current values of the VSR
           DAC is to perform a :meth:`write_dac_values` and process the returned :obj:`dict`.

        Returns:
            :obj:`int`: 12 bit :obj:`int` for the :attr:`dac_umid` attribute.
        """
        return self.dac_umid

    def set_dac_hv(self, val):
        """Sets the value of DAC `HV` attribute *without* writing to the VSR DAC.

        .. warning::
           This method *DOES NOT* load the `HV` value into the VSR DAC. Use :meth:`write_dac_values` to
           write all `DAC` attributes to the VSR DAC.

        Args:
            val (:obj:`int`): A 12 bit :obj:`int` representing the DAC `HV` value.

        Returns:
            Nothing.
        """
        mask = 0xFFF
        self.dac_hv = val & mask

    def get_dac_hv(self):
        """Gets the DAC `HV` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `HV` value from the VSR DAC. There is no method to
           read each of the current DAC values from the VSR DAC. The only way to retrieve the current values of the VSR
           DAC is to perform a :meth:`write_dac_values` and process the returned :obj:`dict`.

        Returns:
            :obj:`int`: 12 bit :obj:`int` for the :attr:`dac_hv` attribute.
        """
        return self.dac_hv

    def set_dac_det_ctrl(self, val):
        """Sets the value of DAC `DET Control` attribute *without* writing to the VSR DAC.

        .. warning::
           This method *DOES NOT* load the `DET Control` value into the VSR DAC. Use :meth:`write_dac_values` to
           write all `DAC` attributes to the VSR DAC.

        Args:
            val (:obj:`int`): A 12 bit :obj:`int` representing the DAC `DET Control` value.

        Returns:
            Nothing.
        """
        mask = 0xFFF
        self.dac_det_ctrl = val & mask

    def get_dac_det_ctrl(self):
        """Gets the DAC `DET Control` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `DET Control` value from the VSR DAC. There is no method to
           read each of the current DAC values from the VSR DAC. The only way to retrieve the current values of the VSR
           DAC is to perform a :meth:`write_dac_values` and process the returned :obj:`dict`.

        Returns:
            :obj:`int`: 12 bit :obj:`int` for the :attr:`dac_det_ctrl` attribute.
        """
        return self.dac_det_ctrl

    def write_dac_values(self, cmd_no=0):
        """Writes each of the DAC based attributes to the VSR DAC.

        Writes the following attributes: :attr:`dac_vcal`, :attr:`dac_umid`,  :attr:`dac_hv`,  :attr:`dac_det_ctrl`, and
        :attr:`dac_reserve2`.

        .. note::
           The only way to return values from the VSR DAC is by performing a :meth:`write_dac_values`. This method
           will return a :obj:`dict` of all values **without** overwriting the VSR DAC based attributes.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`dict` of key/values pairs, where the keys are: `vcal`, `umid`, `hv`, `det_ctrl` and `reserve2`.
        """
        dac_mask = 0xFFF  # Limit the DAC to 12 bits.
        nof_bytes = 2  # Each value unpacks into this many bytes.
        vsr_cmd = get_vsr_cmd_char("write_dac_values")
        dac_values = [self.dac_vcal, self.dac_umid, self.dac_hv, self.dac_det_ctrl, self.dac_reserve2 ]
        wr_cmd = list()
        tmp_dict =dict()
        for val in dac_values:
            wr_cmd.extend(unpack_data_for_vsr_write(val, mask=dac_mask, nof_bytes=nof_bytes))
        self._uart_write(self.addr, vsr_cmd, wr_cmd, cmd_no=cmd_no)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)
        tmp_dict['vcal'] = resp[0:4]
        tmp_dict['umid'] = resp[4:8]
        tmp_dict['hv'] = resp[8:12]
        tmp_dict['det_ctrl'] = resp[12:16]
        tmp_dict['reserve2'] = resp[16:20]
        return tmp_dict

    def disable_sm(self, cmd_no=0):
        """De-asserts the State-Machine Enable bit in the control register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = clr_field(VSR_FPGA_REGS_V0_5_REG1, "SM_EN",
                             self._fpga_reg_read(VSR_FPGA_REGS_V0_5_REG1['addr'], cmd_no=cmd_no))
        self._fpga_reg_write(VSR_FPGA_REGS_V0_5_REG1['addr'], ctrl_reg, cmd_no=cmd_no)

    def enable_sm(self, cmd_no=0):
        """Asserts the State-Machine Enable bit in the control register.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        ctrl_reg = set_field(VSR_FPGA_REGS_V0_5_REG1, "SM_EN",
                             self._fpga_reg_read(VSR_FPGA_REGS_V0_5_REG1['addr'], cmd_no=cmd_no), 1)
        self._fpga_reg_write(VSR_FPGA_REGS_V0_5_REG1['addr'], ctrl_reg, cmd_no=cmd_no)

    def preconfigure(self, **kwargs):
        """Preconfigure the :obj:`VsrModule` ready for :meth:`initialise`.

        Keyword Args:
            rows1_clock (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            s1sph (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            sphs2 (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            gain (:obj:`str`, optional): `high` or `low`. Default value: loaded on :meth:`VsrModule.__init__`.
            adc_clock_delay (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            adc_signal_delay (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            sm_vcal_clock (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            sm_row_wait_clock (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.

        Returns:
            Nothing.
        """
        self.set_rows1_clock(kwargs.get('rows1_clock', self.rows1_clock))
        self.set_s1sph(kwargs.get('s1sph', self.s1sph))
        self.set_sphs2(kwargs.get('sphs2', self.sphs2))
        self.set_gain(kwargs.get('gain', self.gain))
        self.set_adc_clock_delay(kwargs.get('adc_clock_delay', self.adc_clock_delay))
        self.set_adc_signal_delay(kwargs.get('adc_signal_delay', self.adc_signal_delay))
        self.set_sm_vcal_clock(kwargs.get('sm_vcal_clock', self.sm_vcal_clock))
        self.set_sm_row_wait_clock(kwargs.get('sm_row_wait_clock', self.sm_row_wait_clock))

    def preconfigure_dac(self, **kwargs):
        """Preconfigure the DAC of :obj:`VsrModule` ready for :meth:`initialise`.

        Keyword Args:
            dac_vcal (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            dac_umid (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            dac_hv (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            dac_det_ctrl (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.

        Returns:
            Nothing.
        """
        self.set_dac_vcal(kwargs.get('dac_vcal', self.dac_vcal))
        self.set_dac_umid(kwargs.get('dac_umid', self.dac_umid))
        self.set_dac_hv(kwargs.get('dac_hv', self.dac_hv))
        self.set_dac_det_ctrl(kwargs.get('dac_det_ctrl', self.dac_det_ctrl))

    def set_adc_output_phase(self, phase):
        """Sets the value of ADC `Output Phase` value attribute *without* writing to the VSR ADC.

        .. warning::
           This method *DOES NOT* load the `Output Phase` value into the VSR ADC. Use :meth:`write_adc_values` to
           write all `DAC` attributes to the VSR DAC.

        Args:
            phase (:obj:`str`): Representing the ADC `Output Phase` value.

        Returns:
            Nothing.
        """
        if phase.lower() == "0":
            self.adc_output_phase = 0x0
        elif phase.lower() == "60":
            self.adc_output_phase = 0x1
        elif phase.lower() == "120":
            self.adc_output_phase = 0x2
        elif phase.lower() == "180":
            self.adc_output_phase = 0x3
        elif phase.lower() == "300":
            self.adc_output_phase = 0x5
        elif phase.lower() == "360":
            self.adc_output_phase = 0x6
        elif phase.lower() == "480":
            self.adc_output_phase = 0x8
        elif phase.lower() == "540":
            self.adc_output_phase = 0x9
        elif phase.lower() == "600":
            self.adc_output_phase = 0xA
        elif phase.lower() == "660":
            self.adc_output_phase = 0xF
        else:
            # The default value of 180 degrees
            self.adc_output_phase = 0x3

    def get_adc_output_phase(self):
        """Gets the `ADC Register Address` and `Output Phase` attribute value combination for the AD9252 ADC.

        .. warning::
           This method *DOES NOT* read the ADC `Output Phase` value from the VSR ADC. There is no method to
           read any of the current ADC values from the VSR ADC. The only way to retrieve the current value of a VSR
           ADC register is to perform a :meth:`write_adc_values` and process the returned :obj:`dict`.

        Returns:
            :obj:`list` of :obj:`int`: 8 bit `ADC Reg Address` and 8 bit `Output Phase` pair for AD9252 ADC.
        """
        adc_output_phase_reg_addr = 0x16
        return [adc_output_phase_reg_addr, self.adc_output_phase]

    def write_adc_values(self, add_dat_pair, cmd_no=0):
        """Writes an ADC Register Address/Data :obj:`list` pair to the VSR ADC.

        Args:
            add_dat_pair (:obj:`list` of :obj:`int`) ADC Register Address/Data combination pair to write to VSr ADC.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        vsr_cmd = get_vsr_cmd_char("write_adc_values")
        wr_cmd = list()
        for b in add_dat_pair:
            wr_cmd.extend(convert_to_ascii(b, zero_pad=True))
        self._uart_write(self.addr, vsr_cmd, wr_cmd, cmd_no=cmd_no)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)
        return resp[0:4]

    def preconfigure_adc(self, **kwargs):
        """Preconfigure the ADC of :obj:`VsrModule` ready for :meth:`initialise`.

        The register address/values are raw, and can be found in the
        :download:`AD9252 datasheet <../../../docs/references/ad9252.pdf>`.

        Keyword Args:
            adc_output_phase (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.

        Returns:
            Nothing.
        """
        self.set_adc_output_phase(kwargs.get('adc_output_phase', self.adc_output_phase))

    def init_adc(self, cmd_no=0):
        """Initialisation sequence for the VSR ADC.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        self.disable_adc(cmd_no=cmd_no)
        self.enable_dac(cmd_no=cmd_no)
        self.disable_sm(cmd_no=cmd_no)
        self.enable_sm(cmd_no=cmd_no)
        self.enable_adc_and_dac(cmd_no=cmd_no)
        self.write_adc_values(self.get_adc_output_phase(), cmd_no=0)

    def initialise(self, cmd_no=0):
        """Initialise the VSR.

        Before running :meth:`initialise` ensure the correct configuration is loaded using :meth:`preconfigure`.

        Args:
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            Nothing.
        """
        print(f"[INFO]: VSR{self.slot}: Starting Initialisation...")
        self.select_external_sync_clock(cmd_no=cmd_no)
        self.enable_plls(pll=True, adc_pll=True, cmd_no=cmd_no)
        self.write_rows1_clock(cmd_no=cmd_no)
        self.write_s1sph(cmd_no=cmd_no)
        self.write_sphs2(cmd_no=cmd_no)
        self.write_gain(cmd_no=cmd_no)
        self.write_adc_clock_delay(cmd_no=cmd_no)
        self.write_adc_signal_delay(cmd_no=cmd_no)
        self.write_sm_row_wait_clock(cmd_no=cmd_no)
        self.start_sm_on_falling_edge(cmd_no=cmd_no)
        # asserting the serial interface reset bit corresponds with line 1196 (enable LVDS interface) of:
        # https://github.com/stfc-aeg/hexitec-detector/blob/rdma_rework_from_gitlab/control/src/hexitec/HexitecFem.py
        self.assert_serial_iface_rst(cmd_no=cmd_no)  # 1196
        asics = [1, 2]
        for asic in asics:
            self.configure_asic(asic=asic, cmd_no=cmd_no)  # 1206
        current_dac_vals = self.write_dac_values(cmd_no=cmd_no)  # 1208
        self.init_adc(cmd_no=cmd_no)  # 1216
        self.set_dc_control_bits(capt_avg_pict=True, vcal_pulse_disable=True, spectroscopic_mode_en=False,
                                 cmd_no=cmd_no)  # 1226
        # \TODO: Check if the spectroscopic_mode_en is already enabled or if it needs to be toggled off/on via the
        #        previous :meth:`write_dc_control_bits`.
        self.set_dc_control_bits(capt_avg_pict=False, vcal_pulse_disable=False, spectroscopic_mode_en=True,
                                 cmd_no=cmd_no)  # 1229
        print(f"[INFO]: VSR{self.slot}: Starting LVDS Training...")
        self.enable_training(cmd_no=cmd_no)  # 1231
        self.write_sm_vcal_clock(cmd_no=cmd_no)  # 1238 & 1240
        self.clr_dc_control_bits(capt_avg_pict=False, vcal_pulse_disable=True, spectroscopic_mode_en=False,
                                 cmd_no=cmd_no)  # 1243
        print(f"[INFO]: VSR{self.slot}: Finished Initialisation.")

	### CA Extra Funcs ###

    def _read_response(self, cmd_no=0):
        """Monitors UART Status, reads response once available."""
        # print("uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done")
        counter = 0
        rx_pkt_done = 0
        while not rx_pkt_done:
            _, _, _, _, _, rx_pkt_done = self._rdma_ctrl_iface.read_uart_status()
            # uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, \
            #     rx_pkt_done = self._rdma_ctrl_iface.read_uart_status()
            # print("     {0:X}          {1:X}             {2:X}              {3:X}          {4:X}            {5:X} counter: {6}".format(
            #     uart_status, tx_buff_full, tx_buff_empty, rx_buff_full, rx_buff_empty, rx_pkt_done, counter))
            counter += 1
            if counter == 15001:
                print("   boom!")
                break
        response = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        # print("... receiving: {} ({})".format(' '.join("0x{0:02X}".format(x) for x in response), counter))
        return response

    def _read_vsr_register(self, reg_addr_h, reg_addr_l, cmd_no=0):
        """Reads the specified VSR register address.

        Args:
            reg_addr_h (:obj:`int`): VSR register MSB address.
            reg_addr_l (:obj:`int`): VSR register LSB address.
            cmd_no (:obj:`int`, optional): command number to insert into the RDMA header. Useful for debugging RDMA
                commands. Default: `0`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_read"), [reg_addr_h, reg_addr_l], cmd_no=cmd_no)
        resp = self._read_response(cmd_no)

        # print(f" DBG1:  {resp}")
        # resp_d = self._check_uart_response(resp)
        # # Calling _check_uart_response turns: 
        # #  DBG1:  [42, 144, 70, 70, 13] into:
        # #  DBG2:  [70]
        # print(f" DBG2:  {resp_d}")
        reply = resp[2:-1]                                      # Omit start char, vsr address and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        # print(f" DBG1:  {resp}")
        return resp, reply

    def readout_vsr_register(self, description, address_h, address_l):
        """Read out VSR register.

        Example: (description, address_h, address_l) = 1, "Column Read Enable ASIC2", 0x43, 0x32
        """
        number_registers = 10
        resp_list, reply_list = self.block_read_and_response(number_registers, address_h, address_l)
        print(" {0} (0x{1}{2}): {3}".format(description, chr(address_h), chr(address_l), reply_list))

    def block_read_and_response(self, number_registers, address_h, address_l):
        """Read from address_h, address_l, covering number_registers registers."""
        most_significant, least_significant = self.expand_addresses(number_registers, address_h, address_l)
        resp_list = []
        reply_list = []
        for index in range(number_registers):
            resp, reply = self._read_vsr_register(most_significant[index], least_significant[index])
            resp_list.append(resp[2:-1])
            reply_list.append(reply)
        # print(" BRaR, resp_list: {} reply_list {}".format(resp_list, reply_list))
        # raise Exception("Premature!")
        return resp_list, reply_list

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

    ### Functions for supporting fem.initialise_vsr() ###

    # TODO Desperately in need of refractoring..
    def send_cmd(self, cmd):
        """Send a command string to the microcontroller."""
        # print(" VsrMod Send to UART: {}  ({})".format(' '.join("0x{0:02X}".format(x) for x in cmd), cmd))
        # self.x10g_rdma.uart_tx(cmd)
        num_cmd = len(cmd)
        # print("  send_cmd() is very brittle! cmd? = {}".format(num_cmd))
        # TODO Improve dirty hack?
        if num_cmd == 5:
            # Ordinary start, vsr_address, vsr_value format
            vsr_cmd_char, address_h, address_l, value_h, value_l = cmd
            self._uart_write(self.addr, vsr_cmd_char,
                            [address_h, address_l, value_h, value_l], cmd_no=0)
        else:
            # write_dac_values special case (21 entries)
            vsr_cmd_char = cmd[0]
            self._uart_write(self.addr, vsr_cmd_char,
                            cmd[1:], cmd_no=0)

    def read_and_response(self, address_h, address_l, delay=False, cmd_no=0):
        """Send a read and read the reply."""
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_read"), [address_h, address_l], cmd_no=cmd_no)
        resp = self._read_response(cmd_no)
        # print(f" RaR DBG1:  {resp}")
        # resp_d = self._check_uart_response(resp)
        # # Calling _check_uart_response turns:
        # #  DBG1:  [42, 144, 70, 70, 13] into:
        # #  DBG2:  [70]
        # print(f"RaR DBG2:  {resp_d}")
        reply = resp[2:-1]                                      # Omit start char, vsr address and end char
        reply = "{}".format(''.join([chr(x) for x in reply]))   # Turn list of integers into ASCII string
        return resp, reply

    def write_and_response(self, address_h, address_l, value_h, value_l,
                           masked=True, delay=False, cmd_no=0):
        """Write value_h, value_l to address_h, address_l, if not masked
        then register value overwritten."""
        resp, reply = self.read_and_response(address_h, address_l)
        resp = resp[2:-1]   # Extract payload
        if masked:
            value_h, value_l = self.mask_aspect_encoding(value_h, value_l, resp)
        # print("   WaR Write: {} {} {} {} {}".format(vsr, address_h, address_l, value_h, value_l))

        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_write"),
                         [address_h, address_l, value_h, value_l], cmd_no=cmd_no)
        resp = self._read_response(cmd_no)
        reply = resp[4:-1]  # Omit start char, vsr & register addresses, and end char
        # Turn list of integers into ASCII string
        reply = "{}".format(''.join([chr(x) for x in reply]))
        # print(" WR. reply: {} (resp: {})".format(reply, resp))      # ie reply = '01'
        if ((resp[4] != value_h) or (resp[5] != value_l)):
            print("H? {} L? {}".format(resp[4] == value_h, resp[5] == value_l))
            print("WaR. reply: {} (resp: {}) VS H: {} L: {}".format(reply, resp, value_h, value_l))
            print("WaR. (resp: {} {}) VS H: {} L: {}".format(resp[4], resp[5], value_h, value_l))
            raise RdmaError("Readback value did not match written!")
        return resp, reply

    def translate_to_normal_hex(self, value):
        """Translate Aspect encoding into 0-F equivalent scale."""
        if value not in self.HEX_ASCII_CODE:
            raise RdmaError("Invalid Hexadecimal value {0:X}".format(value))
        if value < 0x3A:
            value -= 0x30
        else:
            value -= 0x37
        return value

    def mask_aspect_encoding(self, value_h, value_l, resp):
        """Mask values honouring aspect encoding.

        Aspect: 0x30 = 1, 0x31 = 1, .., 0x39 = 9, 0x41 = A, 0x42 = B, .., 0x46 = F.
        Therefore increase values between 0x39 and 0x41 by 7 to match aspect's legal range.
        I.e. 0x39 | 0x32 = 0x3B, + 7 = 0x42.
        """
        value_h = self.translate_to_normal_hex(value_h)
        value_l = self.translate_to_normal_hex(value_l)
        resp[0] = self.translate_to_normal_hex(resp[0])
        resp[1] = self.translate_to_normal_hex(resp[1])
        masked_h = value_h | resp[0]
        masked_l = value_l | resp[1]
        # print("h: {0:X} r: {1:X} = {2:X} masked: {3:X} I.e. {4:X}".format(
        #     value_h, resp[0], value_h | resp[0], masked_h, self.HEX_ASCII_CODE[masked_h]))
        # print("l: {0:X} r: {1:X} = {2:X} masked: {3:X} I.e. {4:X}".format(
        #     value_l, resp[1], value_l | resp[1], masked_l, self.HEX_ASCII_CODE[masked_l]))
        return self.HEX_ASCII_CODE[masked_h], self.HEX_ASCII_CODE[masked_l]

    def toggle_lvds_training(self):
        """Enable LVDS training by toggling the relevant register on then off."""
        self._rdma_ctrl_iface.toggle_training(0x10)
        time.sleep(0.2)
        self._rdma_ctrl_iface.toggle_training(0x0)

    # TODO CONSTANTS, move these?

    HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                      0x41, 0x42, 0x43, 0x44, 0x45, 0x46]


class RdmaError(Exception):
    """Simple exception class for RdmaUDP to wrap lower-level exceptions."""

    pass
