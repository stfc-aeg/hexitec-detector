# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.

# *** This file was AUTO-GENERATED. Modifications to this file will be overwritten. ***
"""IC ID and Register dictionaries extracted from XML2VHDL formatted `xml` memory-map generation output file."""
HEXITEC_2X6_ID = {'addr_offset': 0, 'fields': [], 'name': 'HEXITEC_2X6_ID'}
"""XML2VHDL IC References generated from `XML2VHDL` output.

===================  ===============
**ID**               **Offset
HEXITEC_2X6_ID       ``0x0000_0000``
BOARD_BUILD_INFO_ID  ``0x0000_8000``
UDP_CORE_0_0_ID      ``0x0002_0000``
UDP_CORE_0_1_ID      ``0x0002_2000``
UDP_CORE_0_2_ID      ``0x0002_4000``
QSFP_1_ID            ``0x0008_0000``
QSFP_2_ID            ``0x0008_1000``
===================  ===============
"""
BOARD_BUILD_INFO_ID = {'addr_offset': 32768, 'fields': [], 'name': 'BOARD_BUILD_INFO_ID'}
UDP_CORE_0_0_ID = {'addr_offset': 131072, 'fields': [], 'name': 'UDP_CORE_0_0_ID'}
UDP_CORE_0_1_ID = {'addr_offset': 139264, 'fields': [], 'name': 'UDP_CORE_0_1_ID'}
UDP_CORE_0_2_ID = {'addr_offset': 147456, 'fields': [], 'name': 'UDP_CORE_0_2_ID'}
QSFP_1_ID = {'addr_offset': 524288, 'fields': [], 'name': 'QSFP_1_ID'}
QSFP_2_ID = {'addr_offset': 528384, 'fields': [], 'name': 'QSFP_2_ID'}

HEXITEC_2X6_READBACK = { 'addr': 4,
  'description': 'Readback register',
  'fields': [ { 'description': '100MHz FPGA Clock locked',
                'is_bit': True,
                'mask': 1,
                'name': 'FPGA_CLK_LOCKED',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': '156.25MHz FMC Reference Clock locked',
                'is_bit': True,
                'mask': 2,
                'name': 'FMC_REFCLK_LOCKED',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Bank 116 QPLL locked (FMC QSFP1)',
                'is_bit': True,
                'mask': 4,
                'name': 'QPLL_LOCKED_B116',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Bank 115 QPLL locked (FMC QSFP2)',
                'is_bit': True,
                'mask': 8,
                'name': 'QPLL_LOCKED_B115',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'FMC QSFP1 module present (active-high)',
                'is_bit': True,
                'mask': 16,
                'name': 'FMC_QSFP1_MODPRES',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'FMC QSFP2 module present (active-high)',
                'is_bit': True,
                'mask': 32,
                'name': 'FMC_QSFP2_MODPRES',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'FMC QSFP1 lane up (PCS Block Lock)',
                'is_bit': False,
                'mask': 3840,
                'name': 'FMC_QSFP1_LANE_UP',
                'nof_bits': 4,
                'reset_value': '0x0',
                'shiftr': 8},
              { 'description': 'FMC QSFP2 lane up (PCS Block Lock)',
                'is_bit': False,
                'mask': 61440,
                'name': 'FMC_QSFP2_LANE_UP',
                'nof_bits': 4,
                'reset_value': '0x0',
                'shiftr': 12},
              { 'description': 'SMB In 1',
                'is_bit': True,
                'mask': 65536,
                'name': 'SMB1_IN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 16},
              { 'description': 'SMB In 3',
                'is_bit': True,
                'mask': 131072,
                'name': 'SMB3_IN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 17},
              { 'description': 'SMB In 5',
                'is_bit': True,
                'mask': 262144,
                'name': 'SMB5_IN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 18}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_READBACK',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_READBACK` generated from `XML2VHDL` output.

=================  ======================================  ===============  ==============  ===============
**Register**
**Name:**          HEXITEC_2X6_READBACK
**Address:**       ``0x0000_0004``
**Description:**   Readback register
**Bit Fields**     **Description**                         **Mask**         **Permission**  **Reset Value**
FPGA_CLK_LOCKED    100MHz FPGA Clock locked                ``0x0000_0001``  Read/Write      ``0x0000_0000``
FMC_REFCLK_LOCKED  156.25MHz FMC Reference Clock locked    ``0x0000_0002``  Read/Write      ``0x0000_0000``
QPLL_LOCKED_B116   Bank 116 QPLL locked (FMC QSFP1)        ``0x0000_0004``  Read/Write      ``0x0000_0000``
QPLL_LOCKED_B115   Bank 115 QPLL locked (FMC QSFP2)        ``0x0000_0008``  Read/Write      ``0x0000_0000``
FMC_QSFP1_MODPRES  FMC QSFP1 module present (active-high)  ``0x0000_0010``  Read/Write      ``0x0000_0000``
FMC_QSFP2_MODPRES  FMC QSFP2 module present (active-high)  ``0x0000_0020``  Read/Write      ``0x0000_0000``
FMC_QSFP1_LANE_UP  FMC QSFP1 lane up (PCS Block Lock)      ``0x0000_0F00``  Read/Write      ``0x0000_0000``
FMC_QSFP2_LANE_UP  FMC QSFP2 lane up (PCS Block Lock)      ``0x0000_F000``  Read/Write      ``0x0000_0000``
SMB1_IN            SMB In 1                                ``0x0001_0000``  Read/Write      ``0x0000_0000``
SMB3_IN            SMB In 3                                ``0x0002_0000``  Read/Write      ``0x0000_0000``
SMB5_IN            SMB In 5                                ``0x0004_0000``  Read/Write      ``0x0000_0000``
=================  ======================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: FPGA_CLK_LOCKED [ rotate = 270 ]
      1: FMC_REFCLK_LOCKED [ rotate = 270 ]
      2: QPLL_LOCKED_B116 [ rotate = 270 ]
      3: QPLL_LOCKED_B115 [ rotate = 270 ]
      4: FMC_QSFP1_MODPRES [ rotate = 270 ]
      5: FMC_QSFP2_MODPRES [ rotate = 270 ]
      6-7:  [ rotate = 270, color = lightgrey ]
      8-11: FMC_QSFP1_LANE_UP
      12-15: FMC_QSFP2_LANE_UP
      16: SMB1_IN [ rotate = 270 ]
      17: SMB3_IN [ rotate = 270 ]
      18: SMB5_IN [ rotate = 270 ]
      19-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_CLK_CTRL = { 'addr': 8,
  'description': 'Clock control register',
  'fields': [ { 'description': 'Clock enable',
                'is_bit': True,
                'mask': 1,
                'name': 'CLK_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Main clock reset',
                'is_bit': True,
                'mask': 2,
                'name': 'CLK_RST',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_CLK_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_CLK_CTRL` generated from `XML2VHDL` output.

================  ======================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_CLK_CTRL
**Address:**      ``0x0000_0008``
**Description:**  Clock control register
**Bit Fields**    **Description**         **Mask**         **Permission**  **Reset Value**
CLK_EN            Clock enable            ``0x0000_0001``  Read/Write      ``0x0000_0000``
CLK_RST           Main clock reset        ``0x0000_0002``  Read/Write      ``0x0000_0000``
================  ======================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: CLK_EN [ rotate = 270 ]
      1: CLK_RST [ rotate = 270 ]
      2-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_UART_TX_CTRL = { 'addr': 12,
  'description': 'UART send control register',
  'fields': [ { 'description': 'Send buffer reset',
                'is_bit': True,
                'mask': 1,
                'name': 'TX_BUFF_RST',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Fill send buffer strobe',
                'is_bit': True,
                'mask': 2,
                'name': 'TX_FILL_STRB',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Send buffer strobe',
                'is_bit': True,
                'mask': 4,
                'name': 'TX_BUFF_STRB',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Data to send via UART',
                'is_bit': False,
                'mask': 65280,
                'name': 'TX_DATA',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 8}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_UART_TX_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_UART_TX_CTRL` generated from `XML2VHDL` output.

================  ==========================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_UART_TX_CTRL
**Address:**      ``0x0000_000C``
**Description:**  UART send control register
**Bit Fields**    **Description**             **Mask**         **Permission**  **Reset Value**
TX_BUFF_RST       Send buffer reset           ``0x0000_0001``  Read/Write      ``0x0000_0000``
TX_FILL_STRB      Fill send buffer strobe     ``0x0000_0002``  Read/Write      ``0x0000_0000``
TX_BUFF_STRB      Send buffer strobe          ``0x0000_0004``  Read/Write      ``0x0000_0000``
TX_DATA           Data to send via UART       ``0x0000_FF00``  Read/Write      ``0x0000_0000``
================  ==========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: TX_BUFF_RST [ rotate = 270 ]
      1: TX_FILL_STRB [ rotate = 270 ]
      2: TX_BUFF_STRB [ rotate = 270 ]
      3-7:  [ color = lightgrey ]
      8-15: TX_DATA
      16-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_UART_STATUS = { 'addr': 16,
  'description': 'UART status register',
  'fields': [ { 'description': 'Send buffer full flag',
                'is_bit': True,
                'mask': 1,
                'name': 'TX_BUFF_FULL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Send buffer empty flag',
                'is_bit': True,
                'mask': 2,
                'name': 'TX_BUFF_EMTY',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Receive buffer full flag',
                'is_bit': True,
                'mask': 4,
                'name': 'RX_BUFF_FULL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Receive buffer empty flag',
                'is_bit': True,
                'mask': 8,
                'name': 'RX_BUFF_EMTY',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'Receive packet complete flag',
                'is_bit': True,
                'mask': 16,
                'name': 'RX_PKT_DONE',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Receive buffer level',
                'is_bit': False,
                'mask': 65280,
                'name': 'RX_BUFF_LEVEL',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 8},
              { 'description': 'Received data from UART',
                'is_bit': False,
                'mask': 16711680,
                'name': 'RX_DATA',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_UART_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_UART_STATUS` generated from `XML2VHDL` output.

================  ============================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_UART_STATUS
**Address:**      ``0x0000_0010``
**Description:**  UART status register
**Bit Fields**    **Description**               **Mask**         **Permission**  **Reset Value**
TX_BUFF_FULL      Send buffer full flag         ``0x0000_0001``  Read/Write      ``0x0000_0000``
TX_BUFF_EMTY      Send buffer empty flag        ``0x0000_0002``  Read/Write      ``0x0000_0000``
RX_BUFF_FULL      Receive buffer full flag      ``0x0000_0004``  Read/Write      ``0x0000_0000``
RX_BUFF_EMTY      Receive buffer empty flag     ``0x0000_0008``  Read/Write      ``0x0000_0000``
RX_PKT_DONE       Receive packet complete flag  ``0x0000_0010``  Read/Write      ``0x0000_0000``
RX_BUFF_LEVEL     Receive buffer level          ``0x0000_FF00``  Read/Write      ``0x0000_0000``
RX_DATA           Received data from UART       ``0x00FF_0000``  Read/Write      ``0x0000_0000``
================  ============================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: TX_BUFF_FULL [ rotate = 270 ]
      1: TX_BUFF_EMTY [ rotate = 270 ]
      2: RX_BUFF_FULL [ rotate = 270 ]
      3: RX_BUFF_EMTY [ rotate = 270 ]
      4: RX_PKT_DONE [ rotate = 270 ]
      5-7:  [ rotate = 270, color = lightgrey ]
      8-15: RX_BUFF_LEVEL
      16-23: RX_DATA
      24-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_UART_RX_CTRL = { 'addr': 20,
  'description': 'UART receive control register',
  'fields': [ { 'description': 'Recieve buffer reset',
                'is_bit': True,
                'mask': 1,
                'name': 'RX_BUFF_RST',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Recieve buffer strobe',
                'is_bit': True,
                'mask': 2,
                'name': 'RX_BUFF_STRB',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_UART_RX_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_UART_RX_CTRL` generated from `XML2VHDL` output.

================  =============================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_UART_RX_CTRL
**Address:**      ``0x0000_0014``
**Description:**  UART receive control register
**Bit Fields**    **Description**                **Mask**         **Permission**  **Reset Value**
RX_BUFF_RST       Recieve buffer reset           ``0x0000_0001``  Read/Write      ``0x0000_0000``
RX_BUFF_STRB      Recieve buffer strobe          ``0x0000_0002``  Read/Write      ``0x0000_0000``
================  =============================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: RX_BUFF_RST [ rotate = 270 ]
      1: RX_BUFF_STRB [ rotate = 270 ]
      2-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_VSR_CTRL = { 'addr': 24,
  'description': 'VSR control register',
  'fields': [ { 'description': 'VSR enable',
                'is_bit': False,
                'mask': 63,
                'name': 'VSR_EN',
                'nof_bits': 6,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'High Voltage enable',
                'is_bit': False,
                'mask': 16128,
                'name': 'HV_EN',
                'nof_bits': 6,
                'reset_value': '0x0',
                'shiftr': 8}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR_CTRL` generated from `XML2VHDL` output.

================  ====================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR_CTRL
**Address:**      ``0x0000_0018``
**Description:**  VSR control register
**Bit Fields**    **Description**       **Mask**         **Permission**  **Reset Value**
VSR_EN            VSR enable            ``0x0000_003F``  Read/Write      ``0x0000_0000``
HV_EN             High Voltage enable   ``0x0000_3F00``  Read/Write      ``0x0000_0000``
================  ====================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: VSR_EN
      6-7:  [ rotate = 270, color = lightgrey ]
      8-13: HV_EN
      14-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_VSR_MODE_CTRL = { 'addr': 28,
  'description': 'VSR mode control register',
  'fields': [ { 'description': 'SM enable',
                'is_bit': True,
                'mask': 1,
                'name': 'SM_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Syncmode enable',
                'is_bit': True,
                'mask': 2,
                'name': 'SYNCMODE_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Training pattern select',
                'is_bit': True,
                'mask': 4096,
                'name': 'TRAINING_SEL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 12}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR_MODE_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR_MODE_CTRL` generated from `XML2VHDL` output.

================  =========================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR_MODE_CTRL
**Address:**      ``0x0000_001C``
**Description:**  VSR mode control register
**Bit Fields**    **Description**            **Mask**         **Permission**  **Reset Value**
SM_EN             SM enable                  ``0x0000_0001``  Read/Write      ``0x0000_0000``
SYNCMODE_EN       Syncmode enable            ``0x0000_0002``  Read/Write      ``0x0000_0000``
TRAINING_SEL      Training pattern select    ``0x0000_1000``  Read/Write      ``0x0000_0000``
================  =========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: SM_EN [ rotate = 270 ]
      1: SYNCMODE_EN [ rotate = 270 ]
      2-11:  [ color = lightgrey ]
      12: TRAINING_SEL [ rotate = 270 ]
      13-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_VSR_DATA_CTRL = { 'addr': 32,
  'description': 'VSR data control register',
  'fields': [ { 'description': 'Data enable',
                'is_bit': True,
                'mask': 1,
                'name': 'DATA_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Training enable',
                'is_bit': True,
                'mask': 16,
                'name': 'TRAINING_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Synth data enable',
                'is_bit': True,
                'mask': 256,
                'name': 'SYNTH_DATA_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 8},
              { 'description': 'Training pattern',
                'is_bit': False,
                'mask': 4294901760,
                'name': 'TRAINING_PATTERN',
                'nof_bits': 16,
                'reset_value': '0x0',
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR_DATA_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR_DATA_CTRL` generated from `XML2VHDL` output.

================  =========================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR_DATA_CTRL
**Address:**      ``0x0000_0020``
**Description:**  VSR data control register
**Bit Fields**    **Description**            **Mask**         **Permission**  **Reset Value**
DATA_EN           Data enable                ``0x0000_0001``  Read/Write      ``0x0000_0000``
TRAINING_EN       Training enable            ``0x0000_0010``  Read/Write      ``0x0000_0000``
SYNTH_DATA_EN     Synth data enable          ``0x0000_0100``  Read/Write      ``0x0000_0000``
TRAINING_PATTERN  Training pattern           ``0xFFFF_0000``  Read/Write      ``0x0000_0000``
================  =========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: DATA_EN [ rotate = 270 ]
      1-3:  [ rotate = 270, color = lightgrey ]
      4: TRAINING_EN [ rotate = 270 ]
      5-7:  [ rotate = 270, color = lightgrey ]
      8: SYNTH_DATA_EN [ rotate = 270 ]
      9-15:  [ color = lightgrey ]
      16-31: TRAINING_PATTERN
   }

"""

HEXITEC_2X6_SMB_CFG = { 'addr': 36,
  'description': 'SMB configuration register',
  'fields': [],
  'mask': 7,
  'name': 'HEXITEC_2X6_SMB_CFG',
  'nof_bits': 3,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_SMB_CFG` generated from `XML2VHDL` output.

================  ==========================
**Register**
**Name:**         HEXITEC_2X6_SMB_CFG
**Address:**      ``0x0000_0024``
**Description:**  SMB configuration register
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ==========================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-2: SMB_CFG [ rotate = 270 ]
      3-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_TIG_CTRL = { 'addr': 40,
  'description': 'Test Image Generator control register',
  'fields': [ { 'description': 'Test Image Generator reset',
                'is_bit': True,
                'mask': 1,
                'name': 'TIG_RST',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Test Image Generator enable',
                'is_bit': True,
                'mask': 2,
                'name': 'TIG_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Test Image Generator mode',
                'is_bit': False,
                'mask': 1792,
                'name': 'TIG_MODE',
                'nof_bits': 3,
                'reset_value': '0x0',
                'shiftr': 8}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_TIG_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_TIG_CTRL` generated from `XML2VHDL` output.

================  =====================================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_TIG_CTRL
**Address:**      ``0x0000_0028``
**Description:**  Test Image Generator control register
**Bit Fields**    **Description**                        **Mask**         **Permission**  **Reset Value**
TIG_RST           Test Image Generator reset             ``0x0000_0001``  Read/Write      ``0x0000_0000``
TIG_EN            Test Image Generator enable            ``0x0000_0002``  Read/Write      ``0x0000_0000``
TIG_MODE          Test Image Generator mode              ``0x0000_0700``  Read/Write      ``0x0000_0000``
================  =====================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: TIG_RST [ rotate = 270 ]
      1: TIG_EN [ rotate = 270 ]
      2-7:  [ color = lightgrey ]
      8-10: TIG_MODE [ rotate = 270 ]
      11-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_TIG_ROWS = { 'addr': 44,
  'description': 'Test Image Generator rows register',
  'fields': [],
  'mask': 16777215,
  'name': 'HEXITEC_2X6_TIG_ROWS',
  'nof_bits': 24,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_TIG_ROWS` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         HEXITEC_2X6_TIG_ROWS
**Address:**      ``0x0000_002C``
**Description:**  Test Image Generator rows register
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-23: TIG_ROWS
      24-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_TIG_COLS = { 'addr': 48,
  'description': 'Test Image Generator columns register',
  'fields': [],
  'mask': 16777215,
  'name': 'HEXITEC_2X6_TIG_COLS',
  'nof_bits': 24,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_TIG_COLS` generated from `XML2VHDL` output.

================  =====================================
**Register**
**Name:**         HEXITEC_2X6_TIG_COLS
**Address:**      ``0x0000_0030``
**Description:**  Test Image Generator columns register
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =====================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-23: TIG_COLS
      24-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_TIG_LBCLKS = { 'addr': 52,
  'description': 'Test Image Generator lbclks register',
  'fields': [],
  'mask': 16777215,
  'name': 'HEXITEC_2X6_TIG_LBCLKS',
  'nof_bits': 24,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_TIG_LBCLKS` generated from `XML2VHDL` output.

================  ====================================
**Register**
**Name:**         HEXITEC_2X6_TIG_LBCLKS
**Address:**      ``0x0000_0034``
**Description:**  Test Image Generator lbclks register
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ====================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-23: TIG_LBCLKS
      24-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_TIG_FBCLKS = { 'addr': 56,
  'description': 'Test Image Generator fbclks register',
  'fields': [],
  'mask': 16777215,
  'name': 'HEXITEC_2X6_TIG_FBCLKS',
  'nof_bits': 24,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_TIG_FBCLKS` generated from `XML2VHDL` output.

================  ====================================
**Register**
**Name:**         HEXITEC_2X6_TIG_FBCLKS
**Address:**      ``0x0000_0038``
**Description:**  Test Image Generator fbclks register
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ====================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-23: TIG_FBCLKS
      24-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_UDP_CORE_CTRL = { 'addr': 64,
  'description': 'UDP Core control register',
  'fields': [ { 'description': 'Use fixed external addresses',
                'is_bit': False,
                'mask': 255,
                'name': 'USE_EXT_ADDRS',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_UDP_CORE_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_UDP_CORE_CTRL` generated from `XML2VHDL` output.

================  ============================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_UDP_CORE_CTRL
**Address:**      ``0x0000_0040``
**Description:**  UDP Core control register
**Bit Fields**    **Description**               **Mask**         **Permission**  **Reset Value**
USE_EXT_ADDRS     Use fixed external addresses  ``0x0000_00FF``  Read/Write      ``0x0000_0000``
================  ============================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: USE_EXT_ADDRS
      8-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_TEST_CTRL = { 'addr': 68,
  'description': 'Board test control register',
  'fields': [ { 'description': 'UART loopback enable',
                'is_bit': True,
                'mask': 1,
                'name': 'UART_LOOPBACK_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_TEST_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_TEST_CTRL` generated from `XML2VHDL` output.

================  ===========================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_TEST_CTRL
**Address:**      ``0x0000_0044``
**Description:**  Board test control register
**Bit Fields**    **Description**              **Mask**         **Permission**  **Reset Value**
UART_LOOPBACK_EN  UART loopback enable         ``0x0000_0001``  Read/Write      ``0x0000_0000``
================  ===========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: UART_LOOPBACK_EN [ rotate = 270 ]
      1-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_HEADER_CTRL = { 'addr': 256,
  'description': 'Hexitc header control register',
  'fields': [ { 'description': 'Load preload frame number into frame counter',
                'is_bit': True,
                'mask': 1,
                'name': 'FRAME_COUNTER_LOAD',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Load preload packet number into packet counter',
                'is_bit': True,
                'mask': 2,
                'name': 'PACKET_COUNTER_LOAD',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Reset frame number counter',
                'is_bit': True,
                'mask': 4,
                'name': 'FRAME_COUNTER_RST',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Reset packet number counter',
                'is_bit': True,
                'mask': 8,
                'name': 'PACKET_COUNTER_RST',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'Restart the frame generator',
                'is_bit': True,
                'mask': 1073741824,
                'name': 'RUN_GENERATOR',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 30},
              { 'description': 'Readout enable',
                'is_bit': True,
                'mask': 2147483648,
                'name': 'READOUT_ENABLE',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 31}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_HEADER_CTRL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_HEADER_CTRL` generated from `XML2VHDL` output.

===================  ==============================================  ===============  ==============  ===============
**Register**
**Name:**            HEXITEC_2X6_HEADER_CTRL
**Address:**         ``0x0000_0100``
**Description:**     Hexitc header control register
**Bit Fields**       **Description**                                 **Mask**         **Permission**  **Reset Value**
FRAME_COUNTER_LOAD   Load preload frame number into frame counter    ``0x0000_0001``  Read/Write      ``0x0000_0000``
PACKET_COUNTER_LOAD  Load preload packet number into packet counter  ``0x0000_0002``  Read/Write      ``0x0000_0000``
FRAME_COUNTER_RST    Reset frame number counter                      ``0x0000_0004``  Read/Write      ``0x0000_0000``
PACKET_COUNTER_RST   Reset packet number counter                     ``0x0000_0008``  Read/Write      ``0x0000_0000``
RUN_GENERATOR        Restart the frame generator                     ``0x4000_0000``  Read/Write      ``0x0000_0000``
READOUT_ENABLE       Readout enable                                  ``0x8000_0000``  Read/Write      ``0x0000_0000``
===================  ==============================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: FRAME_COUNTER_LOAD [ rotate = 270 ]
      1: PACKET_COUNTER_LOAD [ rotate = 270 ]
      2: FRAME_COUNTER_RST [ rotate = 270 ]
      3: PACKET_COUNTER_RST [ rotate = 270 ]
      4-29:  [ color = lightgrey ]
      30: RUN_GENERATOR [ rotate = 270 ]
      31: READOUT_ENABLE [ rotate = 270 ]
   }

"""

HEXITEC_2X6_HEADER_STATUS = { 'addr': 260,
  'description': 'Hexitec header status register',
  'fields': [ { 'description': 'Current readout lane',
                'is_bit': False,
                'mask': 3,
                'name': 'READOUT_LANE',
                'nof_bits': 2,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_HEADER_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_HEADER_STATUS` generated from `XML2VHDL` output.

================  ==============================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_HEADER_STATUS
**Address:**      ``0x0000_0104``
**Description:**  Hexitec header status register
**Bit Fields**    **Description**                 **Mask**         **Permission**  **Reset Value**
READOUT_LANE      Current readout lane            ``0x0000_0003``  Read/Write      ``0x0000_0000``
================  ==============================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-1: READOUT_LANE [ rotate = 270 ]
      2-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_FRAME_PRELOAD_LOWER = { 'addr': 272,
  'description': 'Frame number preload value [31:0]',
  'fields': [],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_FRAME_PRELOAD_LOWER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_FRAME_PRELOAD_LOWER` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         HEXITEC_2X6_FRAME_PRELOAD_LOWER
**Address:**      ``0x0000_0110``
**Description:**  Frame number preload value [31:0]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: FRAME_PRELOAD_LOWER
   }

"""

HEXITEC_2X6_FRAME_PRELOAD_UPPER = { 'addr': 276,
  'description': 'Frame number preload value [63:32]',
  'fields': [],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_FRAME_PRELOAD_UPPER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_FRAME_PRELOAD_UPPER` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         HEXITEC_2X6_FRAME_PRELOAD_UPPER
**Address:**      ``0x0000_0114``
**Description:**  Frame number preload value [63:32]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: FRAME_PRELOAD_UPPER
   }

"""

HEXITEC_2X6_PACKET_PRELOAD_LOWER = { 'addr': 280,
  'description': 'Packet number preload value [31:0]]',
  'fields': [],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_PACKET_PRELOAD_LOWER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_PACKET_PRELOAD_LOWER` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         HEXITEC_2X6_PACKET_PRELOAD_LOWER
**Address:**      ``0x0000_0118``
**Description:**  Packet number preload value [31:0]]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: PACKET_PRELOAD_LOWER
   }

"""

HEXITEC_2X6_PACKET_PRELOAD_UPPER = { 'addr': 284,
  'description': 'Packet number preload value [63:32]',
  'fields': [],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_PACKET_PRELOAD_UPPER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_PACKET_PRELOAD_UPPER` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         HEXITEC_2X6_PACKET_PRELOAD_UPPER
**Address:**      ``0x0000_011C``
**Description:**  Packet number preload value [63:32]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: PACKET_PRELOAD_UPPER
   }

"""

HEXITEC_2X6_FRAME_NUMBER_LOWER = { 'addr': 288,
  'description': 'frame number counter [31:0]',
  'fields': [],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_FRAME_NUMBER_LOWER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_FRAME_NUMBER_LOWER` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         HEXITEC_2X6_FRAME_NUMBER_LOWER
**Address:**      ``0x0000_0120``
**Description:**  frame number counter [31:0]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: FRAME_NUMBER_LOWER
   }

"""

HEXITEC_2X6_FRAME_NUMBER_UPPER = { 'addr': 292,
  'description': 'frame number counter [63:32]',
  'fields': [],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_FRAME_NUMBER_UPPER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_FRAME_NUMBER_UPPER` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         HEXITEC_2X6_FRAME_NUMBER_UPPER
**Address:**      ``0x0000_0124``
**Description:**  frame number counter [63:32]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: FRAME_NUMBER_UPPER
   }

"""

HEXITEC_2X6_PACKET_NUMBER_LOWER = { 'addr': 296,
  'description': 'packet number counter [31:0]',
  'fields': [],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_PACKET_NUMBER_LOWER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_PACKET_NUMBER_LOWER` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         HEXITEC_2X6_PACKET_NUMBER_LOWER
**Address:**      ``0x0000_0128``
**Description:**  packet number counter [31:0]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: PACKET_NUMBER_LOWER
   }

"""

HEXITEC_2X6_PACKET_NUMBER_UPPER = { 'addr': 300,
  'description': 'packet number counter [63:32]',
  'fields': [],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_PACKET_NUMBER_UPPER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_PACKET_NUMBER_UPPER` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         HEXITEC_2X6_PACKET_NUMBER_UPPER
**Address:**      ``0x0000_012C``
**Description:**  packet number counter [63:32]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: PACKET_NUMBER_UPPER
   }

"""

HEXITEC_2X6_VSR0_STATUS = { 'addr': 1000,
  'description': 'VSR 0 status register',
  'fields': [ { 'description': 'locked',
                'is_bit': False,
                'mask': 255,
                'name': 'LOCKED',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR0_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR0_STATUS` generated from `XML2VHDL` output.

================  =======================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR0_STATUS
**Address:**      ``0x0000_03E8``
**Description:**  VSR 0 status register
**Bit Fields**    **Description**          **Mask**         **Permission**  **Reset Value**
LOCKED            locked                   ``0x0000_00FF``  Read/Write      ``0x0000_0000``
================  =======================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_VSR1_STATUS = { 'addr': 1004,
  'description': 'VSR 1 status register',
  'fields': [ { 'description': 'locked',
                'is_bit': False,
                'mask': 255,
                'name': 'LOCKED',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR1_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR1_STATUS` generated from `XML2VHDL` output.

================  =======================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR1_STATUS
**Address:**      ``0x0000_03EC``
**Description:**  VSR 1 status register
**Bit Fields**    **Description**          **Mask**         **Permission**  **Reset Value**
LOCKED            locked                   ``0x0000_00FF``  Read/Write      ``0x0000_0000``
================  =======================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_VSR2_STATUS = { 'addr': 1008,
  'description': 'VSR 2 status register',
  'fields': [ { 'description': 'locked',
                'is_bit': False,
                'mask': 255,
                'name': 'LOCKED',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR2_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR2_STATUS` generated from `XML2VHDL` output.

================  =======================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR2_STATUS
**Address:**      ``0x0000_03F0``
**Description:**  VSR 2 status register
**Bit Fields**    **Description**          **Mask**         **Permission**  **Reset Value**
LOCKED            locked                   ``0x0000_00FF``  Read/Write      ``0x0000_0000``
================  =======================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_VSR3_STATUS = { 'addr': 1012,
  'description': 'VSR 3 status register',
  'fields': [ { 'description': 'locked',
                'is_bit': False,
                'mask': 255,
                'name': 'LOCKED',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR3_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR3_STATUS` generated from `XML2VHDL` output.

================  =======================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR3_STATUS
**Address:**      ``0x0000_03F4``
**Description:**  VSR 3 status register
**Bit Fields**    **Description**          **Mask**         **Permission**  **Reset Value**
LOCKED            locked                   ``0x0000_00FF``  Read/Write      ``0x0000_0000``
================  =======================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_VSR4_STATUS = { 'addr': 1016,
  'description': 'VSR 4 status register',
  'fields': [ { 'description': 'locked',
                'is_bit': False,
                'mask': 255,
                'name': 'LOCKED',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR4_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR4_STATUS` generated from `XML2VHDL` output.

================  =======================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR4_STATUS
**Address:**      ``0x0000_03F8``
**Description:**  VSR 4 status register
**Bit Fields**    **Description**          **Mask**         **Permission**  **Reset Value**
LOCKED            locked                   ``0x0000_00FF``  Read/Write      ``0x0000_0000``
================  =======================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31:  [ color = lightgrey ]
   }

"""

HEXITEC_2X6_VSR5_STATUS = { 'addr': 1020,
  'description': 'VSR 5 status register',
  'fields': [ { 'description': 'locked',
                'is_bit': False,
                'mask': 255,
                'name': 'LOCKED',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_VSR5_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_VSR5_STATUS` generated from `XML2VHDL` output.

================  =======================  ===============  ==============  ===============
**Register**
**Name:**         HEXITEC_2X6_VSR5_STATUS
**Address:**      ``0x0000_03FC``
**Description:**  VSR 5 status register
**Bit Fields**    **Description**          **Mask**         **Permission**  **Reset Value**
LOCKED            locked                   ``0x0000_00FF``  Read/Write      ``0x0000_0000``
================  =======================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31:  [ color = lightgrey ]
   }

"""

BOARD_BUILD_INFO_SRC_VERSION = { 'addr': 32768,
  'description': 'Source code version in hex readable form '
                 '[major].[minor].[micro]',
  'fields': [ { 'description': '3 digit hex readable micro',
                'is_bit': False,
                'mask': 4095,
                'name': 'MICRO',
                'nof_bits': 12,
                'reset_value': None,
                'shiftr': 0},
              { 'description': '3 digit hex readable minor',
                'is_bit': False,
                'mask': 16773120,
                'name': 'MINOR',
                'nof_bits': 12,
                'reset_value': None,
                'shiftr': 12},
              { 'description': '2 digit hex readable major',
                'is_bit': False,
                'mask': 4278190080,
                'name': 'MAJOR',
                'nof_bits': 8,
                'reset_value': None,
                'shiftr': 24}],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_SRC_VERSION',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_SRC_VERSION` generated from `XML2VHDL` output.

================  ================================================================  ===============  ==============  ===============
**Register**
**Name:**         BOARD_BUILD_INFO_SRC_VERSION
**Address:**      ``0x0000_8000``
**Description:**  Source code version in hex readable form [major].[minor].[micro]
**Bit Fields**    **Description**                                                   **Mask**         **Permission**  **Reset Value**
MICRO             3 digit hex readable micro                                        ``0x0000_0FFF``  Read-Only       \-\-\-
MINOR             3 digit hex readable minor                                        ``0x00FF_F000``  Read-Only       \-\-\-
MAJOR             2 digit hex readable major                                        ``0xFF00_0000``  Read-Only       \-\-\-
================  ================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-11: MICRO
      12-23: MINOR
      24-31: MAJOR
   }

"""

BOARD_BUILD_INFO_GIT_HASH = { 'addr': 32772,
  'description': 'Abbreviated Git hash for commit where bit-stream was '
                 'compiled (padded to 32bit)',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_GIT_HASH',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_GIT_HASH` generated from `XML2VHDL` output.

================  ===============================================================================
**Register**
**Name:**         BOARD_BUILD_INFO_GIT_HASH
**Address:**      ``0x0000_8004``
**Description:**  Abbreviated Git hash for commit where bit-stream was compiled (padded to 32bit)
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ===============================================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: GIT_HASH
   }

"""

BOARD_BUILD_INFO_BUILD_DATE = { 'addr': 32776,
  'description': 'Build date in hex readable form [year]-[month]-[day]',
  'fields': [ { 'description': '2 digit hex readable day',
                'is_bit': False,
                'mask': 255,
                'name': 'DAY',
                'nof_bits': 8,
                'reset_value': None,
                'shiftr': 0},
              { 'description': '2 digit hex readable month',
                'is_bit': False,
                'mask': 65280,
                'name': 'MONTH',
                'nof_bits': 8,
                'reset_value': None,
                'shiftr': 8},
              { 'description': '4 digit hex readable year',
                'is_bit': False,
                'mask': 4294901760,
                'name': 'YEAR',
                'nof_bits': 16,
                'reset_value': None,
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_BUILD_DATE',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_BUILD_DATE` generated from `XML2VHDL` output.

================  ====================================================  ===============  ==============  ===============
**Register**
**Name:**         BOARD_BUILD_INFO_BUILD_DATE
**Address:**      ``0x0000_8008``
**Description:**  Build date in hex readable form [year]-[month]-[day]
**Bit Fields**    **Description**                                       **Mask**         **Permission**  **Reset Value**
DAY               2 digit hex readable day                              ``0x0000_00FF``  Read-Only       \-\-\-
MONTH             2 digit hex readable month                            ``0x0000_FF00``  Read-Only       \-\-\-
YEAR              4 digit hex readable year                             ``0xFFFF_0000``  Read-Only       \-\-\-
================  ====================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: DAY
      8-15: MONTH
      16-31: YEAR
   }

"""

BOARD_BUILD_INFO_BUILD_TIME = { 'addr': 32780,
  'description': 'Build time in hex readable form [hour]:[minute]:[seconds]',
  'fields': [ { 'description': '2 digit hex readable seconds',
                'is_bit': False,
                'mask': 255,
                'name': 'SECONDS',
                'nof_bits': 8,
                'reset_value': None,
                'shiftr': 0},
              { 'description': '2 digit hex readable minute',
                'is_bit': False,
                'mask': 65280,
                'name': 'MINUTE',
                'nof_bits': 8,
                'reset_value': None,
                'shiftr': 8},
              { 'description': '2 digit hex readable hour',
                'is_bit': False,
                'mask': 16711680,
                'name': 'HOUR',
                'nof_bits': 8,
                'reset_value': None,
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_BUILD_TIME',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_BUILD_TIME` generated from `XML2VHDL` output.

================  =========================================================  ===============  ==============  ===============
**Register**
**Name:**         BOARD_BUILD_INFO_BUILD_TIME
**Address:**      ``0x0000_800C``
**Description:**  Build time in hex readable form [hour]:[minute]:[seconds]
**Bit Fields**    **Description**                                            **Mask**         **Permission**  **Reset Value**
SECONDS           2 digit hex readable seconds                               ``0x0000_00FF``  Read-Only       \-\-\-
MINUTE            2 digit hex readable minute                                ``0x0000_FF00``  Read-Only       \-\-\-
HOUR              2 digit hex readable hour                                  ``0x00FF_0000``  Read-Only       \-\-\-
================  =========================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: SECONDS
      8-15: MINUTE
      16-23: HOUR
      24-31:  [ color = lightgrey ]
   }

"""

BOARD_BUILD_INFO_DNA_0 = { 'addr': 32784,
  'description': 'Unique FPGA device DNA ID [31..0]',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_DNA_0',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_DNA_0` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         BOARD_BUILD_INFO_DNA_0
**Address:**      ``0x0000_8010``
**Description:**  Unique FPGA device DNA ID [31..0]
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DNA_0
   }

"""

BOARD_BUILD_INFO_DNA_1 = { 'addr': 32788,
  'description': 'Unique FPGA device DNA ID [63..32]',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_DNA_1',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_DNA_1` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         BOARD_BUILD_INFO_DNA_1
**Address:**      ``0x0000_8014``
**Description:**  Unique FPGA device DNA ID [63..32]
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DNA_1
   }

"""

BOARD_BUILD_INFO_DNA_2 = { 'addr': 32792,
  'description': 'Unique FPGA device DNA ID [95..64]',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_DNA_2',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_DNA_2` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         BOARD_BUILD_INFO_DNA_2
**Address:**      ``0x0000_8018``
**Description:**  Unique FPGA device DNA ID [95..64]
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DNA_2
   }

"""

BOARD_BUILD_INFO_RSV_DNA_3 = { 'addr': 32796,
  'description': 'Unique FPGA device DNA ID Reserved for future expansion '
                 '[127..96]',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_RSV_DNA_3',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_RSV_DNA_3` generated from `XML2VHDL` output.

================  =================================================================
**Register**
**Name:**         BOARD_BUILD_INFO_RSV_DNA_3
**Address:**      ``0x0000_801C``
**Description:**  Unique FPGA device DNA ID Reserved for future expansion [127..96]
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =================================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: RSV_DNA_3 [ color = lightgrey ]
   }

"""

BOARD_BUILD_INFO_DNA_STATUS = { 'addr': 32800,
  'description': 'DNA status register',
  'fields': [ { 'description': 'FPGA DNA valid',
                'is_bit': True,
                'mask': 1,
                'name': 'VALID',
                'nof_bits': 1,
                'reset_value': None,
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_DNA_STATUS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_DNA_STATUS` generated from `XML2VHDL` output.

================  ===========================  ===============  ==============  ===============
**Register**
**Name:**         BOARD_BUILD_INFO_DNA_STATUS
**Address:**      ``0x0000_8020``
**Description:**  DNA status register
**Bit Fields**    **Description**              **Mask**         **Permission**  **Reset Value**
VALID             FPGA DNA valid               ``0x0000_0001``  Read-Only       \-\-\-
================  ===========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: VALID [ rotate = 270 ]
      1-31:  [ color = lightgrey ]
   }

"""

BOARD_BUILD_INFO_SCRATCH_1 = { 'addr': 32816,
  'description': 'Scratch register 1 to test register read writes with no '
                 'impact to design functionality',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_SCRATCH_1',
  'nof_bits': 32,
  'reset_value': '0x11111111',
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_SCRATCH_1` generated from `XML2VHDL` output.

================  ======================================================================================
**Register**
**Name:**         BOARD_BUILD_INFO_SCRATCH_1
**Address:**      ``0x0000_8030``
**Description:**  Scratch register 1 to test register read writes with no impact to design functionality
**Permission:**   Read/Write
**Reset Value:**  ``0x1111_1111``
================  ======================================================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SCRATCH_1
   }

"""

BOARD_BUILD_INFO_SCRATCH_2 = { 'addr': 32820,
  'description': 'Scratch register 2 to test register read writes with no '
                 'impact to design functionality',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_SCRATCH_2',
  'nof_bits': 32,
  'reset_value': '0x22222222',
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_SCRATCH_2` generated from `XML2VHDL` output.

================  ======================================================================================
**Register**
**Name:**         BOARD_BUILD_INFO_SCRATCH_2
**Address:**      ``0x0000_8034``
**Description:**  Scratch register 2 to test register read writes with no impact to design functionality
**Permission:**   Read/Write
**Reset Value:**  ``0x2222_2222``
================  ======================================================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SCRATCH_2
   }

"""

BOARD_BUILD_INFO_SCRATCH_3 = { 'addr': 32824,
  'description': 'Scratch register 3 to test register read writes with no '
                 'impact to design functionality',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_SCRATCH_3',
  'nof_bits': 32,
  'reset_value': '0x33333333',
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_SCRATCH_3` generated from `XML2VHDL` output.

================  ======================================================================================
**Register**
**Name:**         BOARD_BUILD_INFO_SCRATCH_3
**Address:**      ``0x0000_8038``
**Description:**  Scratch register 3 to test register read writes with no impact to design functionality
**Permission:**   Read/Write
**Reset Value:**  ``0x3333_3333``
================  ======================================================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SCRATCH_3
   }

"""

BOARD_BUILD_INFO_SCRATCH_4 = { 'addr': 32828,
  'description': 'Scratch register 4 to test register read writes with no '
                 'impact to design functionality',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_SCRATCH_4',
  'nof_bits': 32,
  'reset_value': '0x44444444',
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_SCRATCH_4` generated from `XML2VHDL` output.

================  ======================================================================================
**Register**
**Name:**         BOARD_BUILD_INFO_SCRATCH_4
**Address:**      ``0x0000_803C``
**Description:**  Scratch register 4 to test register read writes with no impact to design functionality
**Permission:**   Read/Write
**Reset Value:**  ``0x4444_4444``
================  ======================================================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SCRATCH_4
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER = { 'addr': 131072,
  'description': 'Source MAC Address Lower',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER',
  'nof_bits': 32,
  'reset_value': '0x00000201',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER
**Address:**      ``0x0002_0000``
**Description:**  Source MAC Address Lower
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0201``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SRC_MAC_ADDR_LOWER
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER = { 'addr': 131076,
  'description': 'Source MAC Address Upper',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER',
  'nof_bits': 16,
  'reset_value': '0x6200',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER
**Address:**      ``0x0002_0004``
**Description:**  Source MAC Address Upper
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_6200``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: SRC_MAC_ADDR_UPPER
      16-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER = { 'addr': 131084,
  'description': 'Destination MAC Address Lower',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER',
  'nof_bits': 32,
  'reset_value': '0x00000FF00',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER
**Address:**      ``0x0002_000C``
**Description:**  Destination MAC Address Lower
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_FF00``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DST_MAC_ADDR_LOWER
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER = { 'addr': 131088,
  'description': 'Destination MAC Address Upper',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER',
  'nof_bits': 16,
  'reset_value': '0x6200',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER
**Address:**      ``0x0002_0010``
**Description:**  Destination MAC Address Upper
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_6200``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: DST_MAC_ADDR_UPPER
      16-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_DST_IP_ADDR = { 'addr': 131108,
  'description': 'UDP Destination IP Address',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_DST_IP_ADDR',
  'nof_bits': 32,
  'reset_value': '0xC0A80201',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_DST_IP_ADDR` generated from `XML2VHDL` output.

================  =========================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_DST_IP_ADDR
**Address:**      ``0x0002_0024``
**Description:**  UDP Destination IP Address
**Permission:**   Read/Write
**Reset Value:**  ``0xC0A8_0201``
================  =========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DST_IP_ADDR
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_IP_ADDR = { 'addr': 131112,
  'description': 'UDP Source IP Address',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_IP_ADDR',
  'nof_bits': 32,
  'reset_value': '0xC0A8020B',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_IP_ADDR` generated from `XML2VHDL` output.

================  =========================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_SRC_IP_ADDR
**Address:**      ``0x0002_0028``
**Description:**  UDP Source IP Address
**Permission:**   Read/Write
**Reset Value:**  ``0xC0A8_020B``
================  =========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SRC_IP_ADDR
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_UDP_PORTS = { 'addr': 131116,
  'description': 'UDP Ports',
  'fields': [ { 'description': 'UDP Source Port',
                'is_bit': False,
                'mask': 65535,
                'name': 'SRC_PORT',
                'nof_bits': 16,
                'reset_value': '0xf0d0',
                'shiftr': 0},
              { 'description': 'UDP Destination Port',
                'is_bit': False,
                'mask': 4294901760,
                'name': 'DST_PORT',
                'nof_bits': 16,
                'reset_value': '0xf0d1',
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_UDP_PORTS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_UDP_PORTS` generated from `XML2VHDL` output.

================  =======================================  ===============  ==============  ===============
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_UDP_PORTS
**Address:**      ``0x0002_002C``
**Description:**  UDP Ports
**Bit Fields**    **Description**                          **Mask**         **Permission**  **Reset Value**
SRC_PORT          UDP Source Port                          ``0x0000_FFFF``  Read/Write      ``0x0000_F0D0``
DST_PORT          UDP Destination Port                     ``0xFFFF_0000``  Read/Write      ``0x0000_F0D1``
================  =======================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: SRC_PORT
      16-31: DST_PORT
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_FILTER_CONTROL = { 'addr': 131128,
  'description': 'Controls the level of filtering in the UDP core Rx',
  'fields': [ { 'description': 'Enables Broadcast Recieving',
                'is_bit': True,
                'mask': 1,
                'name': 'BROADCAST_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 0},
              { 'description': 'Enables ARPs',
                'is_bit': True,
                'mask': 2,
                'name': 'ARP_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 1},
              { 'description': 'Enables Pings',
                'is_bit': True,
                'mask': 4,
                'name': 'PING_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 2},
              { 'description': 'Enable Passing of Unsupported Ethernet Packets',
                'is_bit': True,
                'mask': 256,
                'name': 'PASS_UNS_ETHTYPE',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 8},
              { 'description': 'Enable Passing of Unsupported IPv4 Packets',
                'is_bit': True,
                'mask': 512,
                'name': 'PASS_UNS_IPV4',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 9},
              { 'description': 'Check Dest MAC address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 65536,
                'name': 'DST_MAC_CHK_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 16},
              { 'description': 'Check Source MAC address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 131072,
                'name': 'SRC_MAC_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 17},
              { 'description': 'Check Dest IP address Field Of Incoming Packet',
                'is_bit': True,
                'mask': 262144,
                'name': 'DST_IP_CHK_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 18},
              { 'description': 'Check Source IP address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 524288,
                'name': 'SRC_IP_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 19},
              { 'description': 'Check Dest UDP Port Field Of Incoming Packet',
                'is_bit': True,
                'mask': 1048576,
                'name': 'DST_PORT_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 20},
              { 'description': 'Check Source UDP Port Field Of Incoming Packet',
                'is_bit': True,
                'mask': 2097152,
                'name': 'SRC_PORT_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 21},
              { 'description': 'Reset Packet Counts',
                'is_bit': True,
                'mask': 4194304,
                'name': 'PACKET_COUNT_RST_N',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 22},
              { 'description': 'Remove The Header From Incoming Unsupported '
                               'IPv4 Data',
                'is_bit': True,
                'mask': 16777216,
                'name': 'STRIP_UNS_PRO',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 24},
              { 'description': 'Remove The Header From Incoming Unsupported '
                               'Ethernet Data',
                'is_bit': True,
                'mask': 33554432,
                'name': 'STRIP_UNS_ETH',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 25},
              { 'description': 'Check Received Packets Total IP Length and Cut '
                               'off Extra Padding',
                'is_bit': True,
                'mask': 67108864,
                'name': 'CHK_IP_LENGTH',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 26}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_FILTER_CONTROL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_FILTER_CONTROL` generated from `XML2VHDL` output.

==================  ================================================================  ===============  ==============  ===============
**Register**
**Name:**           UDP_CORE_0_0_UDP_CORE_CONTROL_FILTER_CONTROL
**Address:**        ``0x0002_0038``
**Description:**    Controls the level of filtering in the UDP core Rx
**Bit Fields**      **Description**                                                   **Mask**         **Permission**  **Reset Value**
BROADCAST_EN        Enables Broadcast Recieving                                       ``0x0000_0001``  Read/Write      ``0x0000_0001``
ARP_EN              Enables ARPs                                                      ``0x0000_0002``  Read/Write      ``0x0000_0001``
PING_EN             Enables Pings                                                     ``0x0000_0004``  Read/Write      ``0x0000_0001``
PASS_UNS_ETHTYPE    Enable Passing of Unsupported Ethernet Packets                    ``0x0000_0100``  Read/Write      ``0x0000_0001``
PASS_UNS_IPV4       Enable Passing of Unsupported IPv4 Packets                        ``0x0000_0200``  Read/Write      ``0x0000_0001``
DST_MAC_CHK_EN      Check Dest MAC address Field Of Incoming Packet                   ``0x0001_0000``  Read/Write      ``0x0000_0001``
SRC_MAC_CHK_EN      Check Source MAC address Field Of Incoming Packet                 ``0x0002_0000``  Read/Write      ``0x0000_0000``
DST_IP_CHK_EN       Check Dest IP address Field Of Incoming Packet                    ``0x0004_0000``  Read/Write      ``0x0000_0001``
SRC_IP_CHK_EN       Check Source IP address Field Of Incoming Packet                  ``0x0008_0000``  Read/Write      ``0x0000_0000``
DST_PORT_CHK_EN     Check Dest UDP Port Field Of Incoming Packet                      ``0x0010_0000``  Read/Write      ``0x0000_0000``
SRC_PORT_CHK_EN     Check Source UDP Port Field Of Incoming Packet                    ``0x0020_0000``  Read/Write      ``0x0000_0000``
PACKET_COUNT_RST_N  Reset Packet Counts                                               ``0x0040_0000``  Read/Write      ``0x0000_0001``
STRIP_UNS_PRO       Remove The Header From Incoming Unsupported IPv4 Data             ``0x0100_0000``  Read/Write      ``0x0000_0001``
STRIP_UNS_ETH       Remove The Header From Incoming Unsupported Ethernet Data         ``0x0200_0000``  Read/Write      ``0x0000_0001``
CHK_IP_LENGTH       Check Received Packets Total IP Length and Cut off Extra Padding  ``0x0400_0000``  Read/Write      ``0x0000_0001``
==================  ================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: BROADCAST_EN [ rotate = 270 ]
      1: ARP_EN [ rotate = 270 ]
      2: PING_EN [ rotate = 270 ]
      3-7:  [ color = lightgrey ]
      8: PASS_UNS_ETHTYPE [ rotate = 270 ]
      9: PASS_UNS_IPV4 [ rotate = 270 ]
      10-15:  [ color = lightgrey ]
      16: DST_MAC_CHK_EN [ rotate = 270 ]
      17: SRC_MAC_CHK_EN [ rotate = 270 ]
      18: DST_IP_CHK_EN [ rotate = 270 ]
      19: SRC_IP_CHK_EN [ rotate = 270 ]
      20: DST_PORT_CHK_EN [ rotate = 270 ]
      21: SRC_PORT_CHK_EN [ rotate = 270 ]
      22: PACKET_COUNT_RST_N [ rotate = 270 ]
      23:  [ rotate = 270, color = lightgrey ]
      24: STRIP_UNS_PRO [ rotate = 270 ]
      25: STRIP_UNS_ETH [ rotate = 270 ]
      26: CHK_IP_LENGTH [ rotate = 270 ]
      27-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_CONTROL = { 'addr': 131144,
  'description': 'UDP Core Control Register',
  'fields': [ { 'description': 'Use Fixed Packet Size In Tx For Outgoing '
                               'Packets - Currently Unused',
                'is_bit': True,
                'mask': 8,
                'name': 'FIXED_PKT_SIZE',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 3},
              { 'description': 'Set UDP Checksum to Zero - Currently Unused',
                'is_bit': True,
                'mask': 16,
                'name': 'UDP_CHECKSUM_ZERO',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 4},
              { 'description': 'LUT Mode Enable - Use To Set Dst Addresses Of '
                               'Outgoing UDP Packets From LUT',
                'is_bit': True,
                'mask': 32,
                'name': 'LUT_MODE',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 5},
              { 'description': 'Use Bits 15:0 of tuser for destination UDP '
                               'port of outgoing packets',
                'is_bit': True,
                'mask': 64,
                'name': 'TUSER_DST_PRT',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 6},
              { 'description': 'Use Bits 31:16 of tuser for source UDP port of '
                               'outgoing packets',
                'is_bit': True,
                'mask': 128,
                'name': 'TUSER_SRC_PRT',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 7},
              { 'description': 'Soft Reset - Currently Unused',
                'is_bit': True,
                'mask': 32768,
                'name': 'RESET_N',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 15},
              { 'description': 'UDP Length For Fixed Packet Length - Currently '
                               'Unused',
                'is_bit': False,
                'mask': 4294901760,
                'name': 'UDP_LENGTH',
                'nof_bits': 16,
                'reset_value': '0x0008',
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_CONTROL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_CONTROL` generated from `XML2VHDL` output.

=================  ===========================================================================  ===============  ==============  ===============
**Register**
**Name:**          UDP_CORE_0_0_UDP_CORE_CONTROL_CONTROL
**Address:**       ``0x0002_0048``
**Description:**   UDP Core Control Register
**Bit Fields**     **Description**                                                              **Mask**         **Permission**  **Reset Value**
FIXED_PKT_SIZE     Use Fixed Packet Size In Tx For Outgoing Packets - Currently Unused          ``0x0000_0008``  Read/Write      ``0x0000_0000``
UDP_CHECKSUM_ZERO  Set UDP Checksum to Zero - Currently Unused                                  ``0x0000_0010``  Read/Write      ``0x0000_0001``
LUT_MODE           LUT Mode Enable - Use To Set Dst Addresses Of Outgoing UDP Packets From LUT  ``0x0000_0020``  Read/Write      ``0x0000_0000``
TUSER_DST_PRT      Use Bits 15:0 of tuser for destination UDP port of outgoing packets          ``0x0000_0040``  Read/Write      ``0x0000_0000``
TUSER_SRC_PRT      Use Bits 31:16 of tuser for source UDP port of outgoing packets              ``0x0000_0080``  Read/Write      ``0x0000_0000``
RESET_N            Soft Reset - Currently Unused                                                ``0x0000_8000``  Read/Write      ``0x0000_0001``
UDP_LENGTH         UDP Length For Fixed Packet Length - Currently Unused                        ``0xFFFF_0000``  Read/Write      ``0x0000_0008``
=================  ===========================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-2:  [ rotate = 270, color = lightgrey ]
      3: FIXED_PKT_SIZE [ rotate = 270 ]
      4: UDP_CHECKSUM_ZERO [ rotate = 270 ]
      5: LUT_MODE [ rotate = 270 ]
      6: TUSER_DST_PRT [ rotate = 270 ]
      7: TUSER_SRC_PRT [ rotate = 270 ]
      8-14:  [ color = lightgrey ]
      15: RESET_N [ rotate = 270 ]
      16-31: UDP_LENGTH
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_UDP_COUNT = { 'addr': 131148,
  'description': 'Counter For Valid UDP Packets',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_UDP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_UDP_COUNT` generated from `XML2VHDL` output.

================  =======================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_UDP_COUNT
**Address:**      ``0x0002_004C``
**Description:**  Counter For Valid UDP Packets
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UDP_COUNT
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_PING_COUNT = { 'addr': 131152,
  'description': 'Counter For Valid Ping Packets',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_PING_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_PING_COUNT` generated from `XML2VHDL` output.

================  ========================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_PING_COUNT
**Address:**      ``0x0002_0050``
**Description:**  Counter For Valid Ping Packets
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: PING_COUNT
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_ARP_COUNT = { 'addr': 131156,
  'description': 'Counter For Valid ARP Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_ARP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_ARP_COUNT` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_ARP_COUNT
**Address:**      ``0x0002_0054``
**Description:**  Counter For Valid ARP Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: ARP_COUNT
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_UNS_ETYPE_COUNT = { 'addr': 131160,
  'description': 'Counter Unsupported Etype Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_UNS_ETYPE_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_UNS_ETYPE_COUNT` generated from `XML2VHDL` output.

================  ====================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_UNS_ETYPE_COUNT
**Address:**      ``0x0002_0058``
**Description:**  Counter Unsupported Etype Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ====================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UNS_ETYPE_COUNT
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_UNS_PRO_COUNT = { 'addr': 131164,
  'description': 'Counter Unsupported Protocol Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_UNS_PRO_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_UNS_PRO_COUNT` generated from `XML2VHDL` output.

================  =======================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_UNS_PRO_COUNT
**Address:**      ``0x0002_005C``
**Description:**  Counter Unsupported Protocol Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UNS_PRO_COUNT
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_MAC_COUNT = { 'addr': 131168,
  'description': 'Counter For Dropped Mac Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_MAC_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_MAC_COUNT` generated from `XML2VHDL` output.

================  =======================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_MAC_COUNT
**Address:**      ``0x0002_0060``
**Description:**  Counter For Dropped Mac Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_MAC_COUNT
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_IP_COUNT = { 'addr': 131172,
  'description': 'Counter For Dropped IP Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_IP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_IP_COUNT` generated from `XML2VHDL` output.

================  ======================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_IP_COUNT
**Address:**      ``0x0002_0064``
**Description:**  Counter For Dropped IP Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_IP_COUNT
   }

"""

UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_PORT_COUNT = { 'addr': 131176,
  'description': 'Counter For Dropped Port Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_PORT_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_PORT_COUNT` generated from `XML2VHDL` output.

================  ========================================================
**Register**
**Name:**         UDP_CORE_0_0_UDP_CORE_CONTROL_DROPPED_PORT_COUNT
**Address:**      ``0x0002_0068``
**Description:**  Counter For Dropped Port Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ========================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_PORT_COUNT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER = { 'addr': 139264,
  'description': 'Source MAC Address Lower',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER',
  'nof_bits': 32,
  'reset_value': '0x00000201',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER
**Address:**      ``0x0002_2000``
**Description:**  Source MAC Address Lower
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0201``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SRC_MAC_ADDR_LOWER
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER = { 'addr': 139268,
  'description': 'Source MAC Address Upper',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER',
  'nof_bits': 16,
  'reset_value': '0x6200',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER
**Address:**      ``0x0002_2004``
**Description:**  Source MAC Address Upper
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_6200``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: SRC_MAC_ADDR_UPPER
      16-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER = { 'addr': 139276,
  'description': 'Destination MAC Address Lower',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER',
  'nof_bits': 32,
  'reset_value': '0x00000FF00',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER
**Address:**      ``0x0002_200C``
**Description:**  Destination MAC Address Lower
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_FF00``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DST_MAC_ADDR_LOWER
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER = { 'addr': 139280,
  'description': 'Destination MAC Address Upper',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER',
  'nof_bits': 16,
  'reset_value': '0x6200',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER
**Address:**      ``0x0002_2010``
**Description:**  Destination MAC Address Upper
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_6200``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: DST_MAC_ADDR_UPPER
      16-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_DST_IP_ADDR = { 'addr': 139300,
  'description': 'UDP Destination IP Address',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_DST_IP_ADDR',
  'nof_bits': 32,
  'reset_value': '0xC0A80201',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_DST_IP_ADDR` generated from `XML2VHDL` output.

================  =========================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_DST_IP_ADDR
**Address:**      ``0x0002_2024``
**Description:**  UDP Destination IP Address
**Permission:**   Read/Write
**Reset Value:**  ``0xC0A8_0201``
================  =========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DST_IP_ADDR
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_IP_ADDR = { 'addr': 139304,
  'description': 'UDP Source IP Address',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_IP_ADDR',
  'nof_bits': 32,
  'reset_value': '0xC0A8020B',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_IP_ADDR` generated from `XML2VHDL` output.

================  =========================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_SRC_IP_ADDR
**Address:**      ``0x0002_2028``
**Description:**  UDP Source IP Address
**Permission:**   Read/Write
**Reset Value:**  ``0xC0A8_020B``
================  =========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SRC_IP_ADDR
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_UDP_PORTS = { 'addr': 139308,
  'description': 'UDP Ports',
  'fields': [ { 'description': 'UDP Source Port',
                'is_bit': False,
                'mask': 65535,
                'name': 'SRC_PORT',
                'nof_bits': 16,
                'reset_value': '0xf0d0',
                'shiftr': 0},
              { 'description': 'UDP Destination Port',
                'is_bit': False,
                'mask': 4294901760,
                'name': 'DST_PORT',
                'nof_bits': 16,
                'reset_value': '0xf0d1',
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_UDP_PORTS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_UDP_PORTS` generated from `XML2VHDL` output.

================  =======================================  ===============  ==============  ===============
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_UDP_PORTS
**Address:**      ``0x0002_202C``
**Description:**  UDP Ports
**Bit Fields**    **Description**                          **Mask**         **Permission**  **Reset Value**
SRC_PORT          UDP Source Port                          ``0x0000_FFFF``  Read/Write      ``0x0000_F0D0``
DST_PORT          UDP Destination Port                     ``0xFFFF_0000``  Read/Write      ``0x0000_F0D1``
================  =======================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: SRC_PORT
      16-31: DST_PORT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_FILTER_CONTROL = { 'addr': 139320,
  'description': 'Controls the level of filtering in the UDP core Rx',
  'fields': [ { 'description': 'Enables Broadcast Recieving',
                'is_bit': True,
                'mask': 1,
                'name': 'BROADCAST_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 0},
              { 'description': 'Enables ARPs',
                'is_bit': True,
                'mask': 2,
                'name': 'ARP_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 1},
              { 'description': 'Enables Pings',
                'is_bit': True,
                'mask': 4,
                'name': 'PING_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 2},
              { 'description': 'Enable Passing of Unsupported Ethernet Packets',
                'is_bit': True,
                'mask': 256,
                'name': 'PASS_UNS_ETHTYPE',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 8},
              { 'description': 'Enable Passing of Unsupported IPv4 Packets',
                'is_bit': True,
                'mask': 512,
                'name': 'PASS_UNS_IPV4',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 9},
              { 'description': 'Check Dest MAC address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 65536,
                'name': 'DST_MAC_CHK_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 16},
              { 'description': 'Check Source MAC address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 131072,
                'name': 'SRC_MAC_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 17},
              { 'description': 'Check Dest IP address Field Of Incoming Packet',
                'is_bit': True,
                'mask': 262144,
                'name': 'DST_IP_CHK_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 18},
              { 'description': 'Check Source IP address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 524288,
                'name': 'SRC_IP_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 19},
              { 'description': 'Check Dest UDP Port Field Of Incoming Packet',
                'is_bit': True,
                'mask': 1048576,
                'name': 'DST_PORT_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 20},
              { 'description': 'Check Source UDP Port Field Of Incoming Packet',
                'is_bit': True,
                'mask': 2097152,
                'name': 'SRC_PORT_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 21},
              { 'description': 'Reset Packet Counts',
                'is_bit': True,
                'mask': 4194304,
                'name': 'PACKET_COUNT_RST_N',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 22},
              { 'description': 'Remove The Header From Incoming Unsupported '
                               'IPv4 Data',
                'is_bit': True,
                'mask': 16777216,
                'name': 'STRIP_UNS_PRO',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 24},
              { 'description': 'Remove The Header From Incoming Unsupported '
                               'Ethernet Data',
                'is_bit': True,
                'mask': 33554432,
                'name': 'STRIP_UNS_ETH',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 25},
              { 'description': 'Check Received Packets Total IP Length and Cut '
                               'off Extra Padding',
                'is_bit': True,
                'mask': 67108864,
                'name': 'CHK_IP_LENGTH',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 26}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_FILTER_CONTROL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_FILTER_CONTROL` generated from `XML2VHDL` output.

==================  ================================================================  ===============  ==============  ===============
**Register**
**Name:**           UDP_CORE_0_1_UDP_CORE_CONTROL_FILTER_CONTROL
**Address:**        ``0x0002_2038``
**Description:**    Controls the level of filtering in the UDP core Rx
**Bit Fields**      **Description**                                                   **Mask**         **Permission**  **Reset Value**
BROADCAST_EN        Enables Broadcast Recieving                                       ``0x0000_0001``  Read/Write      ``0x0000_0001``
ARP_EN              Enables ARPs                                                      ``0x0000_0002``  Read/Write      ``0x0000_0001``
PING_EN             Enables Pings                                                     ``0x0000_0004``  Read/Write      ``0x0000_0001``
PASS_UNS_ETHTYPE    Enable Passing of Unsupported Ethernet Packets                    ``0x0000_0100``  Read/Write      ``0x0000_0001``
PASS_UNS_IPV4       Enable Passing of Unsupported IPv4 Packets                        ``0x0000_0200``  Read/Write      ``0x0000_0001``
DST_MAC_CHK_EN      Check Dest MAC address Field Of Incoming Packet                   ``0x0001_0000``  Read/Write      ``0x0000_0001``
SRC_MAC_CHK_EN      Check Source MAC address Field Of Incoming Packet                 ``0x0002_0000``  Read/Write      ``0x0000_0000``
DST_IP_CHK_EN       Check Dest IP address Field Of Incoming Packet                    ``0x0004_0000``  Read/Write      ``0x0000_0001``
SRC_IP_CHK_EN       Check Source IP address Field Of Incoming Packet                  ``0x0008_0000``  Read/Write      ``0x0000_0000``
DST_PORT_CHK_EN     Check Dest UDP Port Field Of Incoming Packet                      ``0x0010_0000``  Read/Write      ``0x0000_0000``
SRC_PORT_CHK_EN     Check Source UDP Port Field Of Incoming Packet                    ``0x0020_0000``  Read/Write      ``0x0000_0000``
PACKET_COUNT_RST_N  Reset Packet Counts                                               ``0x0040_0000``  Read/Write      ``0x0000_0001``
STRIP_UNS_PRO       Remove The Header From Incoming Unsupported IPv4 Data             ``0x0100_0000``  Read/Write      ``0x0000_0001``
STRIP_UNS_ETH       Remove The Header From Incoming Unsupported Ethernet Data         ``0x0200_0000``  Read/Write      ``0x0000_0001``
CHK_IP_LENGTH       Check Received Packets Total IP Length and Cut off Extra Padding  ``0x0400_0000``  Read/Write      ``0x0000_0001``
==================  ================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: BROADCAST_EN [ rotate = 270 ]
      1: ARP_EN [ rotate = 270 ]
      2: PING_EN [ rotate = 270 ]
      3-7:  [ color = lightgrey ]
      8: PASS_UNS_ETHTYPE [ rotate = 270 ]
      9: PASS_UNS_IPV4 [ rotate = 270 ]
      10-15:  [ color = lightgrey ]
      16: DST_MAC_CHK_EN [ rotate = 270 ]
      17: SRC_MAC_CHK_EN [ rotate = 270 ]
      18: DST_IP_CHK_EN [ rotate = 270 ]
      19: SRC_IP_CHK_EN [ rotate = 270 ]
      20: DST_PORT_CHK_EN [ rotate = 270 ]
      21: SRC_PORT_CHK_EN [ rotate = 270 ]
      22: PACKET_COUNT_RST_N [ rotate = 270 ]
      23:  [ rotate = 270, color = lightgrey ]
      24: STRIP_UNS_PRO [ rotate = 270 ]
      25: STRIP_UNS_ETH [ rotate = 270 ]
      26: CHK_IP_LENGTH [ rotate = 270 ]
      27-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_IFG = { 'addr': 139328,
  'description': 'Used To Add Extra Delay Between Packets In Tx Path',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_IFG',
  'nof_bits': 16,
  'reset_value': '0x0000',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_IFG` generated from `XML2VHDL` output.

================  ==================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_IFG
**Address:**      ``0x0002_2040``
**Description:**  Used To Add Extra Delay Between Packets In Tx Path
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ==================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: IFG
      16-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_CONTROL = { 'addr': 139336,
  'description': 'UDP Core Control Register',
  'fields': [ { 'description': 'Use Fixed Packet Size In Tx For Outgoing '
                               'Packets - Currently Unused',
                'is_bit': True,
                'mask': 8,
                'name': 'FIXED_PKT_SIZE',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 3},
              { 'description': 'Set UDP Checksum to Zero - Currently Unused',
                'is_bit': True,
                'mask': 16,
                'name': 'UDP_CHECKSUM_ZERO',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 4},
              { 'description': 'LUT Mode Enable - Use To Set Dst Addresses Of '
                               'Outgoing UDP Packets From LUT',
                'is_bit': True,
                'mask': 32,
                'name': 'LUT_MODE',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 5},
              { 'description': 'Use Bits 15:0 of tuser for destination UDP '
                               'port of outgoing packets',
                'is_bit': True,
                'mask': 64,
                'name': 'TUSER_DST_PRT',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 6},
              { 'description': 'Use Bits 31:16 of tuser for source UDP port of '
                               'outgoing packets',
                'is_bit': True,
                'mask': 128,
                'name': 'TUSER_SRC_PRT',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 7},
              { 'description': 'Soft Reset - Currently Unused',
                'is_bit': True,
                'mask': 32768,
                'name': 'RESET_N',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 15},
              { 'description': 'UDP Length For Fixed Packet Length - Currently '
                               'Unused',
                'is_bit': False,
                'mask': 4294901760,
                'name': 'UDP_LENGTH',
                'nof_bits': 16,
                'reset_value': '0x0008',
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_CONTROL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_CONTROL` generated from `XML2VHDL` output.

=================  ===========================================================================  ===============  ==============  ===============
**Register**
**Name:**          UDP_CORE_0_1_UDP_CORE_CONTROL_CONTROL
**Address:**       ``0x0002_2048``
**Description:**   UDP Core Control Register
**Bit Fields**     **Description**                                                              **Mask**         **Permission**  **Reset Value**
FIXED_PKT_SIZE     Use Fixed Packet Size In Tx For Outgoing Packets - Currently Unused          ``0x0000_0008``  Read/Write      ``0x0000_0000``
UDP_CHECKSUM_ZERO  Set UDP Checksum to Zero - Currently Unused                                  ``0x0000_0010``  Read/Write      ``0x0000_0001``
LUT_MODE           LUT Mode Enable - Use To Set Dst Addresses Of Outgoing UDP Packets From LUT  ``0x0000_0020``  Read/Write      ``0x0000_0000``
TUSER_DST_PRT      Use Bits 15:0 of tuser for destination UDP port of outgoing packets          ``0x0000_0040``  Read/Write      ``0x0000_0000``
TUSER_SRC_PRT      Use Bits 31:16 of tuser for source UDP port of outgoing packets              ``0x0000_0080``  Read/Write      ``0x0000_0000``
RESET_N            Soft Reset - Currently Unused                                                ``0x0000_8000``  Read/Write      ``0x0000_0001``
UDP_LENGTH         UDP Length For Fixed Packet Length - Currently Unused                        ``0xFFFF_0000``  Read/Write      ``0x0000_0008``
=================  ===========================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-2:  [ rotate = 270, color = lightgrey ]
      3: FIXED_PKT_SIZE [ rotate = 270 ]
      4: UDP_CHECKSUM_ZERO [ rotate = 270 ]
      5: LUT_MODE [ rotate = 270 ]
      6: TUSER_DST_PRT [ rotate = 270 ]
      7: TUSER_SRC_PRT [ rotate = 270 ]
      8-14:  [ color = lightgrey ]
      15: RESET_N [ rotate = 270 ]
      16-31: UDP_LENGTH
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_UDP_COUNT = { 'addr': 139340,
  'description': 'Counter For Valid UDP Packets',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_UDP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_UDP_COUNT` generated from `XML2VHDL` output.

================  =======================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_UDP_COUNT
**Address:**      ``0x0002_204C``
**Description:**  Counter For Valid UDP Packets
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UDP_COUNT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_PING_COUNT = { 'addr': 139344,
  'description': 'Counter For Valid Ping Packets',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_PING_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_PING_COUNT` generated from `XML2VHDL` output.

================  ========================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_PING_COUNT
**Address:**      ``0x0002_2050``
**Description:**  Counter For Valid Ping Packets
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: PING_COUNT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_ARP_COUNT = { 'addr': 139348,
  'description': 'Counter For Valid ARP Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_ARP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_ARP_COUNT` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_ARP_COUNT
**Address:**      ``0x0002_2054``
**Description:**  Counter For Valid ARP Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: ARP_COUNT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_UNS_ETYPE_COUNT = { 'addr': 139352,
  'description': 'Counter Unsupported Etype Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_UNS_ETYPE_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_UNS_ETYPE_COUNT` generated from `XML2VHDL` output.

================  ====================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_UNS_ETYPE_COUNT
**Address:**      ``0x0002_2058``
**Description:**  Counter Unsupported Etype Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ====================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UNS_ETYPE_COUNT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_UNS_PRO_COUNT = { 'addr': 139356,
  'description': 'Counter Unsupported Protocol Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_UNS_PRO_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_UNS_PRO_COUNT` generated from `XML2VHDL` output.

================  =======================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_UNS_PRO_COUNT
**Address:**      ``0x0002_205C``
**Description:**  Counter Unsupported Protocol Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UNS_PRO_COUNT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_MAC_COUNT = { 'addr': 139360,
  'description': 'Counter For Dropped Mac Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_MAC_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_MAC_COUNT` generated from `XML2VHDL` output.

================  =======================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_MAC_COUNT
**Address:**      ``0x0002_2060``
**Description:**  Counter For Dropped Mac Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_MAC_COUNT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_IP_COUNT = { 'addr': 139364,
  'description': 'Counter For Dropped IP Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_IP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_IP_COUNT` generated from `XML2VHDL` output.

================  ======================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_IP_COUNT
**Address:**      ``0x0002_2064``
**Description:**  Counter For Dropped IP Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_IP_COUNT
   }

"""

UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_PORT_COUNT = { 'addr': 139368,
  'description': 'Counter For Dropped Port Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_PORT_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_PORT_COUNT` generated from `XML2VHDL` output.

================  ========================================================
**Register**
**Name:**         UDP_CORE_0_1_UDP_CORE_CONTROL_DROPPED_PORT_COUNT
**Address:**      ``0x0002_2068``
**Description:**  Counter For Dropped Port Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ========================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_PORT_COUNT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER = { 'addr': 147456,
  'description': 'Source MAC Address Lower',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER',
  'nof_bits': 32,
  'reset_value': '0x00000201',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER
**Address:**      ``0x0002_4000``
**Description:**  Source MAC Address Lower
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0201``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SRC_MAC_ADDR_LOWER
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER = { 'addr': 147460,
  'description': 'Source MAC Address Upper',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER',
  'nof_bits': 16,
  'reset_value': '0x6200',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER
**Address:**      ``0x0002_4004``
**Description:**  Source MAC Address Upper
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_6200``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: SRC_MAC_ADDR_UPPER
      16-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER = { 'addr': 147468,
  'description': 'Destination MAC Address Lower',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER',
  'nof_bits': 32,
  'reset_value': '0x00000FF00',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER
**Address:**      ``0x0002_400C``
**Description:**  Destination MAC Address Lower
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_FF00``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DST_MAC_ADDR_LOWER
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER = { 'addr': 147472,
  'description': 'Destination MAC Address Upper',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER',
  'nof_bits': 16,
  'reset_value': '0x6200',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER
**Address:**      ``0x0002_4010``
**Description:**  Destination MAC Address Upper
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_6200``
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: DST_MAC_ADDR_UPPER
      16-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_DST_IP_ADDR = { 'addr': 147492,
  'description': 'UDP Destination IP Address',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_DST_IP_ADDR',
  'nof_bits': 32,
  'reset_value': '0xC0A80201',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_DST_IP_ADDR` generated from `XML2VHDL` output.

================  =========================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_DST_IP_ADDR
**Address:**      ``0x0002_4024``
**Description:**  UDP Destination IP Address
**Permission:**   Read/Write
**Reset Value:**  ``0xC0A8_0201``
================  =========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DST_IP_ADDR
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_IP_ADDR = { 'addr': 147496,
  'description': 'UDP Source IP Address',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_IP_ADDR',
  'nof_bits': 32,
  'reset_value': '0xC0A8020B',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_IP_ADDR` generated from `XML2VHDL` output.

================  =========================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_SRC_IP_ADDR
**Address:**      ``0x0002_4028``
**Description:**  UDP Source IP Address
**Permission:**   Read/Write
**Reset Value:**  ``0xC0A8_020B``
================  =========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SRC_IP_ADDR
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_UDP_PORTS = { 'addr': 147500,
  'description': 'UDP Ports',
  'fields': [ { 'description': 'UDP Source Port',
                'is_bit': False,
                'mask': 65535,
                'name': 'SRC_PORT',
                'nof_bits': 16,
                'reset_value': '0xf0d0',
                'shiftr': 0},
              { 'description': 'UDP Destination Port',
                'is_bit': False,
                'mask': 4294901760,
                'name': 'DST_PORT',
                'nof_bits': 16,
                'reset_value': '0xf0d1',
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_UDP_PORTS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_UDP_PORTS` generated from `XML2VHDL` output.

================  =======================================  ===============  ==============  ===============
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_UDP_PORTS
**Address:**      ``0x0002_402C``
**Description:**  UDP Ports
**Bit Fields**    **Description**                          **Mask**         **Permission**  **Reset Value**
SRC_PORT          UDP Source Port                          ``0x0000_FFFF``  Read/Write      ``0x0000_F0D0``
DST_PORT          UDP Destination Port                     ``0xFFFF_0000``  Read/Write      ``0x0000_F0D1``
================  =======================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-15: SRC_PORT
      16-31: DST_PORT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_FILTER_CONTROL = { 'addr': 147512,
  'description': 'Controls the level of filtering in the UDP core Rx',
  'fields': [ { 'description': 'Enables Broadcast Recieving',
                'is_bit': True,
                'mask': 1,
                'name': 'BROADCAST_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 0},
              { 'description': 'Enables ARPs',
                'is_bit': True,
                'mask': 2,
                'name': 'ARP_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 1},
              { 'description': 'Enables Pings',
                'is_bit': True,
                'mask': 4,
                'name': 'PING_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 2},
              { 'description': 'Enable Passing of Unsupported Ethernet Packets',
                'is_bit': True,
                'mask': 256,
                'name': 'PASS_UNS_ETHTYPE',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 8},
              { 'description': 'Enable Passing of Unsupported IPv4 Packets',
                'is_bit': True,
                'mask': 512,
                'name': 'PASS_UNS_IPV4',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 9},
              { 'description': 'Check Dest MAC address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 65536,
                'name': 'DST_MAC_CHK_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 16},
              { 'description': 'Check Source MAC address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 131072,
                'name': 'SRC_MAC_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 17},
              { 'description': 'Check Dest IP address Field Of Incoming Packet',
                'is_bit': True,
                'mask': 262144,
                'name': 'DST_IP_CHK_EN',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 18},
              { 'description': 'Check Source IP address Field Of Incoming '
                               'Packet',
                'is_bit': True,
                'mask': 524288,
                'name': 'SRC_IP_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 19},
              { 'description': 'Check Dest UDP Port Field Of Incoming Packet',
                'is_bit': True,
                'mask': 1048576,
                'name': 'DST_PORT_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 20},
              { 'description': 'Check Source UDP Port Field Of Incoming Packet',
                'is_bit': True,
                'mask': 2097152,
                'name': 'SRC_PORT_CHK_EN',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 21},
              { 'description': 'Reset Packet Counts',
                'is_bit': True,
                'mask': 4194304,
                'name': 'PACKET_COUNT_RST_N',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 22},
              { 'description': 'Remove The Header From Incoming Unsupported '
                               'IPv4 Data',
                'is_bit': True,
                'mask': 16777216,
                'name': 'STRIP_UNS_PRO',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 24},
              { 'description': 'Remove The Header From Incoming Unsupported '
                               'Ethernet Data',
                'is_bit': True,
                'mask': 33554432,
                'name': 'STRIP_UNS_ETH',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 25},
              { 'description': 'Check Received Packets Total IP Length and Cut '
                               'off Extra Padding',
                'is_bit': True,
                'mask': 67108864,
                'name': 'CHK_IP_LENGTH',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 26}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_FILTER_CONTROL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_FILTER_CONTROL` generated from `XML2VHDL` output.

==================  ================================================================  ===============  ==============  ===============
**Register**
**Name:**           UDP_CORE_0_2_UDP_CORE_CONTROL_FILTER_CONTROL
**Address:**        ``0x0002_4038``
**Description:**    Controls the level of filtering in the UDP core Rx
**Bit Fields**      **Description**                                                   **Mask**         **Permission**  **Reset Value**
BROADCAST_EN        Enables Broadcast Recieving                                       ``0x0000_0001``  Read/Write      ``0x0000_0001``
ARP_EN              Enables ARPs                                                      ``0x0000_0002``  Read/Write      ``0x0000_0001``
PING_EN             Enables Pings                                                     ``0x0000_0004``  Read/Write      ``0x0000_0001``
PASS_UNS_ETHTYPE    Enable Passing of Unsupported Ethernet Packets                    ``0x0000_0100``  Read/Write      ``0x0000_0001``
PASS_UNS_IPV4       Enable Passing of Unsupported IPv4 Packets                        ``0x0000_0200``  Read/Write      ``0x0000_0001``
DST_MAC_CHK_EN      Check Dest MAC address Field Of Incoming Packet                   ``0x0001_0000``  Read/Write      ``0x0000_0001``
SRC_MAC_CHK_EN      Check Source MAC address Field Of Incoming Packet                 ``0x0002_0000``  Read/Write      ``0x0000_0000``
DST_IP_CHK_EN       Check Dest IP address Field Of Incoming Packet                    ``0x0004_0000``  Read/Write      ``0x0000_0001``
SRC_IP_CHK_EN       Check Source IP address Field Of Incoming Packet                  ``0x0008_0000``  Read/Write      ``0x0000_0000``
DST_PORT_CHK_EN     Check Dest UDP Port Field Of Incoming Packet                      ``0x0010_0000``  Read/Write      ``0x0000_0000``
SRC_PORT_CHK_EN     Check Source UDP Port Field Of Incoming Packet                    ``0x0020_0000``  Read/Write      ``0x0000_0000``
PACKET_COUNT_RST_N  Reset Packet Counts                                               ``0x0040_0000``  Read/Write      ``0x0000_0001``
STRIP_UNS_PRO       Remove The Header From Incoming Unsupported IPv4 Data             ``0x0100_0000``  Read/Write      ``0x0000_0001``
STRIP_UNS_ETH       Remove The Header From Incoming Unsupported Ethernet Data         ``0x0200_0000``  Read/Write      ``0x0000_0001``
CHK_IP_LENGTH       Check Received Packets Total IP Length and Cut off Extra Padding  ``0x0400_0000``  Read/Write      ``0x0000_0001``
==================  ================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: BROADCAST_EN [ rotate = 270 ]
      1: ARP_EN [ rotate = 270 ]
      2: PING_EN [ rotate = 270 ]
      3-7:  [ color = lightgrey ]
      8: PASS_UNS_ETHTYPE [ rotate = 270 ]
      9: PASS_UNS_IPV4 [ rotate = 270 ]
      10-15:  [ color = lightgrey ]
      16: DST_MAC_CHK_EN [ rotate = 270 ]
      17: SRC_MAC_CHK_EN [ rotate = 270 ]
      18: DST_IP_CHK_EN [ rotate = 270 ]
      19: SRC_IP_CHK_EN [ rotate = 270 ]
      20: DST_PORT_CHK_EN [ rotate = 270 ]
      21: SRC_PORT_CHK_EN [ rotate = 270 ]
      22: PACKET_COUNT_RST_N [ rotate = 270 ]
      23:  [ rotate = 270, color = lightgrey ]
      24: STRIP_UNS_PRO [ rotate = 270 ]
      25: STRIP_UNS_ETH [ rotate = 270 ]
      26: CHK_IP_LENGTH [ rotate = 270 ]
      27-31:  [ color = lightgrey ]
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_CONTROL = { 'addr': 147528,
  'description': 'UDP Core Control Register',
  'fields': [ { 'description': 'Use Fixed Packet Size In Tx For Outgoing '
                               'Packets - Currently Unused',
                'is_bit': True,
                'mask': 8,
                'name': 'FIXED_PKT_SIZE',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 3},
              { 'description': 'Set UDP Checksum to Zero - Currently Unused',
                'is_bit': True,
                'mask': 16,
                'name': 'UDP_CHECKSUM_ZERO',
                'nof_bits': 1,
                'reset_value': '1',
                'shiftr': 4},
              { 'description': 'LUT Mode Enable - Use To Set Dst Addresses Of '
                               'Outgoing UDP Packets From LUT',
                'is_bit': True,
                'mask': 32,
                'name': 'LUT_MODE',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 5},
              { 'description': 'Use Bits 15:0 of tuser for destination UDP '
                               'port of outgoing packets',
                'is_bit': True,
                'mask': 64,
                'name': 'TUSER_DST_PRT',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 6},
              { 'description': 'Use Bits 31:16 of tuser for source UDP port of '
                               'outgoing packets',
                'is_bit': True,
                'mask': 128,
                'name': 'TUSER_SRC_PRT',
                'nof_bits': 1,
                'reset_value': '0',
                'shiftr': 7},
              { 'description': 'Soft Reset - Currently Unused',
                'is_bit': True,
                'mask': 32768,
                'name': 'RESET_N',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 15},
              { 'description': 'UDP Length For Fixed Packet Length - Currently '
                               'Unused',
                'is_bit': False,
                'mask': 4294901760,
                'name': 'UDP_LENGTH',
                'nof_bits': 16,
                'reset_value': '0x0008',
                'shiftr': 16}],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_CONTROL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_CONTROL` generated from `XML2VHDL` output.

=================  ===========================================================================  ===============  ==============  ===============
**Register**
**Name:**          UDP_CORE_0_2_UDP_CORE_CONTROL_CONTROL
**Address:**       ``0x0002_4048``
**Description:**   UDP Core Control Register
**Bit Fields**     **Description**                                                              **Mask**         **Permission**  **Reset Value**
FIXED_PKT_SIZE     Use Fixed Packet Size In Tx For Outgoing Packets - Currently Unused          ``0x0000_0008``  Read/Write      ``0x0000_0000``
UDP_CHECKSUM_ZERO  Set UDP Checksum to Zero - Currently Unused                                  ``0x0000_0010``  Read/Write      ``0x0000_0001``
LUT_MODE           LUT Mode Enable - Use To Set Dst Addresses Of Outgoing UDP Packets From LUT  ``0x0000_0020``  Read/Write      ``0x0000_0000``
TUSER_DST_PRT      Use Bits 15:0 of tuser for destination UDP port of outgoing packets          ``0x0000_0040``  Read/Write      ``0x0000_0000``
TUSER_SRC_PRT      Use Bits 31:16 of tuser for source UDP port of outgoing packets              ``0x0000_0080``  Read/Write      ``0x0000_0000``
RESET_N            Soft Reset - Currently Unused                                                ``0x0000_8000``  Read/Write      ``0x0000_0001``
UDP_LENGTH         UDP Length For Fixed Packet Length - Currently Unused                        ``0xFFFF_0000``  Read/Write      ``0x0000_0008``
=================  ===========================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-2:  [ rotate = 270, color = lightgrey ]
      3: FIXED_PKT_SIZE [ rotate = 270 ]
      4: UDP_CHECKSUM_ZERO [ rotate = 270 ]
      5: LUT_MODE [ rotate = 270 ]
      6: TUSER_DST_PRT [ rotate = 270 ]
      7: TUSER_SRC_PRT [ rotate = 270 ]
      8-14:  [ color = lightgrey ]
      15: RESET_N [ rotate = 270 ]
      16-31: UDP_LENGTH
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_UDP_COUNT = { 'addr': 147532,
  'description': 'Counter For Valid UDP Packets',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_UDP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_UDP_COUNT` generated from `XML2VHDL` output.

================  =======================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_UDP_COUNT
**Address:**      ``0x0002_404C``
**Description:**  Counter For Valid UDP Packets
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UDP_COUNT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_PING_COUNT = { 'addr': 147536,
  'description': 'Counter For Valid Ping Packets',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_PING_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_PING_COUNT` generated from `XML2VHDL` output.

================  ========================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_PING_COUNT
**Address:**      ``0x0002_4050``
**Description:**  Counter For Valid Ping Packets
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: PING_COUNT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_ARP_COUNT = { 'addr': 147540,
  'description': 'Counter For Valid ARP Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_ARP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_ARP_COUNT` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_ARP_COUNT
**Address:**      ``0x0002_4054``
**Description:**  Counter For Valid ARP Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: ARP_COUNT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_UNS_ETYPE_COUNT = { 'addr': 147544,
  'description': 'Counter Unsupported Etype Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_UNS_ETYPE_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_UNS_ETYPE_COUNT` generated from `XML2VHDL` output.

================  ====================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_UNS_ETYPE_COUNT
**Address:**      ``0x0002_4058``
**Description:**  Counter Unsupported Etype Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ====================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UNS_ETYPE_COUNT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_UNS_PRO_COUNT = { 'addr': 147548,
  'description': 'Counter Unsupported Protocol Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_UNS_PRO_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_UNS_PRO_COUNT` generated from `XML2VHDL` output.

================  =======================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_UNS_PRO_COUNT
**Address:**      ``0x0002_405C``
**Description:**  Counter Unsupported Protocol Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UNS_PRO_COUNT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_MAC_COUNT = { 'addr': 147552,
  'description': 'Counter For Dropped Mac Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_MAC_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_MAC_COUNT` generated from `XML2VHDL` output.

================  =======================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_MAC_COUNT
**Address:**      ``0x0002_4060``
**Description:**  Counter For Dropped Mac Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_MAC_COUNT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_IP_COUNT = { 'addr': 147556,
  'description': 'Counter For Dropped IP Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_IP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_IP_COUNT` generated from `XML2VHDL` output.

================  ======================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_IP_COUNT
**Address:**      ``0x0002_4064``
**Description:**  Counter For Dropped IP Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ======================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_IP_COUNT
   }

"""

UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_PORT_COUNT = { 'addr': 147560,
  'description': 'Counter For Dropped Port Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_PORT_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_PORT_COUNT` generated from `XML2VHDL` output.

================  ========================================================
**Register**
**Name:**         UDP_CORE_0_2_UDP_CORE_CONTROL_DROPPED_PORT_COUNT
**Address:**      ``0x0002_4068``
**Description:**  Counter For Dropped Port Addr Packets Detected In Filter
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ========================================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DROPPED_PORT_COUNT
   }

"""

QSFP_1_GIE = { 'addr': 524316,
  'description': 'Global interrupt enable',
  'fields': [ { 'description': 'Reserved',
                'is_bit': False,
                'mask': 2147483647,
                'name': 'RSV_0',
                'nof_bits': 31,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Global interrupt enable',
                'is_bit': True,
                'mask': 2147483648,
                'name': 'GIE',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 31}],
  'mask': 4294967295,
  'name': 'QSFP_1_GIE',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_GIE` generated from `XML2VHDL` output.

================  =======================  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_GIE
**Address:**      ``0x0008_001C``
**Description:**  Global interrupt enable
**Bit Fields**    **Description**          **Mask**         **Permission**  **Reset Value**
RSV_0             Reserved                 ``0x7FFF_FFFF``  Read/Write      ``0x0000_0000``
GIE               Global interrupt enable  ``0x8000_0000``  Read/Write      ``0x0000_0000``
================  =======================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-30: RSV_0 [ color = lightgrey ]
      31: GIE [ rotate = 270 ]
   }

"""

QSFP_1_SOFTR = { 'addr': 524352,
  'description': 'Soft Reset Register',
  'fields': [ { 'description': 'Reset key: 0xA',
                'is_bit': False,
                'mask': 15,
                'name': 'RKEY',
                'nof_bits': 4,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967280,
                'name': 'RSV_0',
                'nof_bits': 28,
                'reset_value': '0x0',
                'shiftr': 4}],
  'mask': 4294967295,
  'name': 'QSFP_1_SOFTR',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_SOFTR` generated from `XML2VHDL` output.

================  ===================  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_SOFTR
**Address:**      ``0x0008_0040``
**Description:**  Soft Reset Register
**Bit Fields**    **Description**      **Mask**         **Permission**  **Reset Value**
RKEY              Reset key: 0xA       ``0x0000_000F``  Read/Write      ``0x0000_0000``
RSV_0             Reserved             ``0xFFFF_FFF0``  Read/Write      ``0x0000_0000``
================  ===================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-3: RKEY
      4-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_CTRL_REG = { 'addr': 524544,
  'description': 'Control Register',
  'fields': [ { 'description': 'AXI IIC enable',
                'is_bit': True,
                'mask': 1,
                'name': 'EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Tx FIFO reset',
                'is_bit': True,
                'mask': 2,
                'name': 'RX_FIFO_RESET',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Master/Slave mode select',
                'is_bit': True,
                'mask': 4,
                'name': 'MSMS',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Tx/Rx mode select',
                'is_bit': True,
                'mask': 8,
                'name': 'TX',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'Tx acknowledge enable',
                'is_bit': True,
                'mask': 16,
                'name': 'TXAK',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Repeat start',
                'is_bit': True,
                'mask': 32,
                'name': 'RSTA',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'General call enable',
                'is_bit': True,
                'mask': 64,
                'name': 'GC_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967168,
                'name': 'RSV_0',
                'nof_bits': 25,
                'reset_value': '0x0',
                'shiftr': 7}],
  'mask': 4294967295,
  'name': 'QSFP_1_CTRL_REG',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_CTRL_REG` generated from `XML2VHDL` output.

================  ========================  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_CTRL_REG
**Address:**      ``0x0008_0100``
**Description:**  Control Register
**Bit Fields**    **Description**           **Mask**         **Permission**  **Reset Value**
EN                AXI IIC enable            ``0x0000_0001``  Read/Write      ``0x0000_0000``
RX_FIFO_RESET     Tx FIFO reset             ``0x0000_0002``  Read/Write      ``0x0000_0000``
MSMS              Master/Slave mode select  ``0x0000_0004``  Read/Write      ``0x0000_0000``
TX                Tx/Rx mode select         ``0x0000_0008``  Read/Write      ``0x0000_0000``
TXAK              Tx acknowledge enable     ``0x0000_0010``  Read/Write      ``0x0000_0000``
RSTA              Repeat start              ``0x0000_0020``  Read/Write      ``0x0000_0000``
GC_EN             General call enable       ``0x0000_0040``  Read/Write      ``0x0000_0000``
RSV_0             Reserved                  ``0xFFFF_FF80``  Read/Write      ``0x0000_0000``
================  ========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: EN [ rotate = 270 ]
      1: RX_FIFO_RESET [ rotate = 270 ]
      2: MSMS [ rotate = 270 ]
      3: TX [ rotate = 270 ]
      4: TXAK [ rotate = 270 ]
      5: RSTA [ rotate = 270 ]
      6: GC_EN [ rotate = 270 ]
      7-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_STAT_REG = { 'addr': 524548,
  'description': 'Status Register',
  'fields': [ { 'description': 'Addressed by general call',
                'is_bit': True,
                'mask': 1,
                'name': 'AGBC',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Addressed as slave',
                'is_bit': True,
                'mask': 2,
                'name': 'AAS',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Bus busy',
                'is_bit': True,
                'mask': 4,
                'name': 'BB',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Slave read/write',
                'is_bit': True,
                'mask': 8,
                'name': 'SRW',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'Tx FIFO full',
                'is_bit': True,
                'mask': 16,
                'name': 'TX_FIFO_FULL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Rx FIFO full',
                'is_bit': True,
                'mask': 32,
                'name': 'RX_FIFO_FULL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'Rx FIFO empty',
                'is_bit': True,
                'mask': 64,
                'name': 'RX_FIFO_EMPTY',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'Tx FIFO empty',
                'is_bit': True,
                'mask': 128,
                'name': 'TX_FIFO_EMPTY',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 7},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967040,
                'name': 'RSV_0',
                'nof_bits': 24,
                'reset_value': '0x0',
                'shiftr': 8}],
  'mask': 4294967295,
  'name': 'QSFP_1_STAT_REG',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_STAT_REG` generated from `XML2VHDL` output.

================  =========================  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_STAT_REG
**Address:**      ``0x0008_0104``
**Description:**  Status Register
**Bit Fields**    **Description**            **Mask**         **Permission**  **Reset Value**
AGBC              Addressed by general call  ``0x0000_0001``  Read/Write      ``0x0000_0000``
AAS               Addressed as slave         ``0x0000_0002``  Read/Write      ``0x0000_0000``
BB                Bus busy                   ``0x0000_0004``  Read/Write      ``0x0000_0000``
SRW               Slave read/write           ``0x0000_0008``  Read/Write      ``0x0000_0000``
TX_FIFO_FULL      Tx FIFO full               ``0x0000_0010``  Read/Write      ``0x0000_0000``
RX_FIFO_FULL      Rx FIFO full               ``0x0000_0020``  Read/Write      ``0x0000_0000``
RX_FIFO_EMPTY     Rx FIFO empty              ``0x0000_0040``  Read/Write      ``0x0000_0000``
TX_FIFO_EMPTY     Tx FIFO empty              ``0x0000_0080``  Read/Write      ``0x0000_0000``
RSV_0             Reserved                   ``0xFFFF_FF00``  Read/Write      ``0x0000_0000``
================  =========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: AGBC [ rotate = 270 ]
      1: AAS [ rotate = 270 ]
      2: BB [ rotate = 270 ]
      3: SRW [ rotate = 270 ]
      4: TX_FIFO_FULL [ rotate = 270 ]
      5: RX_FIFO_FULL [ rotate = 270 ]
      6: RX_FIFO_EMPTY [ rotate = 270 ]
      7: TX_FIFO_EMPTY [ rotate = 270 ]
      8-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_TX_FIFO = { 'addr': 524552,
  'description': 'Tx FIFO',
  'fields': [ { 'description': 'Tx data',
                'is_bit': False,
                'mask': 255,
                'name': 'TX_DATA',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Start',
                'is_bit': True,
                'mask': 256,
                'name': 'START',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 8},
              { 'description': 'Stop',
                'is_bit': True,
                'mask': 512,
                'name': 'STOP',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 9},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294966272,
                'name': 'RSV_0',
                'nof_bits': 22,
                'reset_value': '0x0',
                'shiftr': 10}],
  'mask': 4294967295,
  'name': 'QSFP_1_TX_FIFO',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_TX_FIFO` generated from `XML2VHDL` output.

================  ===============  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_TX_FIFO
**Address:**      ``0x0008_0108``
**Description:**  Tx FIFO
**Bit Fields**    **Description**  **Mask**         **Permission**  **Reset Value**
TX_DATA           Tx data          ``0x0000_00FF``  Read/Write      ``0x0000_0000``
START             Start            ``0x0000_0100``  Read/Write      ``0x0000_0000``
STOP              Stop             ``0x0000_0200``  Read/Write      ``0x0000_0000``
RSV_0             Reserved         ``0xFFFF_FC00``  Read/Write      ``0x0000_0000``
================  ===============  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: TX_DATA
      8: START [ rotate = 270 ]
      9: STOP [ rotate = 270 ]
      10-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_RX_FIFO = { 'addr': 524556,
  'description': 'Rx FIFO',
  'fields': [ { 'description': 'Rx data',
                'is_bit': False,
                'mask': 255,
                'name': 'RX_DATA',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967040,
                'name': 'RSV_0',
                'nof_bits': 24,
                'reset_value': '0x0',
                'shiftr': 8}],
  'mask': 4294967295,
  'name': 'QSFP_1_RX_FIFO',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_RX_FIFO` generated from `XML2VHDL` output.

================  ===============  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_RX_FIFO
**Address:**      ``0x0008_010C``
**Description:**  Rx FIFO
**Bit Fields**    **Description**  **Mask**         **Permission**  **Reset Value**
RX_DATA           Rx data          ``0x0000_00FF``  Read/Write      ``0x0000_0000``
RSV_0             Reserved         ``0xFFFF_FF00``  Read/Write      ``0x0000_0000``
================  ===============  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: RX_DATA
      8-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_TX_FIFO_OCY = { 'addr': 524564,
  'description': 'Tx FIFO Occupancy Register',
  'fields': [ { 'description': 'Tx FIFO occupancy',
                'is_bit': False,
                'mask': 15,
                'name': 'TX_OCY',
                'nof_bits': 4,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967280,
                'name': 'RSV_0',
                'nof_bits': 28,
                'reset_value': '0x0',
                'shiftr': 4}],
  'mask': 4294967295,
  'name': 'QSFP_1_TX_FIFO_OCY',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_TX_FIFO_OCY` generated from `XML2VHDL` output.

================  ==========================  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_TX_FIFO_OCY
**Address:**      ``0x0008_0114``
**Description:**  Tx FIFO Occupancy Register
**Bit Fields**    **Description**             **Mask**         **Permission**  **Reset Value**
TX_OCY            Tx FIFO occupancy           ``0x0000_000F``  Read/Write      ``0x0000_0000``
RSV_0             Reserved                    ``0xFFFF_FFF0``  Read/Write      ``0x0000_0000``
================  ==========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-3: TX_OCY
      4-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_RX_FIFO_OCY = { 'addr': 524568,
  'description': 'Rx FIFO Occupancy Register',
  'fields': [ { 'description': 'Rx FIFO occupancy',
                'is_bit': False,
                'mask': 15,
                'name': 'RX_OCY',
                'nof_bits': 4,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967280,
                'name': 'RSV_0',
                'nof_bits': 28,
                'reset_value': '0x0',
                'shiftr': 4}],
  'mask': 4294967295,
  'name': 'QSFP_1_RX_FIFO_OCY',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_RX_FIFO_OCY` generated from `XML2VHDL` output.

================  ==========================  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_RX_FIFO_OCY
**Address:**      ``0x0008_0118``
**Description:**  Rx FIFO Occupancy Register
**Bit Fields**    **Description**             **Mask**         **Permission**  **Reset Value**
RX_OCY            Rx FIFO occupancy           ``0x0000_000F``  Read/Write      ``0x0000_0000``
RSV_0             Reserved                    ``0xFFFF_FFF0``  Read/Write      ``0x0000_0000``
================  ==========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-3: RX_OCY
      4-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_RX_FIFO_PIRQ = { 'addr': 524576,
  'description': 'Rx FIFO Programmable Depth Interrupt Register',
  'fields': [ { 'description': 'Compare value',
                'is_bit': False,
                'mask': 15,
                'name': 'COMP_VAL',
                'nof_bits': 4,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967280,
                'name': 'RSV_0',
                'nof_bits': 28,
                'reset_value': '0x0',
                'shiftr': 4}],
  'mask': 4294967295,
  'name': 'QSFP_1_RX_FIFO_PIRQ',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_RX_FIFO_PIRQ` generated from `XML2VHDL` output.

================  =============================================  ===============  ==============  ===============
**Register**
**Name:**         QSFP_1_RX_FIFO_PIRQ
**Address:**      ``0x0008_0120``
**Description:**  Rx FIFO Programmable Depth Interrupt Register
**Bit Fields**    **Description**                                **Mask**         **Permission**  **Reset Value**
COMP_VAL          Compare value                                  ``0x0000_000F``  Read/Write      ``0x0000_0000``
RSV_0             Reserved                                       ``0xFFFF_FFF0``  Read/Write      ``0x0000_0000``
================  =============================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-3: COMP_VAL
      4-31: RSV_0 [ color = lightgrey ]
   }

"""
