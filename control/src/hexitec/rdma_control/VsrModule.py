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
    from rdma_control.rdma_register_helpers import *
except ModuleNotFoundError:
    from RDMA_REGISTERS import *
    from rdma_register_helpers import *


def get_vsr_cmd_char(code):
    """Converts operation into corresponding VSR command character.

        Args:
            code (:obj:`str`): from:
                `"start"`, `"end"`, `"resp"`, `"bcast"`, `"whois"`, '"get_pwr"', `"get_env"`,
                '"send_reg_value"', '"read_vsr"', '"enable"', '"disable"', `"adc_dac_ctrl"`.

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
    elif code.lower() == "send_reg_value":
        return 0x40
    elif code.lower() == "read_vsr":
        return 0x41
    elif code.lower() == "enable":
        return 0xE3
    elif code.lower() == "disable":
        return 0xE2
    elif code.lower() == "adc_dac_ctrl":
        return 0x55
    else:
        return 0x23


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
        addr_mapping (:obj:`dict`, optional): Key/value pairs cross-referencing :attr:`slot` with hardware address of the
            corresponding VSR module. Default: `None`. If an address mapping is not supplied the :obj:`VsrAssembly` will
            perform a :meth:`VsrAssembly.lookup` to determine the configuration of the attached system.

    Attributes:
        addr_mapping (:obj:`dict`): A copy of the address mapping configuration, either provided or determined at
            initialisation.
        slot (:obj:`int`): Slot number. Set to '0' for global addressing and control.
        addr (:obj:`int`): Hardware address of VSR module, hard-coded on each VSR module.

    """
    def __init__(self, rdma_ctrl_iface, slot=0, addr_mapping=None):
        self._rdma_ctrl_iface = rdma_ctrl_iface
        self.slot = slot
        if addr_mapping is None:
            self.addr_mapping = self.lookup(init_time=15)
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


    def _uart_write(self, vsr_a, vsr_cmd, wr_d, cmd_no=0):
        """Wraps UART Tx data with a VSR command header for writing to aSpect based VSR modules
        """
        wr_cmd = list()
        wr_cmd.append(get_vsr_cmd_char("start"))
        wr_cmd.append(vsr_a)
        wr_cmd.append(vsr_cmd)

        for d in wr_d:
            wr_cmd.append(d)
        wr_cmd.append(get_vsr_cmd_char("end"))
        # print(f"[DEBUG]: MR' VsrMod._uart_write: {[ hex(c) for c in wr_cmd ]}")
        self._rdma_ctrl_iface.uart_write(wr_cmd, cmd_no=cmd_no)


    def _get_status(self, hv=False, all_vsrs=False, cmd_no=0):
        """Returns status of power/high-voltage enable signals for the selected VSR(s).

        Args:
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
        if self.slot > nof_modules:
            print(f"[ERROR]: Requested VSR module: <{self.slot}> exceeds total number of modules available: <{nof_modules}>")
            return 0

        if all_vsrs:
            vsr_mod = range(1, nof_modules + 1)
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
        # print(f"[DEBUG]: VSR who_is? response: {[hex(c) for c in resp]}")
        # check response:
        if resp[-2:] == hv_power_module_id:
            # print(f"[INFO]: Power/HV module response: <OK>")
            if len(resp) > len(hv_power_module_id):
                stripped_resp = resp[:-2]
                if stripped_resp[-1] == whois_end_char:
                    # print(f"[INFO]: VSR address response: <OK>")
                    vsr_addrs = stripped_resp[:-1]
                    # print(f"[INFO]: VSR address(es): {[hex(i) for i in vsr_addrs]}")
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
            init_time (:obj:`int`, optional): wait time, in seconds, to allow each VSR to initialise before issuing the
                `who_is?` command. Default: `15`.
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
            self._ctrl(vsr_mod=v + 1, op="disable", init_time=init_time, cmd_no=cmd_no)
            self._get_status(vsr_mod=v + 1, cmd_no=cmd_no)

        # print(f"[DEBUG]: address mapping from lookup: {vsr_addr_map}")
        return vsr_addr_map


    def _ctrl(self, all_vsrs=False, op="disable", init_time=15, cmd_no=0):
        """Control the selected VSR modules(s).

        This controls the power and high-voltage enable signals between the FPGA and VSR module slots.

        Args:
            all_vsrs (:obj:`bool`, optional): Control all VSR modules. Default: `False`.
            op (:obj:`str`, optional): Operation to perform. From: `enable`, `disable`, `hv_enable`, `hv_disable`.
                Default: `disable`.
            init_time (:obj:`int`, optional): wait time, in seconds, to allow each VSR to initialise before issuing the
                `who_is?` command. Default: `15`.
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
        return self._ctrl(all_vsrs=all_vsrs, op="enable", init_time=15, cmd_no=0)


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


    def _convert_from_ascii(self, d):
        return int("".join([chr(c) for c in d]), 16)


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
        addr_mapping (:obj:`dict`, optional): Key/value pairs cross-referencing :attr:`slot` with hardware address of the
            corresponding VSR module. Default: `None`. If an address mapping is not supplied the :obj:`VsrModule` will
            perform a :meth:`VsrModule.lookup` to determine the configuration of the attached system.

    Attributes:
        addr_mapping (:obj:`dict`): A copy of the address mapping configuration, either provided or determined at
            initialisation.
        slot (:obj:`int`): Slot number for corresponding VSR module, indexed from '1'.
        addr (:obj:`int`): Hardware address of VSR module, hard-coded on each VSR module.


    """
    def __init__(self, rdma_ctrl_iface, slot=1, addr_mapping=None):
        super().__init__(rdma_ctrl_iface, slot=slot, addr_mapping=addr_mapping)


    def _get_env_sensors(self, cmd_no=0):
        vsr_d = list()  # empty VSR data list to pass to: self.uart_write()
        self._uart_write(self.addr, get_vsr_cmd_char("get_env"), vsr_d, cmd_no=cmd_no)
        time.sleep(1)
        resp = self._rdma_ctrl_iface.uart_read(cmd_no=cmd_no)
        resp = self._check_uart_response(resp)
        calc_ambient_temp = round(((self._convert_from_ascii(resp[0:4]) / 2**16) * 175.72) - 46.85, 3)
        calc_humidity = round(((self._convert_from_ascii(resp[4:8]) / 2**16) * 125) + 6, 3)
        calc_asic1_temp = round(self._convert_from_ascii(resp[8:12]) * 0.0625, 2)
        calc_asic2_temp = round(self._convert_from_ascii(resp[12:16]) * 0.0625, 2)
        calc_adc_temp = round(self._convert_from_ascii(resp[16:20]) * 0.0625, 2)
        return calc_ambient_temp, calc_humidity, calc_asic1_temp, calc_asic2_temp, calc_adc_temp

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
            reference_voltage = self._convert_from_ascii(sensors_values[36:40]) * (2.048 / 4095)
            # Calculate HV rails
            u1 = self._convert_from_ascii(sensors_values[:4]) * (reference_voltage / 2**12)
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
        self._uart_write(self.addr, get_vsr_cmd_char("read_vsr"), [reg_addr_h, reg_addr_l], cmd_no=cmd_no)
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
        # self._uart_write(self.addr, get_vsr_cmd_char("send_reg_value"),
        #                  [address_h, address_l, value_h, value_l], cmd_no=cmd_no)

    def read_and_response(self, address_h, address_l, delay=False, cmd_no=0):
        """Send a read and read the reply."""
        self._uart_write(self.addr, get_vsr_cmd_char("read_vsr"), [address_h, address_l], cmd_no=cmd_no)
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

        self._uart_write(self.addr, get_vsr_cmd_char("send_reg_value"),
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
