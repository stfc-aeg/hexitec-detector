# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.

# *** This file was AUTO-GENERATED. Modifications to this file will be overwritten. ***
"""IC ID and Register dictionaries extracted from XML2VHDL formatted `xml` memory-map generation output file."""
IC_OFFSETS = {'ic_ids': [{'addr_offset': 0, 'name': 'HEXITEC_2X6_ID'}]}
"""XML2VHDL IC References generated from `XML2VHDL` output.

==============  ===============
**ID**          **Offset
HEXITEC_2X6_ID  ``0x0000_0000``
==============  ===============
"""

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
