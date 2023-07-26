# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.
"""Classes and functions to connect to, and interact with aSpect VSR modules in Hexitec 2x\ `N`
based systems.

.. important::

   Requires memory mapped :obj:`dict` imported from the following modules:
    - :mod:`rdma_control.RDMA_REGISTERS`,
    - :mod:`rdma_control.VSR_FPGA_REGISTERS`
   Also requires the corresponding helper functions imported from
   :mod:`rdma_control.rdma_register_helpers` to access and modify the dictionary entries defining
   the registers.

   :mod:`rdma_control.RDMA_REGISTERS` and :mod:`rdma_control.VSR_FPGA_REGISTERS` are generated from
   `XML2VHDL` output, regenerated at FPGA synthesis time. Please
   ensure the latest version is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure
   compatibility with the register map in the current FPGA bitstream.
"""
import time
import RdmaUdp.rdma_register_helpers as rdma
from . import VSR_FPGA_REGISTERS
from .VSR_RDMA_REGISTERS import *


def get_vsr_cmd_char(code):
    """Converts operation into corresponding VSR command character.

        Args:
            code (:obj:`str`): from:
                `"start"`, `"end"`, `"resp"`, `"bcast"`, `"whois"`, `"get_env"`, '"enable"',
                '"disable"', `"adc_dac_ctrl"`, `"fpga_reg_write"`, `"fpga_reg_read"`,
                `"fpga_reg_set_bit"`, `"fpga_reg_clr_bit"`, `"fpga_reg_write_burst"`,
                `"fpga_reg_write_stream"`, `"fpga_active_reg_readback"`, `"write_dac_values"`,
                `"write_dac_values"`

        Returns:
            :obj:`int`: cmd/character to place in VSR UART command sequences, can also be used to
                validate command responses.
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
    elif code.lower() == "get_pwr":
        return 0x50
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
    """Converts an integer into a :obj:`list` of :obj:`int` ASCII representations of the :obj:`hex`
    equivalent.

    Args:
        d (:obj:`int`): Value to convert.
        zero_pad (:obj:`bool`, optional): Add ASCII zero padding to left-hand side of generated
            :obj:`list`. Default: `False`.

    Returns:
        :obj:`list` of :obj:`int`: Values of ASCII equivalents, for each of the :obj:`hex`
            characters required to represent the :attr:`d`.
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


def set_row_column_mask(row_col_mask=None, all_as_value=0xff, max_elements=80, reg_size=8):
    """Generates a mask to set the selected elements of a `Hexitec` Row or Column.

    Args:
        row_col_mask (:obj:`list` of obj:`int`, optional): A :obj:`list` containing
            :obj:`max_elements` of 8 bit valuesto apply as the row/column mask, if
            `None` :obj:`all_as_value` will be applied to all elements. Default: `None`.
        all_as_value (:obj:`int`, optional): 8 bit value, to set all elements to, if `row_col_mask`
            is `None`, otherwise ignored and :obj:`row_col_mask` will be used. Default: `0xff`.
        max_elements (:obj:`int`, optional): number of elements in the generated mask.
            Default: `80`.
        reg_size (:obj:`int`, optional): size, in bits, of the register(s) storing masked values.
            Default: `8` bit.
    Returns:
        :obj:`list` of :obj:`int` of values, where each element in the :obj:`list` represents the
            masked values of each of the 8 bit registers required to describe the complete mask.
    """
    tmp_list = list()
    if row_col_mask is None:
        for i in range(0, max_elements // reg_size):
            tmp_list.append(all_as_value & 0xff)
    else:
        for i in row_col_mask:
            tmp_list.append(i & 0xff)
    return tmp_list


def unpack_data_for_vsr_write(dat, mask=0xFFF, nof_bytes=2):
    """Unpacks words, greater than 1 byte and unpacks them into multiple bytes for writing to the
    VSR.

    Args:
        dat (:obj:`int`): Data to unpack.
        mask (:obj:`int`, optional): Mask to limit the number of ASCII characters to unpack data to.
            Default: `0xFFF`, 12 bits.
        nof_bytes (:obj:`int`): Number of bytes to unpack :argument:`dat` to. Default: `2`.

    Returns:
        :obj:`list` of ASCII coded hex values for :argument:`dat`.
    """
    unpacked_dat = list()
    for i in range(0, nof_bytes):
        shifted = ((dat & mask) >> (i * 8)) & 0xFF
        unpacked_dat = [*(convert_to_ascii(shifted, zero_pad=True)), *unpacked_dat]
    return unpacked_dat


def enable_training(vsr_list, time_s=0.1):
    vsr = ''
    for vsr in vsr_list:
        vsr._enable_training()

    ctrl_reg = rdma.set_field(HEXITEC_2X6_VSR_DATA_CTRL, "TRAINING_EN",
                              vsr._fpga_reg_read(HEXITEC_2X6_VSR_DATA_CTRL['addr']), 1)
    vsr._fpga_reg_write(HEXITEC_2X6_VSR_DATA_CTRL['addr'], ctrl_reg)

    time.sleep(time_s)


def disable_training(vsr_list):
    vsr = ''
    for vsr in vsr_list:
        vsr._disable_training()

    ctrl_reg = rdma.clr_field(HEXITEC_2X6_VSR_DATA_CTRL, "TRAINING_EN",
                              vsr._fpga_reg_read(HEXITEC_2X6_VSR_DATA_CTRL['addr']))
    vsr._fpga_reg_write(HEXITEC_2X6_VSR_DATA_CTRL['addr'], ctrl_reg)


class VsrAssembly(object):
    """Class for globally controlling all VSR modules on a Hexitec assembly.

    .. important::

       Requires memory mapped :obj:`dict` imported from the following modules:
        - :mod:`rdma_control.RDMA_REGISTERS`,
        - :mod:`rdma_control.VSR_FPGA_REGISTERS`
       Also requires the corresponding helper functions imported from
       :mod:`rdma_control.rdma_register_helpers` to access and modify the dictionary entries
       defining the registers.

       :mod:`rdma_control.RDMA_REGISTERS` and :mod:`rdma_control.VSR_FPGA_REGISTERS` are generated
       from `XML2VHDL` output, regenerated at FPGA synthesis time. Please ensure the latest version
       is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure compatibility with the
       register map in the current FPGA bitstream.

    .. warning::

       Not supplying a :attr:`addr_mapping` :obj:`dict`, :class:`VsrAssembly` will perform a
       :meth:`VsrAssembly.lookup` to determine the configuration of the attached system. This is a
       time-consuming operation so should be avoided whenever possible by supplying a pre-determined
       configuration matching the target system.

    Args:
        rdma_ctrl_iface (:obj:`rdma_control.RdmaUdp`): A configured connection to communicate with
            the `RDMA` `UDP` Ethernet interface.
        slot (:obj:`int`, optional): Slot should only be set via child class(es). Leave set to `0`.
            Default: `0`.
        init_time(:obj:`int`, optional): Time, in seconds, to wait for VSR to power up and FPGA to
            initialise. Default: `15` seconds.
        addr_mapping (:obj:`dict`, optional): Key/value pairs cross-referencing :attr:`slot` with
            hardware address of the corresponding VSR module. Default: `None`. If an address mapping
            is not supplied the :obj:`VsrAssembly` will perform a :meth:`VsrAssembly.lookup` to
            determine the configuration of the attached system.

    Attributes:
        addr_mapping (:obj:`dict`): A copy of the address mapping configuration, either provided or
            determined at initialisation.
        slot (:obj:`int`): Slot number. Set to '0' for global addressing and control.
        addr (:obj:`int`): Hardware address of VSR module, hard-coded on each VSR module.
        cmd_no (:obj:`int`): command number to insert into the RDMA header. Useful for debugging
            RDMA commands. Default: `0`.
    """
    def __init__(self, rdma_ctrl_iface, slot=0, init_time=15, addr_mapping=None, rdma_offset=0x0):
        self._rdma_ctrl_iface = rdma_ctrl_iface
        self.rdma_offset = rdma_offset
        self.cmd_no = 0
        self.slot = slot
        self.init_time = init_time
        if addr_mapping is None:
            self.addr_mapping = self.lookup(init_time=self.init_time)
        else:
            self.addr_mapping = addr_mapping
        self.addr = self.get_addr()
        self._adc_enabled_flag = False
        self._dac_enabled_flag = True   # Enabled upon VSR Power on
        self.debug = False

    def __del__(self):
        self.hv_disable()
        self.disable_module()

    def get_slot(self):
        """Returns the slot number, hosting the VSR module.

        .. note::

           :attr:`slot` = 0 has a special meaning, where :attr:`addr` will be set to the VSR
           broadcast address. Otherwise, positional location of the VSR module (indexed from '1').
           Used by the host FPGA to control power and high-voltage, and to determine which
           :mod:`rdma_control.RDMA_REGISTERS` to associate with the VSR module.

        Returns:
            :obj:`int`:
        """
        return self.slot

    def get_addr(self):
        """Returns the hardware address of the VSR.

        .. note::

            :attr:`slot` = `0` has a special meaning, where :attr:`addr` will be set to the VSR
            broadcast address. Otherwise, the physical VSR address, hard-coded onto the VSR module.

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

    def _fpga_reg_read(self, fgpa_reg_addr):
        """Constructs a VSR FPGA register read command and transmits the request via the UART
        connection.

        Args:
            fgpa_reg_addr (:obj:`int`): Single FPGA register address to read from.

        Returns:
            :obj:`int`: Value read from :attr:`fgpa_reg_addr`.
        """
        ascii_reg_addr = convert_to_ascii(fgpa_reg_addr, zero_pad=True)
        read_cmd = get_vsr_cmd_char("fpga_reg_read")
        self._uart_write(self.addr, read_cmd, ascii_reg_addr)
        resp = self._rdma_ctrl_iface.uart_read()
        if resp:
            resp = self._check_uart_response(resp)
            rd_data = convert_from_ascii(resp[0:2])
            return rd_data
        else:
            print(f"[ERROR]: No response reading from VSR FPGA Register: {hex(fgpa_reg_addr)}")
            return 0

    def _fpga_reg_write(self, fpga_reg_addr, wr_data):
        """Constructs a VSR FPGA register write command and transmits the request via the UART
        connection.

        Args:
            fpga_reg_addr (:obj:`int`): Single FPGA register address to write to.
            wr_data (:obj:`int`): Byte, to write.

        Returns:
            Nothing.
        """
        wr_cmd = list()
        wr_cmd.extend(convert_to_ascii(fpga_reg_addr, zero_pad=True))
        wr_cmd.extend(convert_to_ascii(wr_data, zero_pad=True))
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_write"), wr_cmd)
        resp = self._rdma_ctrl_iface.uart_read()
        self._check_uart_response(resp)

    def _fpga_reg_set_bit(self, fgpa_reg_addr, mask):
        """Constructs a VSR FPGA register set bit command and transmits the request via the UART
        connection.

        Args:
            fgpa_reg_addr (:obj:`int`): Single FPGA register address to write to.
            mask (:obj:`int`): Mask to select bits in the register to set, unmasked bits will remain
                unchanged.
        Returns:
            Nothing.
        """
        wr_cmd = list()
        wr_cmd.extend(convert_to_ascii(fgpa_reg_addr, zero_pad=True))
        wr_cmd.extend(convert_to_ascii(mask, zero_pad=True))
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_set_bit"), wr_cmd)
        resp = self._rdma_ctrl_iface.uart_read()
        self._check_uart_response(resp)

    def _fpga_reg_clr_bit(self, fpga_reg_addr, mask):
        """Constructs a VSR FPGA register clear bit command and transmits the request via the UART
        connection.

        Args:
            fpga_reg_addr (:obj:`int`): Single FPGA register address to write to.
            mask (:obj:`int`): Mask to select bits in the register to clear, unmasked bits will
            remain unchanged.
        Returns:
            Nothing.
        """
        wr_cmd = list()
        wr_cmd.extend(convert_to_ascii(fpga_reg_addr, zero_pad=True))
        wr_cmd.extend(convert_to_ascii(mask, zero_pad=True))
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_clr_bit"), wr_cmd)
        # flush the response from the UART Rx FIFO:
        resp = self._rdma_ctrl_iface.uart_read()
        self._check_uart_response(resp)

    def _fpga_reg_write_burst(self, fpga_reg_addr, wr_data):
        """Constructs a VSR FPGA register write burst command and transmits the request via the UART
        connection.

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
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_reg_write_burst"), wr_cmd)
        # flush the response from the UART Rx FIFO:
        resp = self._rdma_ctrl_iface.uart_read()
        self._check_uart_response(resp)

    def _fpga_reg_write_stream(self, addr_data_pairs):
        """Constructs a VSR FPGA register write stream command and transmits the request via the
        UART connection.

        Args:
            addr_data_pairs (:obj:`dict` of :obj:`int` key and :obj:`int` value pairs): where the
                key is the FPGA register address and the value is the data to write to the key's
                address.

        Returns:
            Nothing.
        """
        wr_dat = list()
        wr_cmd = get_vsr_cmd_char("fpga_reg_write_stream")
        wr_dat.extend(convert_to_ascii(len(addr_data_pairs), zero_pad=True))
        for k, v in addr_data_pairs.items():
            wr_dat.extend(convert_to_ascii(k, zero_pad=True))
            wr_dat.extend(convert_to_ascii(v, zero_pad=True))
        self._uart_write(self.addr, wr_cmd, wr_dat)
        # flush the response from the UART Rx FIFO:
        resp = self._rdma_ctrl_iface.uart_read()
        self._check_uart_response(resp)

    def _fpga_change_active_reg_readout_fpga_reg_write(self, fpga_reg_addr):
        """Constructs a VSR change active FPGA register readback command and transmits the request.

        Args:
            fpga_reg_addr (:obj:`int`): Single FPGA register address to change active readback to.

        Returns:
            Nothing.
        """
        self._uart_write(self.addr, get_vsr_cmd_char("fpga_active_reg_readback"),
                         convert_to_ascii(fpga_reg_addr, zero_pad=True))
        # flush the response from the UART Rx FIFO:
        resp = self._rdma_ctrl_iface.uart_read()
        self._check_uart_response(resp)

    def _uart_write(self, vsr_a, vsr_cmd, wr_d):
        """Wraps UART Tx data with a VSR command header for writing to aSpect based VSR modules.
        """
        wr_cmd = list()
        wr_cmd.append(get_vsr_cmd_char("start"))
        wr_cmd.append(vsr_a)
        wr_cmd.append(vsr_cmd)

        for d in wr_d:
            wr_cmd.append(d)
        wr_cmd.append(get_vsr_cmd_char("end"))
        if self.debug:
            print(f"[DEBUG]: rdmaVsrMod._uart_write: {[ hex(c) for c in wr_cmd ]}")
        self._rdma_ctrl_iface.uart_write(wr_cmd)

    def _get_status(self, vsr_mod=None, hv=False, all_vsrs=False):
        """Returns status of power/high-voltage enable signals for the selected VSR(s).

        Args:
            vsr_mod (:obj:`int`, optional): VSR module to control, indexed from 1. If not set, will
                use the :attr:`slot` to set the VSR module number. Default: `None`.
            hv (:obj:`bool`, optional): Report High Voltage on status, otherwise report power on
                status to the VSR. Default: `False`.
            all_vsrs (:obj:`bool`, optional): Report on all VSR modules. Default: `False`.

        Returns:
            :obj:`list`: Status of requested VSR enable signal(s), represented as :obj:`str` with
            the values `"ENABLED"` or `"DISABLED"`.
        """
        # use the VSR_EN field to set the total number of VSR modules in the system:
        vsr_en_field = rdma.get_field(HEXITEC_2X6_VSR_CTRL, 'VSR_EN')
        nof_modules = vsr_en_field['nof_bits']
        vsr_status = list()
        hv_status = list()
        reg = HEXITEC_2X6_VSR_CTRL
        addr = reg['addr'] + self.rdma_offset

        if all_vsrs:
            vsr_mod = range(1, nof_modules + 1)
        elif vsr_mod is not None:
            vsr_mod = [vsr_mod]
        else:
            if self.slot > nof_modules:
                print(f"[ERROR]: Requested VSR module: <{self.slot}> exceeds total number of modules available: "
                      f"<{nof_modules}>")
                return 0
            else:
                vsr_mod = [self.slot]

        vsr_ctrl_reg = self._rdma_ctrl_iface.udp_rdma_read(address=addr,
                                                           burst_len=1,
                                                           comment=HEXITEC_2X6_VSR_CTRL['description'])[0]
        vsr_en = rdma.decode_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg)
        vsr_hv_en = rdma.decode_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg)

        for vsr in vsr_mod:
            mod_stat = "ENABLED" if vsr_en & (1 << (vsr - 1)) else "DISABLED"
            mod_hv_en = "ENABLED" if vsr_hv_en & (1 << (vsr - 1)) else "DISABLED"
            vsr_status.append(mod_stat)
            hv_status.append(mod_hv_en)

        return hv_status if hv else vsr_status

    def get_module_status(self):
        """Returns status of VSR enable signals for the selected VSR(s).

        Returns:
            :obj:`list`: Status of requested VSR enable signal(s), represented as :obj:`str` with
            the values `"ENABLED" or `"DISABLED"`.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._get_status(hv=False, all_vsrs=all_vsrs)

    def get_hv_status(self):
        """Returns status of high-voltage enable signals for the selected VSR(s).

        Returns:
            :obj:`list`: Status of requested VSR enable signal(s), represented as :obj:`str` with
            the values `"ENABLED" or `"DISABLED"`.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._get_status(hv=True, all_vsrs=all_vsrs)

    def who_is(self):
        """Sends a VSR `who_is?` command.

        Will check the response to see of the Power/HV module is connected. The Power/HV response
        and end of `who_is?` character will be stripped from the response.

        Returns:
            :obj:`list`: of VSR :obj:`int`: Addresses of enabled VSR modules returned by `who_is?`
            command.
        """
        vsr_d = list()  # empty VSR data list to pass to: :meth:`_vsr_uart_write()`
        hv_power_module_id = [0xc0, 0x31]
        whois_end_char = 0x34
        vsr_addrs = list()
        self._uart_write(get_vsr_cmd_char("bcast"), get_vsr_cmd_char("whois"), vsr_d)
        time.sleep(5)
        resp = self._rdma_ctrl_iface.uart_read()
        # check response:
        if resp[-2:] == hv_power_module_id:
            if len(resp) > len(hv_power_module_id):
                stripped_resp = resp[:-2]
                if stripped_resp[-1] == whois_end_char:
                    vsr_addrs = stripped_resp[:-1]
                else:
                    print("[ERROR]: VSR address response: <FAILED>")
        else:
            print("[ERROR]: Power/HV module response: <FAILED>")
        return vsr_addrs

    def lookup(self, init_time=15):
        """Cycle through each possible VSR module slot and return the VSR address for the module in
        each slot.

        Each VSR module has its address hard-coded on the VSR module. The position of VSRs isn't
        guaranteed between hardware assemblies. This routine can be executed once per assembly with
        the results stored externally.

        Args:
            init_time (:obj:`int`, optional): Time, in seconds, to allow VSR FPGA to initialise.
                Default: `15` seconds.

        Returns:
            :obj:`dict`: The hardware configuration of the `Hexitec` assembly. Where the key is the
                VSR slot idx and the value is the :obj:`int` VSR address. Set to `None` if there is
                no `who_is?` response from the corresponding slot.
        """
        # use the VSR_EN field to set the total number of VSR modules in the system:
        vsr_en_field = rdma.get_field(HEXITEC_2X6_VSR_CTRL, 'VSR_EN')
        nof_modules = vsr_en_field['nof_bits']
        vsr_addr_map = dict()
        for v in range(0, nof_modules):
            self._ctrl(vsr_mod=v + 1, op="enable", init_time=init_time)
            self._get_status(vsr_mod=v + 1)
            tmp_addr = self.who_is()
            vsr_addr_map[v + 1] = tmp_addr[0] if tmp_addr else None
            self._ctrl(vsr_mod=v + 1, op="disable", init_time=0)
            self._get_status(vsr_mod=v + 1)
        print(f"[INFO]: Address mapping from lookup: {vsr_addr_map}")
        return vsr_addr_map

    def _ctrl(self, vsr_mod=None, all_vsrs=False, op="disable", init_time=15):
        """Control the selected VSR modules(s).

        This controls the power and high-voltage enable signals between the FPGA and VSR module slots.

        Args:
            vsr_mod (:obj:`int`, optional): VSR module to control, indexed from 1. If not set, will
                use the :attr:`slot` to set the VSR module number. Default: `None`.
            all_vsrs (:obj:`bool`, optional): Control all VSR modules. Default: `False`.
            op (:obj:`str`, optional): Operation to perform. From: `enable`, `disable`, `hv_enable`,
                `hv_disable`. Default: `disable`.
            init_time(:obj:`int`, optional): Time, in seconds, to wait for VSR to power up and FPGA
                to initialise. Default: `15` seconds.

        Returns:
            :obj:`int`: `1` on success, `0` on failure.
        """
        # use the VSR_EN field to set the total number of VSR modules in the system:
        vsr_en_field = rdma.get_field(HEXITEC_2X6_VSR_CTRL, 'VSR_EN')
        nof_modules = vsr_en_field['nof_bits']
        reg = HEXITEC_2X6_VSR_CTRL
        addr = reg['addr'] + self.rdma_offset

        if self.slot > nof_modules:
            print(f"[ERROR]: Requested VSR module: <{self.slot}> exceeds total number of modules available: "
                  f"<{nof_modules}>")
            return 0

        if all_vsrs:
            en_mask = (2 ** nof_modules) - 1
        elif vsr_mod is not None:
            en_mask = 1 << (vsr_mod - 1)
        else:
            en_mask = 1 << (self.slot - 1)

        vsr_ctrl_reg = self._rdma_ctrl_iface.udp_rdma_read(address=addr,
                                                           burst_len=1,
                                                           comment=HEXITEC_2X6_VSR_CTRL['description'])[0]
        if op.lower() == "enable":
            vsr_status = rdma.decode_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg)
            vsr_status = vsr_status | en_mask
            vsr_ctrl_reg = rdma.set_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg, vsr_status)
            self._rdma_ctrl_iface.udp_rdma_write(addr, [vsr_ctrl_reg])
            print(f"[INFO]: Waiting {init_time} second(s) for VSR(s) to initialise...")
            time.sleep(init_time)
        elif op.lower() == "hv_enable":
            vsr_status = rdma.decode_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg)
            vsr_status = vsr_status | en_mask
            vsr_ctrl_reg = rdma.set_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg, vsr_status)
            self._rdma_ctrl_iface.udp_rdma_write(addr, [vsr_ctrl_reg])
        elif op.lower() == "disable":
            vsr_status = rdma.decode_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg)
            vsr_status = vsr_status & ~ en_mask
            vsr_ctrl_reg = rdma.set_field(HEXITEC_2X6_VSR_CTRL, "VSR_EN", vsr_ctrl_reg, vsr_status)
            self._rdma_ctrl_iface.udp_rdma_write(addr, [vsr_ctrl_reg])
        elif op.lower() == "hv_disable":
            vsr_status = rdma.decode_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg)
            vsr_status = vsr_status & ~ en_mask
            vsr_ctrl_reg = rdma.set_field(HEXITEC_2X6_VSR_CTRL, "HV_EN", vsr_ctrl_reg, vsr_status)
            self._rdma_ctrl_iface.udp_rdma_write(addr, [vsr_ctrl_reg])
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
        return self._ctrl(all_vsrs=all_vsrs, op="enable", init_time=self.init_time)

    def hv_enable(self):
        """Enable High-Voltage to the VSR module.

        Returns:
            :obj:`int`: The value `1` on success, `0` on failure.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._ctrl(all_vsrs=all_vsrs, op="hv_enable", init_time=0)

    def disable_module(self):
        """Disable power to the VSR module.

        Returns:
            :obj:`int`: The value `1` on success, `0` on failure.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._ctrl(all_vsrs=all_vsrs, op="disable", init_time=0)

    def hv_disable(self):
        """Disable High-Voltage to the VSR module.

        Returns:
            :obj:`int`: The value `1` on success, `0` on failure.
        """
        all_vsrs = True if self.slot == 0 else False
        return self._ctrl(all_vsrs=all_vsrs, op="hv_disable", init_time=0)

    def enable_vsr(self, init_time=15, addr=False):
        """Starts the default power-up/init sequence of VSR module.

        Default values will be written to VSR modules FPGA and the ADC and DAC will be enabled.

        Average picture will be taken and the state-machine will start for continuous readout with
        dark correction.

        Args:
            init_time (:obj:`int`, optional): wait time, in seconds, to allow each VSR to
                initialise after being sent the `"enable"` command.
            addr (:obj:`int`): Hardware address to target if set, otherwise own VSR module's.

        Returns:
            Nothing.
        """
        address = self.addr
        if addr:
            address = addr
        vsr_d = list()  # empty VSR data list to pass to: :meth:`_vsr_uart_write()`
        self._uart_write(address, get_vsr_cmd_char("enable"), vsr_d)
        time.sleep(init_time)

    def disable_vsr(self, addr=False):
        """Stops the state-machine, and disables ADC and DAC, also stops the PLL in the VSR modules
        FPGA.

        Args:
            addr (:obj:`int`): Hardware address to target if set, otherwise own VSR module's.

        Returns:
            Nothing.
        """
        address = self.addr
        if addr:
            address = addr
        vsr_d = list()  # empty VSR data list to pass to: :meth:`_vsr_uart_write()`
        self._uart_write(address, get_vsr_cmd_char("disable"), vsr_d)

    def _ctrl_converters(self, adc=False, dac=False):
        """Controls the VSR modules ADC and DAC.

        Args:
            adc (:obj:`bool`, optional): State to set the ADC. `True` is enabled, `False` is
                disabled. Default: `False`.
            dac (:obj:`bool`, optional): State to set the DAC. `True` is enabled, `False` is
                disabled. Default: `False`.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        adc_ctrl_bit = 1 if adc else 0
        dac_ctrl_bit = 1 if dac else 0
        ctrl_byte = (dac_ctrl_bit << 1) + adc_ctrl_bit
        # Ensure byte follow aSpect format
        ctrl_byte = [0x30, ctrl_byte + 0x30]
        self._uart_write(self.addr, get_vsr_cmd_char("adc_dac_ctrl"), ctrl_byte)
        resp = self._rdma_ctrl_iface.uart_read()
        resp = self._check_uart_response(resp)
        return 1 if resp[0] == ctrl_byte else 0

    def enable_adc(self):
        """Enables the VSR module ADC, leaves the DAC unchanged.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=True, dac=self._dac_enabled_flag) == 1:
            self._adc_enabled_flag = True
            return 1
        else:
            return 0

    def enable_dac(self):
        """Enables the VSR module DAC, leaves the ADC unchanged.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=self._adc_enabled_flag, dac=True) == 1:
            self._dac_enabled_flag = True
            return 1
        else:
            return 0

    def enable_adc_and_dac(self):
        """Enables the VSR module ADC and DAC.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=True, dac=True) == 1:
            self._adc_enabled_flag = True
            self._dac_enabled_flag = True
            return 1
        else:
            return 0

    def disable_adc(self):
        """Disables the VSR module ADC, leaves the DAC unchanged.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=False, dac=self._dac_enabled_flag) == 1:
            self._adc_enabled_flag = False
            return 1
        else:
            return 0

    def disable_dac(self):
        """Disables the VSR module DAC, leaves the ADC unchanged.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=self._adc_enabled_flag, dac=False) == 1:
            self._dac_enabled_flag = False
            return 1
        else:
            return 0

    def disable_adc_and_dac(self):
        """Disables the VSR module ADC and DAC.

        Returns:
            :obj:`int`:  `1` on success, `0` on failure.
        """
        if self._ctrl_converters(adc=False, dac=False) == 1:
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
        """Takes an incoming :obj:`list` of bytes received from the VSR UART and validates the
        start and end characters.

        Args:
            rx_d (:obj:`list` of :obj:`int`): full byte-by-byte response from VSR UART.

        Returns:
            :obj:`list` of :obj:`int`: Parses :attr:`rx_d` by removing the start of response;
            address; and end character.
        """
        if rx_d[0] == get_vsr_cmd_char("resp"):
            rx_d = rx_d[1:]
        if rx_d[0] == self.addr:
            rx_d = rx_d[1:]
        if rx_d[-1] == get_vsr_cmd_char("end"):
            rx_d = rx_d[:-1]
        return rx_d


class VsrModule(VsrAssembly):
    """A child class, which inherits methods and attributes from :class:`rdma_control.VsrAssembly`.

    Used for describing and controlling individual VSR modules.

    .. important::

       Requires memory mapped :obj:`dict` imported from the following modules:
        - :mod:`rdma_control.RDMA_REGISTERS`,
        - :mod:`rdma_control.VSR_FPGA_REGISTERS`
       Also requires the corresponding helper functions imported from
       :mod:`rdma_control.rdma_register_helpers` to access and modify the dictionary entries
       defining the registers.

       :mod:`rdma_control.RDMA_REGISTERS` and :mod:`rdma_control.VSR_FPGA_REGISTERS` are generated
       from `XML2VHDL` output, regenerated at FPGA synthesis time. Please ensure the latest version
       is used in conjunction with :mod:`rdma_control.RdmaUdp` to ensure compatibility with the
       register map in the current FPGA bitstream.

    .. warning::

       Not supplying a :attr:`addr_mapping` :obj:`dict`, :class:`VsrModule` will perform a
       :meth:`VsrModule.lookup` to determine the configuration of the attached system. This is a
       time-consuming operation so should be avoided whenever possible by supplying a pre-determined
       configuration matching the target system.

    Args:
        rdma_ctrl_iface (:obj:`rdma_control.RdmaUdp`): A configured connection to communicate with
            the `RDMA` `UDP` Ethernet interface.
        slot (:obj:`int`, optional): Slot index, indexed from `1`, of the VSR module. Default: `1`.
        init_time(:obj:`int`, optional): Time, in seconds, to wait for VSR to power up and FPGA to
            initialise. Default: `15` seconds.
        addr_mapping (:obj:`dict`, optional): Key/value pairs cross-referencing :attr:`slot` with
            hardware address of the corresponding VSR module. Default: `None`. If an address
            mapping is not supplied the :obj:`VsrModule` will perform a :meth:`VsrModule.lookup`
            to determine the configuration of the attached system.

    Attributes:
        addr_mapping (:obj:`dict`): A copy of the address mapping configuration, either provided or
            determined at initialisation.
        slot (:obj:`int`): Slot number for corresponding VSR module, indexed from '1'.
        addr (:obj:`int`): Hardware address of VSR module, hard-coded on each VSR module.
        rows1_clock (:obj:`int`): A 16 bit :obj:`int` representing the `RowS1 Clock` value.
            Default: `1`.
        s1sph (:obj:`int`): A 6 bit :obj:`int` representing the `S1Sph` value. Default: `1`.
        sphs2 (:obj:`int`): A 6 bit :obj:`int` representing the `SphS2` value. Default: `6`.
        gain (:obj:`str`): `"high"` or `"low"` `gain`. Default: `"low"`.
        adc_clock_delay (:obj:`int`): A 5 bit :obj:`int` representing the `ADC Clock Delay` value.
            Default: `2`.
        adc_signal_delay (:obj:`int`): A 8 bit :obj:`int` representing the `ADC Signal Delay` value.
            Controls the F\ :sub:`val` and L\ :sub:`val` delays. Default: `10`.
        sm_vcal_clock (:obj:`int`): A 15 bit :obj:`int` representing the
            `State-Machine` V\ :sub:`cal` `Clock` value.
            Default: `0`.
        sm_row_wait_clock (:obj:`int`): A 8 bit :obj:`int` representing the
            `State-Machine Row Wait Clock` value. Default: `8`.
        dac_vcal (:obj:`int`): A 12 bit :obj:`int` representing the `DAC` V\ :sub:`cal` value.
            Default: `0x111`.
        dac_umid (:obj:`int`): A 12 bit :obj:`int` representing the `DAC` U\ :sub:`mid` value.
            Default: `0x555`.
        dac_hv (:obj:`int`): A 12 bit :obj:`int` representing the `DAC High-Voltage` value.
            Note that in the documentation this field is referred to as `reserve1`. Default: `0x0`.
        dac_det_ctrl (:obj:`int`): A 12 bit :obj:`int` representing the `DAC DET control` value.
            Default: `0x0`.
        dac_reserve2 (:obj:`int`): A 12 bit :obj:`int` representing the `DAC Reserved` value.
            Default: `0x8E8`.
        adc_output_phase (:obj:`str`) Output phase of the VSR AD9252 ADC. Default: "540" degrees.
    """
    def __init__(self, rdma_ctrl_iface, slot=1, init_time=15, addr_mapping=None):
        super().__init__(rdma_ctrl_iface, slot=slot, init_time=init_time, addr_mapping=addr_mapping)
        self.rows1_clock = 1
        self.s1sph = 1
        self.sphs2 = 1
        self.gain = "high"
        self.adc_clock_delay = 2
        self.adc_signal_delay = 10
        self.sm_vcal_clock = 1
        self.sm_row_wait_clock = 8
        self.dac_vcal = 0x111   # 0x111 = 0.2V
        self.dac_umid = 0x555   # 0x555 = 1.0V
        self.dac_hv = 0x555
        self.dac_det_ctrl = 0xCCC   # 0
        self.dac_reserve2 = 0x8E8
        self.adc_output_phase = 9
        self.set_adc_output_phase("540")
        self.vcal_enabled = True
        # Control row, column calibration masks:
        self.column_calibration_mask_asic1 = [0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
        self.column_calibration_mask_asic2 = [0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
        self.row_calibration_mask_asic1 = [0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
        self.row_calibration_mask_asic2 = [0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]

    def _get_env_sensors(self):
        vsr_d = list()  # empty VSR data list to pass to: self.uart_write()
        self._uart_write(self.addr, get_vsr_cmd_char("get_env"), vsr_d)
        resp = self._rdma_ctrl_iface.uart_read()
        resp = self._check_uart_response(resp)
        calc_ambient_temp = round(((convert_from_ascii(resp[0:4]) / 2 ** 16) * 175.72) - 46.85, 3)
        calc_humidity = round(((convert_from_ascii(resp[4:8]) / 2 ** 16) * 125) + 6, 3)
        calc_asic1_temp = round(convert_from_ascii(resp[8:12]) * 0.0625, 2)
        calc_asic2_temp = round(convert_from_ascii(resp[12:16]) * 0.0625, 2)
        calc_adc_temp = round(convert_from_ascii(resp[16:20]) * 0.0625, 2)
        ret_tup = f"{calc_ambient_temp}", f"{calc_humidity}",\
            f"{calc_asic1_temp}", f"{calc_asic2_temp}", \
            f"{calc_adc_temp}"
        return ret_tup

    def get_temperature(self):
        """Gets the current temperature of the VSR module.

        Returns:
            :obj:`str`: Formatted temperature.
        """

        return self._get_env_sensors()[0]

    def get_humidity(self):
        """Gets the current relative humidity of the VSR module.

        Returns:
            :obj:`str`: Formatted relative humidity.
        """
        return self._get_env_sensors()[1]

    def get_asic_temperature(self, idx=1):
        """Gets the current temperature of the selected `Hexitec` ASIC hosted on the VSR module.

        Args:
            idx (:obj:`int`, optional): Index of the Hexitec ASIC to return, indexed from `1`.
                Default: `1`.

        Returns:
            :obj:`str`: Formatted temperature.
        """
        if idx == 0 or idx > 2:
            print(f"[ERROR] ASIC index out of range <{idx}>. Must be '1' or '2'.")
        else:
            idx += 1
        return self._get_env_sensors()[idx]

    def get_adc_temperature(self):
        """Gets the current temperature of the VSR module ADC.

        Returns:
            :obj:`str`: Formatted temperature.
        """
        return self._get_env_sensors()[4]

    def get_firmware_version(self):
        """Gets the VSR FPGA firmware version

        Returns:
            :obj:`str`: Formatted FPGA version.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG130['addr'])

    def get_customer_id(self):
        """Gets the VSR Customer ID

        Returns:
            :obj:`str`: Formatted Customer ID.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG128['addr'])

    def get_project_id(self):
        """Gets the VSR Project ID.

        Returns:
            :obj:`str`: Formatted Project ID.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG129['addr'])

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

    def write_rows1_clock(self):
        """Writes the `RowS1 Clock` value from :attr:`rows1_clock` to the VSR FPGA registers.

        Returns:
            Nothing.
        """
        wr_data = [self.rows1_clock & VSR_FPGA_REGISTERS.REG2['mask'],
                   ((self.rows1_clock >> 8) & VSR_FPGA_REGISTERS.REG3['mask'])]
        addr = VSR_FPGA_REGISTERS.REG2['addr']
        self._fpga_reg_write_burst(addr, wr_data)
        # print(f"  write_rows1_clock({self.rows1_clock}) as {[ hex(c) for c in wr_data ]}")

    def get_rows1_clock(self):
        """Gets the `RowS1 Clock` value of the :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `RowS1 Clock` value from the VSR FPGA registers. Use
           :meth:`read_rows1_clock` to read the :attr:`rows1_clock` attribute from the VSR FPGA
           registers.

        Returns:
            :obj:`int`: 16 bit :obj:`int` for the :attr:`rows1_clock`.
        """
        return self.rows1_clock

    def read_rows1_clock(self):
        """Reads the `RowS1 Clock` value from the corresponding VSR FPGA registers.

        .. warning::
           This method *DOES NOT* modify the :attr:`rows1_clock` attribute. Use
           :meth:`set_rows1_clock`.

        Returns:
            :obj:`int`: Constructed value from the `RowS1 Clock` low and high byte registers.
        """
        rows1_clock_l = self._fpga_reg_read(VSR_FPGA_REGISTERS.REG2['addr'])
        rows1_clock_h = self._fpga_reg_read(VSR_FPGA_REGISTERS.REG3['addr'])
        return int(f"0x{rows1_clock_h:02X}{rows1_clock_l:02X}", 16)

    def set_s1sph(self, val):
        """Sets the value of the `S1Sph` attribute *without* writing to the VSR FPGA register.

        .. warning::
           This method *DOES NOT* load the `S1Sph` value into the VSR FPGA register. Use
           :meth:`write_s1sph` to write :attr:`s1sph` attribute to the VSR FPGA register.

        Args:
            val (:obj:`int`): A 6 bit :obj:`int` representing the `S1Sph` value.

        Returns:
            Nothing.
        """
        self.s1sph = val & VSR_FPGA_REGISTERS.REG4['mask']

    def get_s1sph(self):
        """Gets the `S1Sph` attribute value of the :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `S1Sph` value from the VSR FPGA register. Use
           :meth:`read_s1sph` to read the current :attr:`s1sph` value from the VSR FPGA register.

        Returns:
            :obj:`int`: 6 bit :obj:`int` for the :attr:`s1sph`.
        """
        return self.s1sph

    def write_s1sph(self):
        """Writes the `S1Sph` value from :attr:`s1sph` attribute to the VSR FPGA register.

        Returns:
            Nothing.
        """
        wr_data = self.s1sph & VSR_FPGA_REGISTERS.REG4['mask']
        addr = VSR_FPGA_REGISTERS.REG4['addr']
        self._fpga_reg_write(addr, wr_data)
        # print(f"  write_s1sph({self.s1sph}) as {wr_data:X}")

    def read_s1sph(self):
        """Reads the `S1Sph` value from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`s1sph` attribute. Use :meth:`set_s1sph`.

        Returns:
            :obj:`int`: Value from the `S1Sph` VSR FPGA register.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG4['addr'])

    def set_sphs2(self, val):
        """Sets the value of `SphS2` attribute *without* writing to the VSR FPGA register.

        .. warning::
           This method *DOES NOT* load the `SphS2` value into the VSR FPGA register. Use
           :meth:`write_sphs2` to write :attr:`sphs2` attribute to the VSR FPGA register.

        Args:
            val (:obj:`int`): A 6 bit :obj:`int` representing the `SphS2` value.

        Returns:
            Nothing.
        """
        self.sphs2 = val & VSR_FPGA_REGISTERS.REG5['mask']

    def get_sphs2(self):
        """Gets the `SphS2` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `SphS2` value from the VSR FPGA register. Use
           :meth:`read_sphs2` to read the current :attr:`sphs2` value from the VSR FPGA register.

        Returns:
            :obj:`int`: 6 bit :obj:`int` for the :attr:`sphs2` attribute.
        """
        return self.sphs2

    def write_sphs2(self):
        """Writes the `SphS2` value from :attr:`sphs2` attribute to the corresponding VSR FPGA
            register.

        Returns:
            Nothing.
        """
        wr_data = self.sphs2 & VSR_FPGA_REGISTERS.REG5['mask']
        addr = VSR_FPGA_REGISTERS.REG5['addr']
        self._fpga_reg_write(addr, wr_data)
        # print(f"  write_sphs2({self.sphs2}) as {wr_data:X}")

    def read_sph2(self):
        """Reads the `SphS2` value from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`sphs2` attribute. Use :meth:`set_sphs2`.

        Returns:
            :obj:`int`: Value from the `SphS2` VSR FPGA register.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG5['addr'])

    def _write_high_gain(self):
        ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG6, "GAIN_SEL", self.read_gain())
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG6['addr'], ctrl_reg)
        # print(f" writing high gain")

    def _write_low_gain(self):
        ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG6, "GAIN_SEL", self.read_gain(), 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG6['addr'], ctrl_reg)
        # print(f" writing Low gain")

    def read_gain(self):
        """Reads the `gain` setting bit from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`gain` attribute. Use :meth:`set_gain`.

        Returns:
            :obj:`str`: Either `high` or `low`.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG6['addr'])

    def set_gain(self, val):
        """Sets the `gain` attribute of :obj:`VsrModule` *without* writing to the VSR FPGA register.

        .. warning::
           This method *DOES NOT* load the `gain` setting into the VSR FPGA register. Use
           :meth:`write_gain` to write the :attr:`gain` attribute value to the VSR FPGA register.

        Args:
            val (:obj:`str`): From either: `high` or `low`.

        Returns:
            Nothing.
        """
        if val.lower() == "high" or val.lower() == "low":
            self.gain = val.lower()
        else:
            print("[ERROR]: Unknown gain. Should be from either: 'high' or 'low'.")

    def write_gain(self):
        """Writes the `gain` bit based on the :attr:`gain` attribute to the corresponding VSR FPGA
            register.

        Returns:
            Nothing.
        """
        if self.gain.lower() == "low":
            self._write_low_gain()
        elif self.gain.lower() == "high":
            self._write_high_gain()

    def get_gain(self):
        """Gets the `gain` attribute setting for the :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `gain` setting from the VSR FPGA register. Use
           :meth:`read_gain` to read the current :attr:`gain` setting from the VSR FPGA register.

        Returns:
            :obj:`str`: The :attr:`gain` attribute of the :obj:`VsrModule`. Either `high` or `low`.
        """
        return self.gain

    def set_adc_clock_delay(self, val):
        """Sets the value of `ADC Clock Delay` to either of the :attr:`adc_clock_delay` attribute.

        .. warning::
           This method *DOES NOT* load the `ADC Clock Delay` value into the VSR FPGA register.
           Use :meth:`write_adc_clock_delay` to write :attr:`adc_clock_delay` attribute to the VSR
           FPGA register.

        Args:
            val (:obj:`int`): A 5 bit :obj:`int` representing the `ADC Clock Delay` value.

        Returns:
            Nothing.
        """
        self.adc_clock_delay = val & VSR_FPGA_REGISTERS.REG9['mask']

    def get_adc_clock_delay(self):
        """Gets the `ADC Clock Delay` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `ADC Clock Delay` value from the VSR FPGA register. Use
           :meth:`read_adc_clock_delay` to read the current :attr:`adc_clock_delay` value from the
           VSR FPGA register.

        Returns:
            :obj:`int`: 5 bit :obj:`int` for the :attr:`adc_clock_delay` attribute.
        """
        return self.adc_clock_delay

    def write_adc_clock_delay(self):
        """Writes the `ADC Clock Delay` value from :attr:`adc_clock_delay` attribute.

        Returns:
            Nothing.
        """
        wr_data = self.adc_clock_delay & VSR_FPGA_REGISTERS.REG9['mask']
        addr = VSR_FPGA_REGISTERS.REG9['addr']
        self._fpga_reg_write(addr, wr_data)
        # print(f"  write_adc_clock_delay({self.adc_clock_delay}) as {wr_data:X}")

    def read_adc_clock_delay(self):
        """Reads the `ADC Clock Delay` value from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`adc_clock_delay` attribute. Use
           :meth:`set_adc_clock_delay`.

        Returns:
            :obj:`int`: Value from the `ADC Clock Delay` VSR FPGA register.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG9['addr'])

    def set_adc_signal_delay(self, val):
        """Sets the value of `ADC Signal Delay` to either of the :attr:`adc_signal_delay` attribute.

        `ADC Signal Delay` is described in the VSR documentation as the F\ :sub:`val` and
        L\ :sub`val` signals.

        .. warning::
           This method *DOES NOT* load the `ADC Signal Delay` value into the VSR FPGA register.
           Use :meth:`write_adc_signal_delay` to write :attr:`adc_signal_delay` attribute to the
           VSR FPGA register.

        Args:
            val (:obj:`int`): A 5 bit :obj:`int` representing the `ADC Signal Delay` value.

        Returns:
            Nothing.
        """
        self.adc_signal_delay = val & VSR_FPGA_REGISTERS.REG14['mask']

    def get_adc_signal_delay(self):
        """Gets the `ADC Clock Delay` attribute value of :obj:`VsrModule`.

        `ADC Signal Delay` is described in the VSR documentation as the F\ :sub:`val` and
        L\ :sub:`val` signals.

        .. warning::
           This method *DOES NOT* read the `ADC Signal Delay` value from the VSR FPGA register. Use
           :meth:`read_adc_signal_delay` to read the current :attr:`adc_signal_delay` value from
           the VSR FPGA register.

        Returns:
            :obj:`int`: 5 bit :obj:`int` for the :attr:`adc_signal_delay` attribute.
        """
        return self.adc_signal_delay

    def write_adc_signal_delay(self):
        """Writes the `ADC Signal Delay` value from :attr:`adc_signal_delay` attribute.

        `ADC Signal Delay` is described in the VSR documentation as the F\ :sub:`val` and
        L\ :sub:`val` signals.

        Returns:
            Nothing.
        """
        wr_data = self.adc_signal_delay & VSR_FPGA_REGISTERS.REG14['mask']
        addr = VSR_FPGA_REGISTERS.REG14['addr']
        self._fpga_reg_write(addr, wr_data)
        # print(f"  write_adc_signal_delay({self.adc_signal_delay}) as {wr_data:X}")

    def read_adc_signal_delay(self):
        """Reads the `ADC Signal Delay` value from the corresponding VSR FPGA register.

        `ADC Signal Delay` is described in the VSR documentation as the F\ :sub:`val` and
        L\ :sub:`val` signals.

        .. warning::
           This method *DOES NOT* modify the :attr:`adc_signal_delay` attribute.
           Use :meth:`set_adc_signal_delay`.

        Returns:
            :obj:`int`: Value from the `ADC Signal Delay` VSR FPGA register.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG14['addr'])

    def set_sm_vcal_clock(self, val):
        """Sets the value of `State-Machine` V\ :sub:`cal` `Clock` *without* writing to VSR FPGA
            registers.

        .. warning::
           This method *DOES NOT* load the `State-Machine` V\ :sub:`cal` `Clock` value into the VSR
           FPGA registers. Use :meth:`write_sm_vcal_clock` to write :attr:`sm_vcal_clock` to the VSR
           FPGA registers.

        Args:
            val (:obj:`int`): A 15 bit :obj:`int` representing the `State-Machine`
            V\ :sub:`cal` `Clock` value.

        Returns:
            Nothing.
        """
        self.sm_vcal_clock = val

    def write_sm_vcal_clock(self):
        """Writes the `State-Machine` V\ :sub:`cal` `Clock` value from :attr:`sm_vcal_clock`
            to the VSR FPGA registers.

        Returns:
            Nothing.
        """
        wr_data = [self.sm_vcal_clock & VSR_FPGA_REGISTERS.REG24['mask'],
                   ((self.sm_vcal_clock >> 8) & VSR_FPGA_REGISTERS.REG25['mask'])]
        addr = VSR_FPGA_REGISTERS.REG24['addr']
        self._fpga_reg_write_burst(addr, wr_data)

    def get_sm_vcal_clock(self):
        """Gets the `State-Machine` V\ :sub:`cal` `Clock` value of the :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `State-Machine` V\ :sub:`cal` `Clock` value from the VSR
           FPGA registers. Use :meth:`read_sm_vcal_clock` to read the :attr:`sm_vcal_clock`
           attribute from the VSR FPGA registers.

        Returns:
            :obj:`int`: 15 bit :obj:`int` for the :attr:`sm_vcal_clock`.
        """
        return self.sm_vcal_clock

    def read_sm_vcal_clock(self):
        """Reads the `State-Machine` V\ :sub:`cal` `Clock` value from the corresponding VSR FPGA
            registers.

        .. warning::
           This method *DOES NOT* modify the :attr:`sm_vcal_clock` attribute. Use
           :meth:`set_sm_vcal_clock`.

        Returns:
            :obj:`int`: Constructed value from the `State-Machine` V\ :sub:`cal` `Clock` low and
                high byte registers.
        """
        sm_vcal_clock_l = self._fpga_reg_read(VSR_FPGA_REGISTERS.REG24['addr'])
        sm_vcal_clock_h = self._fpga_reg_read(VSR_FPGA_REGISTERS.REG25['addr'])
        return int(f"0x{sm_vcal_clock_h:02X}{sm_vcal_clock_l:02X}", 16)

    def set_sm_row_wait_clock(self, val):
        """Sets the value of `State-Machine Row Wait Clock` to either of the
            :attr:`sm_row_wait_clock` attribute.

        .. warning::
           This method *DOES NOT* load the `State-Machine Row Wait Clock` value into the VSR FPGA
           register. Use :meth:`write_sm_row_wait_clock` to write :attr:`sm_row_wait_clock`
           attribute to the VSR FPGA register.

        Args:
            val (:obj:`int`): A 8 bit :obj:`int` representing the `State-Machine Row Wait Clock`
                value.

        Returns:
            Nothing.
        """
        self.sm_row_wait_clock = val & VSR_FPGA_REGISTERS.REG27['mask']

    def get_sm_row_wait_clock(self):
        """Gets the `State-Machine Row Wait Clock` attribute value of :obj:`VsrModule`.

        .. warning::
           This method *DOES NOT* read the `State-Machine Row Wait Clock` value from the VSR FPGA
           register. Use :meth:`read_sm_row_wait_clock` to read the current
           :attr:`adc_sm_row_wait_clock` value from the VSR FPGA register.

        Returns:
            :obj:`int`: 8 bit :obj:`int` for the :attr:`sm_row_wait_clock` attribute.
        """
        return self.sm_row_wait_clock

    def write_sm_row_wait_clock(self):
        """Writes the `State-Machine Row Wait Clock` value from :attr:`sm_row_wait_clock` attribute.

        Returns:
            Nothing.
        """
        wr_data = self.sm_row_wait_clock & VSR_FPGA_REGISTERS.REG27['mask']
        addr = VSR_FPGA_REGISTERS.REG27['addr']
        self._fpga_reg_write(addr, wr_data)
        # print(f"  write_sm_row_wait_clock({self.sm_row_wait_clock}) as {wr_data:X}")

    def read_sm_row_wait_clock(self):
        """Reads the `State-Machine Row Wait Clock` value from the corresponding VSR FPGA register.

        .. warning::
           This method *DOES NOT* modify the :attr:`sm_row_wait_clock` attribute. Use
           :meth:`set_sm_row_wait_clock`.

        Returns:
            :obj:`int`: Value from the `State-Machine Row Wait Clock` VSR FPGA register.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG27['addr'])

    def select_internal_sync_clock(self):
        """Select the internal sync clock in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG1, "SYNC_CLK_SEL",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']))
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def select_external_sync_clock(self):
        """Select the external sync clock in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG1, "SYNC_CLK_SEL",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']), 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def deassert_serial_iface_rst(self):
        """De-asserts the Serial Interface Reset bit in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG1, "SERIAL_IFACE_RST",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']))
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def assert_serial_iface_rst(self):
        """Asserts the Serial Interface Reset bit in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG1, "SERIAL_IFACE_RST",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']), 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def disable_training(self):
        """De-asserts the Training Pattern Enable bit in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG1, "TRAINING_PATTERN_EN",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']))
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def enable_training(self):
        """Asserts the Training Pattern Enable bit in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG1, "TRAINING_PATTERN_EN",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']), 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def _disable_training(self):
        """De-asserts the Training Pattern Enable bit in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG1, "TRAINING_PATTERN_EN",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']))
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def _enable_training(self, time_s=0.1):
        """Asserts the Training Pattern Enable bit in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG1, "TRAINING_PATTERN_EN",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']), 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

        time.sleep(time_s)

    def start_trigger_sm(self):
        ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG10, "TRIGGER_START_SM",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG10['addr']), 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def enable_plls(self, pll=True, adc_pll=True):
        """Enables the VSR PLLs.

        Args:
            pll (:obj:`bool`, optional): Enable the PLL, otherwise leave untouched.
                Default: `True`.
            adc_pll (:obj:`bool`, optional): Enable the ADC PLL, otherwise leave untouched.
                Default: `True`.

        Returns:
            Nothing.
        """
        ctrl_reg = self._fpga_reg_read(VSR_FPGA_REGISTERS.REG7['addr'])
        if pll:
            ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG7, "ENABLE_PLL", ctrl_reg, 1)
        if adc_pll:
            ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG7, "ENABLE_ADC_PLL", ctrl_reg, 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG7['addr'], ctrl_reg)

    def start_sm_on_rising_edge(self):
        """Start the State-Machine on the rising edge of the ADC clock.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG20, "SM_START_EDGE",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG20['addr'],))
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG20['addr'], ctrl_reg)

    def start_sm_on_falling_edge(self):
        """Start the State-Machine on the falling edge of the ADC clock.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG20, "SM_START_EDGE",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG20['addr']), 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG20['addr'], ctrl_reg)

    def set_dc_control_bits(self, capt_avg_pict=True, vcal_pulse_disable=True,
                            spectroscopic_mode_en=True):
        """Sets selected bits in the DC Control register.

        Args:
            capt_avg_pict (:obj:`bool`, optional): Sets the corresponding field, otherwise leaves
                it untouched. Default: `True`.
            vcal_pulse_disable (:obj:`bool`, optional): Sets the corresponding field, otherwise
                leaves it untouched. Default: `True`.
            spectroscopic_mode_en (:obj:`bool`, optional): Sets the corresponding field, otherwise
                leaves it untouched. Default: `True`.

        Returns:
            Nothing.
        """
        # print(f"  VSR.set_dc_control_bits({capt_avg_pict}, {vcal_pulse_disable}, {spectroscopic_mode_en})")
        ctrl_reg = self._fpga_reg_read(VSR_FPGA_REGISTERS.REG36['addr'])
        if capt_avg_pict:
            ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG36, "CAPT_AVG_PICT", ctrl_reg, 1)
        if vcal_pulse_disable:
            ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG36, "VCAL_PULSE_DISABLE", ctrl_reg, 1)
        if spectroscopic_mode_en:
            ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG36, "SPECTROSCOPIC_MODE_EN",
                                      ctrl_reg, 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG36['addr'], ctrl_reg)

    def clr_dc_control_bits(self, capt_avg_pict=True, vcal_pulse_disable=True,
                            spectroscopic_mode_en=True):
        """Clears selected bits in the DC Control register.

        Args:
            capt_avg_pict (:obj:`bool`, optional): Clears the corresponding field, otherwise
                leaves it untouched. Default: `True`.
            vcal_pulse_disable (:obj:`bool`, optional): Clears the corresponding field, otherwise
                leaves it untouched. Default: `True`.
            spectroscopic_mode_en (:obj:`bool`, optional): Clears the corresponding field, otherwise
                leaves it untouched. Default: `True`.

        Returns:
            Nothing.
        """
        # print(f"  VSR.clr_dc_control_bits({capt_avg_pict}, {vcal_pulse_disable}, {spectroscopic_mode_en})")
        ctrl_reg = self._fpga_reg_read(VSR_FPGA_REGISTERS.REG36['addr'])
        if capt_avg_pict:
            ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG36, "CAPT_AVG_PICT", ctrl_reg)
        if vcal_pulse_disable:
            ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG36, "VCAL_PULSE_DISABLE", ctrl_reg)
        if spectroscopic_mode_en:
            ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG36, "SPECTROSCOPIC_MODE_EN", ctrl_reg)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG36['addr'], ctrl_reg)

    def enable_all_columns(self, asic=1):
        """Writes the masks to enable Read and Power for Columns of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG174['addr'], VSR_FPGA_REGISTERS.REG194['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG77['addr'], VSR_FPGA_REGISTERS.REG97['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all_as_value=0xff))

    def set_all_columns(self, col_mask, asic=1):
        """Writes the supplied mask to enable Read and Power for Columns of the target ASIC.

        Args:
            col_mask (:obj:`list of :obj:`int`) A :obj:`list` of 8 bit integers with represent
                the mask to set.
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG174['addr'], VSR_FPGA_REGISTERS.REG194['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG77['addr'], VSR_FPGA_REGISTERS.REG97['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(row_col_mask=col_mask))

    def enable_all_rows(self, asic=1):
        """Writes the masks to enable Read and Power for Rows of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG144['addr'], VSR_FPGA_REGISTERS.REG164['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG47['addr'], VSR_FPGA_REGISTERS.REG67['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all_as_value=0xff))

    def set_all_rows(self, row_mask, asic=1):
        """Writes the supplied mask to enable Read and Power for Rows of the target ASIC.

        Args:
            row_mask (:obj:`list of :obj:`int`) A :obj:`list` of 8 bit integers with represent
                the mask to set.
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG144['addr'], VSR_FPGA_REGISTERS.REG164['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG47['addr'], VSR_FPGA_REGISTERS.REG67['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(row_col_mask=row_mask))

    def disable_all_columns(self, asic=1):
        """Writes the masks to disable Read and Power for Columns of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG174['addr'], VSR_FPGA_REGISTERS.REG194['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG77['addr'], VSR_FPGA_REGISTERS.REG97['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all_as_value=0x0))

    def disable_all_rows(self, asic=1):
        """Writes the masks to disable Read and Power for Rows of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG144['addr'], VSR_FPGA_REGISTERS.REG164['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG47['addr'], VSR_FPGA_REGISTERS.REG67['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all_as_value=0x0))

    def enable_all_columns_cal(self, asic=1):
        """Writes the masks to enable Calibration for Columns of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG184['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG87['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all_as_value=0xff))

    def set_all_columns_cal(self, asic=1):
        """Writes the supplied mask to enable Calibration for Columns of the target ASIC.

        Args:
            col_mask (:obj:`list of :obj:`int`) A :obj:`list` of 8 bit integers with represent
                the mask to set.
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG184['addr']]
            col_mask = self.column_calibration_mask_asic2
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG87['addr']]
            col_mask = self.column_calibration_mask_asic1
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(row_col_mask=col_mask))
        if self.debug:
            print("[DEBUG]: ASIC{} VsrModule.set_all_columns_cal: {} start_address: {} ({})".format(
                asic, [hex(c) for c in col_mask], en_start_addrs[0], en_start_addrs))

    def disable_all_columns_cal(self, asic=1):
        """Writes the masks to disable Calibration for Columns of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG184['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG87['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all_as_value=0xff))

    def set_all_rows_cal(self, asic=1):
        """Writes the supplied mask to enable Calibration for Rows of the target ASIC.

        Args:
            row_mask (:obj:`list of :obj:`int`) A :obj:`list` of 8 bit integers with represent
                the mask to set.
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG154['addr']]
            row_mask = self.row_calibration_mask_asic2
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG57['addr']]
            row_mask = self.row_calibration_mask_asic1
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(row_col_mask=row_mask))
        if self.debug:
            print("[DEBUG]: ASIC{} VsrModule.set_all_rows_cal: {} start_address: {}".format(
                asic, [hex(c) for c in row_mask], en_start_addrs))

    def enable_all_rows_cal(self, asic=1):
        """Writes the masks to enable Calibration for Rows of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        # print(" enable_all_rows_cal: 1693, asic=", asic)
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG154['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG57['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all_as_value=0xff))

    def disable_all_rows_cal(self, asic=1):
        """Writes the masks to disable Calibration for Rows of the target ASIC.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        if asic == 2:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG154['addr']]
        else:
            en_start_addrs = [VSR_FPGA_REGISTERS.REG57['addr']]
        for s_addr in en_start_addrs:
            self._fpga_reg_write_burst(s_addr, set_row_column_mask(all_as_value=0x0))

    def configure_asic(self, asic=1):
        """Enables the target ASIC by applying the corresponding enable and calibration settings.

        Args:
            asic (:obj:`int`, optional): Index for the target ASIC. Should be `1` or `2`.
                Default: `1`.

        Returns:
            Nothing.
        """
        self.enable_all_columns(asic=asic)
        if self.vcal_enabled:
            self.set_all_columns_cal(asic=asic)
            self.set_all_rows_cal(asic=asic)
        else:
            self.disable_all_columns_cal(asic=asic)
            self.disable_all_rows_cal(asic=asic)
        self.enable_all_rows(asic=asic)

    def set_dac_vcal(self, val):
        """Sets the value of V\ :sub:`cal` attribute *without* writing to the VSR DAC.

        .. warning::
           This method *DOES NOT* load the V\ :sub:`cal` value into the VSR DAC.
           Use :meth:`write_dac_values` to write all `DAC` attributes to the VSR DAC.

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
           This method *DOES NOT* read the V\ :sub:`cal` value from the VSR DAC. There is no method
           to read each of the current DAC values from the VSR DAC. The only way to retrieve the
           current values of the VSR DAC is to perform a :meth:`write_dac_values` and process the
           returned :obj:`dict`.

        Returns:
            :obj:`int`: 12 bit :obj:`int` for the :attr:`dac_vcal` attribute.
        """
        return self.dac_vcal

    def set_dac_umid(self, val):
        """Sets the value of U\ :sub:`mid` attribute *without* writing to the VSR DAC.

        .. warning::
           This method *DOES NOT* load the U\ :sub:`mid` value into the VSR DAC. Use
           :meth:`write_dac_values` to write all `DAC` attributes to the VSR DAC.

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
           This method *DOES NOT* read the U\ :sub:`mid` value from the VSR DAC. There is no
           method to read each of the current DAC values from the VSR DAC. The only way to
           retrieve the current values of the VSR DAC is to perform a :meth:`write_dac_values`
           and process the returned :obj:`dict`.

        Returns:
            :obj:`int`: 12 bit :obj:`int` for the :attr:`dac_umid` attribute.
        """
        return self.dac_umid

    def set_dac_hv(self, val):
        """Sets the value of DAC `HV` attribute *without* writing to the VSR DAC.

        .. warning::
           This method *DOES NOT* load the `HV` value into the VSR DAC. Use :meth:`write_dac_values`
           to write all `DAC` attributes to the VSR DAC.

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
           This method *DOES NOT* read the `HV` value from the VSR DAC. There is no method to read
           each of the current DAC values from the VSR DAC. The only way to retrieve the current
           values of the VSR DAC is to perform a :meth:`write_dac_values` and process the returned
           :obj:`dict`.

        Returns:
            :obj:`int`: 12 bit :obj:`int` for the :attr:`dac_hv` attribute.
        """
        return self.dac_hv

    def set_dac_det_ctrl(self, val):
        """Sets the value of DAC `DET Control` attribute *without* writing to the VSR DAC.

        .. warning::
           This method *DOES NOT* load the `DET Control` value into the VSR DAC. Use
           :meth:`write_dac_values` to write all `DAC` attributes to the VSR DAC.

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
           This method *DOES NOT* read the `DET Control` value from the VSR DAC. There is no method
           to read each of the current DAC values from the VSR DAC. The only way to retrieve the
           current values of the VSR DAC is to perform a :meth:`write_dac_values` and process the
           returned :obj:`dict`.

        Returns:
            :obj:`int`: 12 bit :obj:`int` for the :attr:`dac_det_ctrl` attribute.
        """
        return self.dac_det_ctrl

    def write_dac_values(self, addr=False):
        """Writes each of the DAC based attributes to the VSR DAC.

        Writes the following attributes: :attr:`dac_vcal`, :attr:`dac_umid`, :attr:`dac_hv`,
        :attr:`dac_det_ctrl`, and :attr:`dac_reserve2`.

        .. note::
           The only way to return values from the VSR DAC is by performing a
           :meth:`write_dac_values`. This method will return a :obj:`dict` of all values
           **without** overwriting the VSR DAC based attributes.

        Args:
            addr (:obj:`int`): Hardware address to target if set, otherwise own VSR module's.

        Returns:
            :obj:`dict` of key/values pairs, where the keys are: `vcal`, `umid`, `hv`, `det_ctrl`
            and `reserve2`.
        """
        # print(f" *** writ_dac_values, self.dac_vcal: 0x{self.dac_vcal:X}")
        address = self.addr
        if addr:
            address = addr
        dac_mask = 0xFFF  # Limit the DAC to 12 bits.
        nof_bytes = 2  # Each value unpacks into this many bytes.
        vsr_cmd = get_vsr_cmd_char("write_dac_values")
        dac_values = [self.dac_vcal, self.dac_umid, self.dac_hv, self.dac_det_ctrl,
                      self.dac_reserve2]
        wr_cmd = list()
        tmp_dict = dict()
        for val in dac_values:
            wr_cmd.extend(unpack_data_for_vsr_write(val, mask=dac_mask, nof_bytes=nof_bytes))
        # print("Send to UART: {} ".format(' '.join("0x{0:02X}".format(x) for x in wr_cmd)))
        self._uart_write(address, vsr_cmd, wr_cmd)
        resp = self._rdma_ctrl_iface.uart_read()
        resp = self._check_uart_response(resp)
        tmp_dict['vcal'] = resp[0:4]
        tmp_dict['umid'] = resp[4:8]
        tmp_dict['hv'] = resp[8:12]
        tmp_dict['det_ctrl'] = resp[12:16]
        tmp_dict['reserve2'] = resp[16:20]
        return tmp_dict

    def disable_sm(self):
        """De-asserts the State-Machine Enable bit in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.clr_field(VSR_FPGA_REGISTERS.REG1, "SM_EN",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']))
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def enable_sm(self):
        """Asserts the State-Machine Enable bit in the control register.

        Returns:
            Nothing.
        """
        ctrl_reg = rdma.set_field(VSR_FPGA_REGISTERS.REG1, "SM_EN",
                                  self._fpga_reg_read(VSR_FPGA_REGISTERS.REG1['addr']), 1)
        self._fpga_reg_write(VSR_FPGA_REGISTERS.REG1['addr'], ctrl_reg)

    def preconfigure(self, **kwargs):
        """Preconfigure the :obj:`VsrModule` ready for :meth:`initialise`.

        Keyword Args:
            rows1_clock (:obj:`int`, optional): Default value: loaded on
                :meth:`VsrModule.__init__`.
            s1sph (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            sphs2 (:obj:`int`, optional): Default value: loaded on :meth:`VsrModule.__init__`.
            gain (:obj:`str`, optional): `high` or `low`. Default value: loaded on
                :meth:`VsrModule.__init__`.
            adc_clock_delay (:obj:`int`, optional): Default value: loaded on
                :meth:`VsrModule.__init__`.
            adc_signal_delay (:obj:`int`, optional): Default value: loaded on
                :meth:`VsrModule.__init__`.
            sm_vcal_clock (:obj:`int`, optional): Default value: loaded on
                :meth:`VsrModule.__init__`.
            sm_row_wait_clock (:obj:`int`, optional): Default value: loaded on
                :meth:`VsrModule.__init__`.

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
            dac_det_ctrl (:obj:`int`, optional): Default value: loaded on
                :meth:`VsrModule.__init__`.

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
           This method *DOES NOT* load the `Output Phase` value into the VSR ADC. Use
           :meth:`write_adc_values` to write all `DAC` attributes to the VSR DAC.

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
        """Gets the `ADC Register Address` and `Output Phase` attribute value combination for
            the AD9252 ADC.

        .. warning::
           This method *DOES NOT* read the ADC `Output Phase` value from the VSR ADC. There is no
           method to read any of the current ADC values from the VSR ADC. The only way to retrieve
           the current value of a VSR ADC register is to perform a :meth:`write_adc_values` and
           process the returned :obj:`dict`.

        Returns:
            :obj:`list` of :obj:`int`: 8 bit `ADC Reg Address` and 8 bit `Output Phase` pair
            for AD9252 ADC.
        """
        adc_output_phase_reg_addr = 0x16
        return [adc_output_phase_reg_addr, self.adc_output_phase]

    def write_adc_values(self, add_dat_pair):
        """Writes an ADC Register Address/Data :obj:`list` pair to the VSR ADC.

        Args:
            add_dat_pair (:obj:`list` of :obj:`int`) ADC Register Address/Data combination pair
            to write to VSR ADC.

        Returns:
            Nothing.
        """
        vsr_cmd = get_vsr_cmd_char("write_adc_values")
        wr_cmd = list()
        for b in add_dat_pair:
            wr_cmd.extend(convert_to_ascii(b, zero_pad=True))
        self._uart_write(self.addr, vsr_cmd, wr_cmd)
        resp = self._rdma_ctrl_iface.uart_read()
        resp = self._check_uart_response(resp)
        return resp[0:4]

    def preconfigure_adc(self, **kwargs):
        """Preconfigure the ADC of :obj:`VsrModule` ready for :meth:`initialise`.

        The register address/values are raw, and can be found in the
        :download:`AD9252 datasheet <../../../docs/references/ad9252.pdf>`.

        Keyword Args:
            adc_output_phase (:obj:`int`, optional): Default value: loaded on
            :meth:`VsrModule.__init__`.

        Returns:
            Nothing.
        """
        self.set_adc_output_phase(kwargs.get('adc_output_phase', self.adc_output_phase))

    def init_adc(self):
        """Initialisation sequence for the VSR ADC.

        Returns:
            Nothing.
        """
        self.disable_adc()
        self.disable_sm()
        self.enable_sm()
        self.enable_adc_and_dac()
        self.write_adc_values(self.get_adc_output_phase())

    def initialise(self, training_delay=0.1):
        """Initialise the VSR.

        Before running :meth:`initialise` ensure the correct configuration is loaded using
        :meth:`preconfigure`.

        Returns:
            Nothing.
        """
        print(f"[INFO]: VSR{self.slot}: Starting Initialisation...")
        self.select_external_sync_clock()
        self.enable_plls(pll=True, adc_pll=True)
        self.write_rows1_clock()
        self.write_s1sph()
        self.write_sphs2()
        self.write_gain()
        self.write_adc_clock_delay()
        self.write_adc_signal_delay()
        self.write_sm_row_wait_clock()
        self.start_sm_on_falling_edge()
        # Asserting serial interface reset bit corresponds with line 1196 (enable LVDS interface):
        # https://github.com/stfc-aeg/hexitec-detector/blob/761ff3aa1008de4fc3fac1b7fdb5c02880168371/control/src/hexitec/HexitecFem.py
        self.assert_serial_iface_rst()  # 1196
        asics = [1, 2]
        for asic in asics:
            self.configure_asic(asic=asic)  # 1206
        current_dac_vals = self.write_dac_values()  # 1208
        self.init_adc()  # 1216
        self.set_dc_control_bits(capt_avg_pict=True, vcal_pulse_disable=self.vcal_enabled,
                                 spectroscopic_mode_en=False)  # 1226
        # \TODO: Check if the spectroscopic_mode_en is already enabled or if it needs to be
        #        toggled off/on via the previous :meth:`write_dc_control_bits`.
        # self.set_dc_control_bits(capt_avg_pict=False, vcal_pulse_disable=False,
        #                          spectroscopic_mode_en=True)  # 1229
        print(f"[INFO]: VSR{self.slot}: Starting LVDS Training...")
        # self.enable_training(time_s=training_delay)  # 1231
        self._enable_training(time_s=training_delay)
        # self.disable_training()
        # self._disable_training()
        self.write_sm_vcal_clock()  # 1238 & 1240
        self.clr_dc_control_bits(capt_avg_pict=False, vcal_pulse_disable=self.vcal_enabled,
                                 spectroscopic_mode_en=False)  # 1243
        print(f"[INFO]: VSR{self.slot}: Finished Initialisation.")

    def get_power(self):
        vsr_d = list()  # empty VSR data list to pass to: self.uart_write()
        self._uart_write(self.addr, 0x50, vsr_d)
        resp = self._rdma_ctrl_iface.uart_read()
        resp = self._check_uart_response(resp)
        MAX1239_INT_REF_V = 2.048
        U10_REF_V = 3.3

        # calc_hv_monitor_rail = round((convert_from_ascii(resp[36:40]) * 1621.65 ) - 1043.22,2)
        calc_3v3 = convert_from_ascii(resp[36:40]) * (MAX1239_INT_REF_V / 4095)
        u1 = convert_from_ascii(resp[0:4]) * (calc_3v3 / 2 ** 12)
        calc_hv_monitor_rail = round(u1 * 1621.65 - 1043.22, 2)    # Removed " + 56 "
        calc_1v2 = round(convert_from_ascii(resp[4:8]) * (U10_REF_V / 2**12), 2)
        calc_1v8 = round(convert_from_ascii(resp[8:12]) * (U10_REF_V / 2**12), 2)
        # reserved
        calc_2v5 = round(convert_from_ascii(resp[16:20]) * (U10_REF_V / 2**12), 2)
        calc_3v3_ln = round(convert_from_ascii(resp[20:24]) * (U10_REF_V / 2**12), 2)
        calc_1v65 = round(convert_from_ascii(resp[24:28]) * (U10_REF_V / 2**12), 2)
        calc_1vb8 = round(convert_from_ascii(resp[28:32]) * (U10_REF_V / 2**12), 2)
        calc_3v8 = round(convert_from_ascii(resp[32:36]) * (U10_REF_V / 2**12), 2)
        calc_3v3 = round(convert_from_ascii(resp[36:40]) * (MAX1239_INT_REF_V / 2 ** 12), 2)

        # reserved
        # reserved
        ret_tup = f"{calc_hv_monitor_rail}V", f"{calc_1v2}V",\
            f"{calc_1v8}V", f"{calc_2v5}V", \
            f"{calc_3v3_ln}V", f"{calc_1v65}V", \
            f"{calc_1vb8}V", f"{calc_3v8}V", \
            f"{calc_3v3}V"
        return ret_tup

    def read_pll_status(self):
        """Reads the `PLL locked` value from the VSR FPGA Registered 137.

        Returns:
            :obj:`int`: Value of 'PLL locked', bit 1 in register 0x89.
        """
        return self._fpga_reg_read(VSR_FPGA_REGISTERS.REG137['addr'])

    def get_power_sensors(self):
        vsr_d = list()  # empty VSR data list to pass to: self.uart_write()
        self._uart_write(self.addr, get_vsr_cmd_char("get_pwr"), vsr_d)
        resp = self._rdma_ctrl_iface.uart_read()
        sensors_values = self._check_uart_response(resp)
        hv_value = self.get_hv_value(sensors_values)
        return hv_value

    def get_hv_value(self, sensors_values):
        """Take the full string of voltages and extract the HV value."""
        try:
            # Calculate V10, the 3.3V reference voltage
            reference_voltage = convert_from_ascii(sensors_values[36:40]) * (2.048 / 4095)
            # Calculate HV rails
            u1 = convert_from_ascii(sensors_values[:4]) * (reference_voltage / 2**12)
            # Apply conversion gain # Added 56V following HV tests
            hv_monitoring_voltage = u1 * 1621.65 - 1043.22 + 56
            return hv_monitoring_voltage
        except ValueError as e:
            print(f"[ERROR]: VSR{self.slot}: Error obtaining HV value: {e}")
            return -1

    def hv_on(self, hv_msb, hv_lsb):
        """Switch HV on."""
        hv_address = 0xC0
        self.enable_vsr(init_time=0.5, addr=hv_address)
        current_dac_vals = self.write_power_board_dac_values(hv_address, hv_msb, hv_lsb)

    def hv_off(self):
        """Switch HV off."""
        hv_address = 0xC0
        self.disable_vsr(addr=hv_address)

    def write_power_board_dac_values(self, addr, hv_msb, hv_lsb):
        """Writes the DAC based HV attribute to the Power Board DAC.

        Args:
            addr (:obj:`int`): Hardware address to target if set, otherwise own VSR module's.
            hv_msb (:obj:`int`): Most significant byte of HV bias level
            hv_lsb (:obj:`int`): Least significant byte of HV bias level

        Returns:
            :obj:`dict` of key/values pairs, where the key is: `hv`.
        """
        address = self.addr
        if addr:
            address = addr
        vsr_cmd = get_vsr_cmd_char("write_dac_values")
        # padding = [0x30, 0x30, 0x30, 0x30]
        dac_values = [  # padding, padding, padding,
            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
            0x30, 0x30, 0x30, 0x30,
            # Actual HV values:
            hv_msb[0], hv_msb[1], hv_lsb[0], hv_lsb[1],
            # padding, padding, padding, padding]
            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30,
            0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30]
        wr_cmd = list()
        tmp_dict = dict()
        for val in dac_values:
            wr_cmd.append(val)
        # print("Send to UART: {} ".format(' '.join("0x{0:02X}".format(x) for x in wr_cmd)))
        self._uart_write(address, vsr_cmd, wr_cmd)
        resp = self._rdma_ctrl_iface.uart_read()
        resp = self._check_uart_response(resp)
        tmp_dict['hv'] = resp[12:16]
        return tmp_dict

    def write_sync_reset_daq(self):
        """Writes SYNC clock, reset interface to the VSR FPGA register.
            i.e. enabling these two bits in register 0x01:
        4 Use SYNC clock from DAQ Board
        5 0 -> Reset serial Interface to DAQ Board

        Returns:
            Nothing.
        """
        wr_data = 0x30 & VSR_FPGA_REGISTERS.REG1['mask']
        addr = VSR_FPGA_REGISTERS.REG1['addr']
        self._fpga_reg_write(addr, wr_data)

    def write_sync_sm_start_trigger(self):
        """Writes synchronized SM start to the VSR FPGA register.
            i.e. write first bit in register 0x0A:
        0 enable synchronized SM start via Trigger

        Returns:
            Nothing.
        """
        wr_data = 0x1 & VSR_FPGA_REGISTERS.REG10['mask']
        addr = VSR_FPGA_REGISTERS.REG10['addr']
        self._fpga_reg_write(addr, wr_data)

    def enable_vcal(self, vcal_enabled):
        """Enables the VSR VCAL and calibration masks.

        Args:
            vcal_enabled (:obj:`bool`, optional): Enable the VCAL.

        Returns:
            Nothing.
        """
        self.vcal_enabled = vcal_enabled

    def set_column_calibration_mask(self, column_calibration_mask, asic):
        """Sets the VSR column calibration mask.

        Args:
            column_calibration_mask (:obj:`list` of :obj:`int`): Column calibration mask.

        Returns:
            Nothing.
        """
        if self.debug:
            print("[DEBUG]: ASIC{} VsrModule.set_column_calibration_mask: {}".format(
                asic, [hex(c) for c in column_calibration_mask]))
        if asic == 1:
            self.column_calibration_mask_asic1 = column_calibration_mask
        else:
            self.column_calibration_mask_asic2 = column_calibration_mask

    def set_row_calibration_mask(self, row_calibration_mask, asic):
        """Sets the VSR row calibration mask.

        Args:
            row_calibration_mask (:obj:`list` of :obj:`int`): Row calibration mask.

        Returns:
            Nothing.
        """
        if self.debug:
            print("[DEBUG]: ASIC{} VsrModule.set_row_calibration_mask: {}".format(
                asic, [hex(c) for c in row_calibration_mask]))
        if asic == 1:
            self.row_calibration_mask_asic1 = row_calibration_mask
        else:
            self.row_calibration_mask_asic2 = row_calibration_mask
