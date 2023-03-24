# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.

# *** This file was AUTO-GENERATED. Modifications to this file will be overwritten. ***
"""RDMA register dictionaries extracted from XML2VHDL memory-map generation."""
HEXITEC_2X6_PRODUCT_ID = { 'addr': 0,
  'description': 'aSpect product ID register',
  'fields': [ { 'description': 'coVersion',
                'is_bit': False,
                'mask': 255,
                'name': 'VERSION',
                'nof_bits': 8,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'coProduct',
                'is_bit': False,
                'mask': 1048320,
                'name': 'PRODUCT',
                'nof_bits': 12,
                'reset_value': '0x0',
                'shiftr': 8},
              { 'description': 'coCustomer',
                'is_bit': False,
                'mask': 4293918720,
                'name': 'CUSTOMER',
                'nof_bits': 12,
                'reset_value': '0x0',
                'shiftr': 20}],
  'mask': 4294967295,
  'name': 'HEXITEC_2X6_PRODUCT_ID',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`HEXITEC_2X6_PRODUCT_ID`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: VERSION
      8-19: PRODUCT
      20-31: CUSTOMER
   }

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
""":const:`HEXITEC_2X6_READBACK`.

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
      6-7: [ color = lightgrey ]
      8-11: FMC_QSFP1_LANE_UP
      12-15: FMC_QSFP2_LANE_UP
      16: SMB1_IN [ rotate = 270 ]
      17: SMB3_IN [ rotate = 270 ]
      18: SMB5_IN [ rotate = 270 ]
      19-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_CLK_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: CLK_EN [ rotate = 270 ]
      1: CLK_RST [ rotate = 270 ]
      2: [ color = lightgrey ]
      3: [ color = lightgrey ]
      4: [ color = lightgrey ]
      5: [ color = lightgrey ]
      6: [ color = lightgrey ]
      7: [ color = lightgrey ]
      8: [ color = lightgrey ]
      9: [ color = lightgrey ]
      10: [ color = lightgrey ]
      11: [ color = lightgrey ]
      12: [ color = lightgrey ]
      13: [ color = lightgrey ]
      14: [ color = lightgrey ]
      15: [ color = lightgrey ]
      16: [ color = lightgrey ]
      17: [ color = lightgrey ]
      18: [ color = lightgrey ]
      19: [ color = lightgrey ]
      20: [ color = lightgrey ]
      21: [ color = lightgrey ]
      22: [ color = lightgrey ]
      23: [ color = lightgrey ]
      24: [ color = lightgrey ]
      25: [ color = lightgrey ]
      26: [ color = lightgrey ]
      27: [ color = lightgrey ]
      28: [ color = lightgrey ]
      29: [ color = lightgrey ]
      30: [ color = lightgrey ]
      31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_UART_TX_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: TX_BUFF_RST [ rotate = 270 ]
      1: TX_FILL_STRB [ rotate = 270 ]
      2: TX_BUFF_STRB [ rotate = 270 ]
      3-7: [ color = lightgrey ]
      8-15: TX_DATA
      16-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_UART_STATUS`.

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
      5-7: [ color = lightgrey ]
      8-15: RX_BUFF_LEVEL
      16-23: RX_DATA
      24-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_UART_RX_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: RX_BUFF_RST [ rotate = 270 ]
      1: RX_BUFF_STRB [ rotate = 270 ]
      2: [ color = lightgrey ]
      3: [ color = lightgrey ]
      4: [ color = lightgrey ]
      5: [ color = lightgrey ]
      6: [ color = lightgrey ]
      7: [ color = lightgrey ]
      8: [ color = lightgrey ]
      9: [ color = lightgrey ]
      10: [ color = lightgrey ]
      11: [ color = lightgrey ]
      12: [ color = lightgrey ]
      13: [ color = lightgrey ]
      14: [ color = lightgrey ]
      15: [ color = lightgrey ]
      16: [ color = lightgrey ]
      17: [ color = lightgrey ]
      18: [ color = lightgrey ]
      19: [ color = lightgrey ]
      20: [ color = lightgrey ]
      21: [ color = lightgrey ]
      22: [ color = lightgrey ]
      23: [ color = lightgrey ]
      24: [ color = lightgrey ]
      25: [ color = lightgrey ]
      26: [ color = lightgrey ]
      27: [ color = lightgrey ]
      28: [ color = lightgrey ]
      29: [ color = lightgrey ]
      30: [ color = lightgrey ]
      31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_VSR_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: VSR_EN
      6-7: [ color = lightgrey ]
      8-13: HV_EN
      14-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_VSR_MODE_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: SM_EN [ rotate = 270 ]
      1: SYNCMODE_EN [ rotate = 270 ]
      2-11: [ color = lightgrey ]
      12: TRAINING_SEL [ rotate = 270 ]
      13: [ color = lightgrey ]
      14: [ color = lightgrey ]
      15: [ color = lightgrey ]
      16: [ color = lightgrey ]
      17: [ color = lightgrey ]
      18: [ color = lightgrey ]
      19: [ color = lightgrey ]
      20: [ color = lightgrey ]
      21: [ color = lightgrey ]
      22: [ color = lightgrey ]
      23: [ color = lightgrey ]
      24: [ color = lightgrey ]
      25: [ color = lightgrey ]
      26: [ color = lightgrey ]
      27: [ color = lightgrey ]
      28: [ color = lightgrey ]
      29: [ color = lightgrey ]
      30: [ color = lightgrey ]
      31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_VSR_DATA_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: DATA_EN [ rotate = 270 ]
      1-3: [ color = lightgrey ]
      4: TRAINING_EN [ rotate = 270 ]
      5-7: [ color = lightgrey ]
      8: SYNTH_DATA_EN [ rotate = 270 ]
      9-15: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_SMB_CFG`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-2: HEXITEC_2X6_SMB_CFG [ rotate = 270 ]
      3-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_TIG_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: TIG_RST [ rotate = 270 ]
      1: TIG_EN [ rotate = 270 ]
      2-7: [ color = lightgrey ]
      8-10: TIG_MODE [ rotate = 270 ]
      11-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_TIG_ROWS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-23: HEXITEC_2X6_TIG_ROWS
      24-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_TIG_COLS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-23: HEXITEC_2X6_TIG_COLS
      24-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_TIG_LBCLKS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-23: HEXITEC_2X6_TIG_LBCLKS
      24-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_TIG_FBCLKS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-23: HEXITEC_2X6_TIG_FBCLKS
      24-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_UDP_CORE_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: USE_EXT_ADDRS
      8-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_TEST_CTRL`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: UART_LOOPBACK_EN [ rotate = 270 ]
      1: [ color = lightgrey ]
      2: [ color = lightgrey ]
      3: [ color = lightgrey ]
      4: [ color = lightgrey ]
      5: [ color = lightgrey ]
      6: [ color = lightgrey ]
      7: [ color = lightgrey ]
      8: [ color = lightgrey ]
      9: [ color = lightgrey ]
      10: [ color = lightgrey ]
      11: [ color = lightgrey ]
      12: [ color = lightgrey ]
      13: [ color = lightgrey ]
      14: [ color = lightgrey ]
      15: [ color = lightgrey ]
      16: [ color = lightgrey ]
      17: [ color = lightgrey ]
      18: [ color = lightgrey ]
      19: [ color = lightgrey ]
      20: [ color = lightgrey ]
      21: [ color = lightgrey ]
      22: [ color = lightgrey ]
      23: [ color = lightgrey ]
      24: [ color = lightgrey ]
      25: [ color = lightgrey ]
      26: [ color = lightgrey ]
      27: [ color = lightgrey ]
      28: [ color = lightgrey ]
      29: [ color = lightgrey ]
      30: [ color = lightgrey ]
      31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_HEADER_CTRL`.

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
      4-29: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_HEADER_STATUS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-1: READOUT_LANE [ rotate = 270 ]
      2-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_FRAME_PRELOAD_LOWER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: HEXITEC_2X6_FRAME_PRELOAD_LOWER
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
""":const:`HEXITEC_2X6_FRAME_PRELOAD_UPPER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: HEXITEC_2X6_FRAME_PRELOAD_UPPER
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
""":const:`HEXITEC_2X6_PACKET_PRELOAD_LOWER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: HEXITEC_2X6_PACKET_PRELOAD_LOWER
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
""":const:`HEXITEC_2X6_PACKET_PRELOAD_UPPER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: HEXITEC_2X6_PACKET_PRELOAD_UPPER
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
""":const:`HEXITEC_2X6_FRAME_NUMBER_LOWER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: HEXITEC_2X6_FRAME_NUMBER_LOWER
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
""":const:`HEXITEC_2X6_FRAME_NUMBER_UPPER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: HEXITEC_2X6_FRAME_NUMBER_UPPER
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
""":const:`HEXITEC_2X6_PACKET_NUMBER_LOWER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: HEXITEC_2X6_PACKET_NUMBER_LOWER
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
""":const:`HEXITEC_2X6_PACKET_NUMBER_UPPER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: HEXITEC_2X6_PACKET_NUMBER_UPPER
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
""":const:`HEXITEC_2X6_VSR0_STATUS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_VSR1_STATUS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_VSR2_STATUS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_VSR3_STATUS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_VSR4_STATUS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31: [ color = lightgrey ]
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
""":const:`HEXITEC_2X6_VSR5_STATUS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: LOCKED
      8-31: [ color = lightgrey ]
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
""":const:`BOARD_BUILD_INFO_SRC_VERSION`.

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
""":const:`BOARD_BUILD_INFO_GIT_HASH`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_GIT_HASH
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
""":const:`BOARD_BUILD_INFO_BUILD_DATE`.

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
""":const:`BOARD_BUILD_INFO_BUILD_TIME`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: SECONDS
      8-15: MINUTE
      16-23: HOUR
      24-31: [ color = lightgrey ]
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
""":const:`BOARD_BUILD_INFO_DNA_0`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_DNA_0
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
""":const:`BOARD_BUILD_INFO_DNA_1`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_DNA_1
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
""":const:`BOARD_BUILD_INFO_DNA_2`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_DNA_2
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
""":const:`BOARD_BUILD_INFO_RSV_DNA_3`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_RSV_DNA_3
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
""":const:`BOARD_BUILD_INFO_DNA_STATUS`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: VALID [ rotate = 270 ]
      1: [ color = lightgrey ]
      2: [ color = lightgrey ]
      3: [ color = lightgrey ]
      4: [ color = lightgrey ]
      5: [ color = lightgrey ]
      6: [ color = lightgrey ]
      7: [ color = lightgrey ]
      8: [ color = lightgrey ]
      9: [ color = lightgrey ]
      10: [ color = lightgrey ]
      11: [ color = lightgrey ]
      12: [ color = lightgrey ]
      13: [ color = lightgrey ]
      14: [ color = lightgrey ]
      15: [ color = lightgrey ]
      16: [ color = lightgrey ]
      17: [ color = lightgrey ]
      18: [ color = lightgrey ]
      19: [ color = lightgrey ]
      20: [ color = lightgrey ]
      21: [ color = lightgrey ]
      22: [ color = lightgrey ]
      23: [ color = lightgrey ]
      24: [ color = lightgrey ]
      25: [ color = lightgrey ]
      26: [ color = lightgrey ]
      27: [ color = lightgrey ]
      28: [ color = lightgrey ]
      29: [ color = lightgrey ]
      30: [ color = lightgrey ]
      31: [ color = lightgrey ]
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
""":const:`BOARD_BUILD_INFO_SCRATCH_1`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_SCRATCH_1
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
""":const:`BOARD_BUILD_INFO_SCRATCH_2`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_SCRATCH_2
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
""":const:`BOARD_BUILD_INFO_SCRATCH_3`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_SCRATCH_3
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
""":const:`BOARD_BUILD_INFO_SCRATCH_4`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_SCRATCH_4
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_1 = { 'addr': 32832,
  'description': 'ACSII description field 1',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_1',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_1`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_1
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_2 = { 'addr': 32836,
  'description': 'ACSII description field 2',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_2',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_2`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_2
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_3 = { 'addr': 32840,
  'description': 'ACSII description field 3',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_3',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_3`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_3
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_4 = { 'addr': 32844,
  'description': 'ACSII description field 4',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_4',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_4`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_4
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_5 = { 'addr': 32848,
  'description': 'ACSII description field 5',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_5',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_5`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_5
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_6 = { 'addr': 32852,
  'description': 'ACSII description field 6',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_6',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_6`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_6
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_7 = { 'addr': 32856,
  'description': 'ACSII description field 7',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_7',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_7`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_7
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_8 = { 'addr': 32860,
  'description': 'ACSII description field 8',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_8',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_8`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_8
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_9 = { 'addr': 32864,
  'description': 'ACSII description field 9',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_9',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_9`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_9
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_10 = { 'addr': 32868,
  'description': 'ACSII description field 10',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_10',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_10`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_10
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_11 = { 'addr': 32872,
  'description': 'ACSII description field 11',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_11',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_11`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_11
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_12 = { 'addr': 32876,
  'description': 'ACSII description field 12',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_12',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_12`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_12
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_13 = { 'addr': 32880,
  'description': 'ACSII description field 13',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_13',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_13`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_13
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_14 = { 'addr': 32884,
  'description': 'ACSII description field 14',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_14',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_14`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_14
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_15 = { 'addr': 32888,
  'description': 'ACSII description field 15',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_15',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_15`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_15
   }

"""

BOARD_BUILD_INFO_ASCII_DESCR_16 = { 'addr': 32892,
  'description': 'ACSII description field 16',
  'fields': [],
  'mask': 4294967295,
  'name': 'BOARD_BUILD_INFO_ASCII_DESCR_16',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`BOARD_BUILD_INFO_ASCII_DESCR_16`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: BOARD_BUILD_INFO_ASCII_DESCR_16
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
""":const:`QSFP_1_GIE`.

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

QSFP_1_ISR = { 'addr': 524320,
  'description': 'Interrupt Status Register',
  'fields': [ { 'description': 'Arbitration lost',
                'is_bit': True,
                'mask': 1,
                'name': 'INT_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Tx error/slave Tx complete',
                'is_bit': True,
                'mask': 2,
                'name': 'INT_1',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Tx FIFO empty',
                'is_bit': True,
                'mask': 4,
                'name': 'INT_2',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Rx FIFO full',
                'is_bit': True,
                'mask': 8,
                'name': 'INT_3',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'IIC bus is not ready',
                'is_bit': True,
                'mask': 16,
                'name': 'INT_4',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Addressed as slave',
                'is_bit': True,
                'mask': 32,
                'name': 'INT_5',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'Not addressed as slave',
                'is_bit': True,
                'mask': 64,
                'name': 'INT_6',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'Tx FIFO half empty',
                'is_bit': True,
                'mask': 128,
                'name': 'INT_7',
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
  'name': 'QSFP_1_ISR',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_ISR`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: INT_0 [ rotate = 270 ]
      1: INT_1 [ rotate = 270 ]
      2: INT_2 [ rotate = 270 ]
      3: INT_3 [ rotate = 270 ]
      4: INT_4 [ rotate = 270 ]
      5: INT_5 [ rotate = 270 ]
      6: INT_6 [ rotate = 270 ]
      7: INT_7 [ rotate = 270 ]
      8-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_IER = { 'addr': 524328,
  'description': 'Interrupt Enable Register',
  'fields': [ { 'description': 'Arbitration lost',
                'is_bit': True,
                'mask': 1,
                'name': 'INT_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Tx error/slave Tx complete',
                'is_bit': True,
                'mask': 2,
                'name': 'INT_1',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Tx FIFO empty',
                'is_bit': True,
                'mask': 4,
                'name': 'INT_2',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Rx FIFO full',
                'is_bit': True,
                'mask': 8,
                'name': 'INT_3',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'IIC bus is not ready',
                'is_bit': True,
                'mask': 16,
                'name': 'INT_4',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Addressed as slave',
                'is_bit': True,
                'mask': 32,
                'name': 'INT_5',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'Not addressed as slave',
                'is_bit': True,
                'mask': 64,
                'name': 'INT_6',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'Tx FIFO half empty',
                'is_bit': True,
                'mask': 128,
                'name': 'INT_7',
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
  'name': 'QSFP_1_IER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_IER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: INT_0 [ rotate = 270 ]
      1: INT_1 [ rotate = 270 ]
      2: INT_2 [ rotate = 270 ]
      3: INT_3 [ rotate = 270 ]
      4: INT_4 [ rotate = 270 ]
      5: INT_5 [ rotate = 270 ]
      6: INT_6 [ rotate = 270 ]
      7: INT_7 [ rotate = 270 ]
      8-31: RSV_0 [ color = lightgrey ]
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
""":const:`QSFP_1_SOFTR`.

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
""":const:`QSFP_1_CTRL_REG`.

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
""":const:`QSFP_1_STAT_REG`.

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
""":const:`QSFP_1_TX_FIFO`.

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
""":const:`QSFP_1_RX_FIFO`.

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

QSFP_1_ADR = { 'addr': 524560,
  'description': 'Slave Address Register',
  'fields': [ { 'description': 'Reserved',
                'is_bit': True,
                'mask': 1,
                'name': 'RSV_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Slave address',
                'is_bit': False,
                'mask': 224,
                'name': 'SLAVE_ADDR',
                'nof_bits': 3,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967040,
                'name': 'RSV_1',
                'nof_bits': 24,
                'reset_value': '0x0',
                'shiftr': 8}],
  'mask': 4294967295,
  'name': 'QSFP_1_ADR',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_ADR`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: RSV_0 [ rotate = 270, color = lightgrey ]
      1-4: [ color = lightgrey ]
      5-7: SLAVE_ADDR [ rotate = 270 ]
      8-31: RSV_1 [ color = lightgrey ]
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
""":const:`QSFP_1_TX_FIFO_OCY`.

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
""":const:`QSFP_1_RX_FIFO_OCY`.

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

QSFP_1_TEN_ADR = { 'addr': 524572,
  'description': 'Slave 10-bit Address Register',
  'fields': [ { 'description': 'The MSBs pf the 10bit address when in slave '
                               'mode',
                'is_bit': False,
                'mask': 7,
                'name': 'MSB_SLAVE_ADDR',
                'nof_bits': 3,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967264,
                'name': 'RSV_0',
                'nof_bits': 27,
                'reset_value': '0x0',
                'shiftr': 5}],
  'mask': 4294967295,
  'name': 'QSFP_1_TEN_ADR',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_TEN_ADR`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-2: MSB_SLAVE_ADDR [ rotate = 270 ]
      3-4: [ color = lightgrey ]
      5-31: RSV_0 [ color = lightgrey ]
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
""":const:`QSFP_1_RX_FIFO_PIRQ`.

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

QSFP_1_GPO = { 'addr': 524580,
  'description': 'General Purpose Output Register',
  'fields': [ { 'description': 'General purpose output 0',
                'is_bit': True,
                'mask': 1,
                'name': 'GPO_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'General purpose output 1',
                'is_bit': True,
                'mask': 2,
                'name': 'GPO_1',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'General purpose output 2',
                'is_bit': True,
                'mask': 4,
                'name': 'GPO_2',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'General purpose output 3',
                'is_bit': True,
                'mask': 8,
                'name': 'GPO_3',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'General purpose output 4',
                'is_bit': True,
                'mask': 16,
                'name': 'GPO_4',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'General purpose output 5',
                'is_bit': True,
                'mask': 32,
                'name': 'GPO_5',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'General purpose output 6',
                'is_bit': True,
                'mask': 64,
                'name': 'GPO_6',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'General purpose output 7',
                'is_bit': True,
                'mask': 128,
                'name': 'GPO_7',
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
  'name': 'QSFP_1_GPO',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_GPO`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: GPO_0 [ rotate = 270 ]
      1: GPO_1 [ rotate = 270 ]
      2: GPO_2 [ rotate = 270 ]
      3: GPO_3 [ rotate = 270 ]
      4: GPO_4 [ rotate = 270 ]
      5: GPO_5 [ rotate = 270 ]
      6: GPO_6 [ rotate = 270 ]
      7: GPO_7 [ rotate = 270 ]
      8-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_1_TSUSTA = { 'addr': 524584,
  'description': 'TSUSTA Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_1_TSUSTA',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_TSUSTA`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_1_TSUSTA
   }

"""

QSFP_1_TSUSTO = { 'addr': 524588,
  'description': 'TSUSTO Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_1_TSUSTO',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_TSUSTO`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_1_TSUSTO
   }

"""

QSFP_1_THDSTA = { 'addr': 524592,
  'description': 'THDSTA Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_1_THDSTA',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_THDSTA`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_1_THDSTA
   }

"""

QSFP_1_TSUDAT = { 'addr': 524596,
  'description': 'TSUDAT Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_1_TSUDAT',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_TSUDAT`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_1_TSUDAT
   }

"""

QSFP_1_TBUF = { 'addr': 524600,
  'description': 'TBUF Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_1_TBUF',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_TBUF`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_1_TBUF
   }

"""

QSFP_1_THIGH = { 'addr': 524604,
  'description': 'THIGH Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_1_THIGH',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_THIGH`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_1_THIGH
   }

"""

QSFP_1_TLOW = { 'addr': 524608,
  'description': 'TLOW Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_1_TLOW',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_TLOW`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_1_TLOW
   }

"""

QSFP_1_THDDAT = { 'addr': 524612,
  'description': 'THDDAT Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_1_THDDAT',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_1_THDDAT`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_1_THDDAT
   }

"""

QSFP_2_GIE = { 'addr': 528412,
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
  'name': 'QSFP_2_GIE',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_GIE`.

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

QSFP_2_ISR = { 'addr': 528416,
  'description': 'Interrupt Status Register',
  'fields': [ { 'description': 'Arbitration lost',
                'is_bit': True,
                'mask': 1,
                'name': 'INT_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Tx error/slave Tx complete',
                'is_bit': True,
                'mask': 2,
                'name': 'INT_1',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Tx FIFO empty',
                'is_bit': True,
                'mask': 4,
                'name': 'INT_2',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Rx FIFO full',
                'is_bit': True,
                'mask': 8,
                'name': 'INT_3',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'IIC bus is not ready',
                'is_bit': True,
                'mask': 16,
                'name': 'INT_4',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Addressed as slave',
                'is_bit': True,
                'mask': 32,
                'name': 'INT_5',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'Not addressed as slave',
                'is_bit': True,
                'mask': 64,
                'name': 'INT_6',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'Tx FIFO half empty',
                'is_bit': True,
                'mask': 128,
                'name': 'INT_7',
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
  'name': 'QSFP_2_ISR',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_ISR`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: INT_0 [ rotate = 270 ]
      1: INT_1 [ rotate = 270 ]
      2: INT_2 [ rotate = 270 ]
      3: INT_3 [ rotate = 270 ]
      4: INT_4 [ rotate = 270 ]
      5: INT_5 [ rotate = 270 ]
      6: INT_6 [ rotate = 270 ]
      7: INT_7 [ rotate = 270 ]
      8-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_2_IER = { 'addr': 528424,
  'description': 'Interrupt Enable Register',
  'fields': [ { 'description': 'Arbitration lost',
                'is_bit': True,
                'mask': 1,
                'name': 'INT_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Tx error/slave Tx complete',
                'is_bit': True,
                'mask': 2,
                'name': 'INT_1',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Tx FIFO empty',
                'is_bit': True,
                'mask': 4,
                'name': 'INT_2',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Rx FIFO full',
                'is_bit': True,
                'mask': 8,
                'name': 'INT_3',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'IIC bus is not ready',
                'is_bit': True,
                'mask': 16,
                'name': 'INT_4',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Addressed as slave',
                'is_bit': True,
                'mask': 32,
                'name': 'INT_5',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'Not addressed as slave',
                'is_bit': True,
                'mask': 64,
                'name': 'INT_6',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'Tx FIFO half empty',
                'is_bit': True,
                'mask': 128,
                'name': 'INT_7',
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
  'name': 'QSFP_2_IER',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_IER`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: INT_0 [ rotate = 270 ]
      1: INT_1 [ rotate = 270 ]
      2: INT_2 [ rotate = 270 ]
      3: INT_3 [ rotate = 270 ]
      4: INT_4 [ rotate = 270 ]
      5: INT_5 [ rotate = 270 ]
      6: INT_6 [ rotate = 270 ]
      7: INT_7 [ rotate = 270 ]
      8-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_2_SOFTR = { 'addr': 528448,
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
  'name': 'QSFP_2_SOFTR',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_SOFTR`.

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

QSFP_2_CTRL_REG = { 'addr': 528640,
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
  'name': 'QSFP_2_CTRL_REG',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_CTRL_REG`.

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

QSFP_2_STAT_REG = { 'addr': 528644,
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
  'name': 'QSFP_2_STAT_REG',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_STAT_REG`.

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

QSFP_2_TX_FIFO = { 'addr': 528648,
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
  'name': 'QSFP_2_TX_FIFO',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_TX_FIFO`.

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

QSFP_2_RX_FIFO = { 'addr': 528652,
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
  'name': 'QSFP_2_RX_FIFO',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_RX_FIFO`.

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

QSFP_2_ADR = { 'addr': 528656,
  'description': 'Slave Address Register',
  'fields': [ { 'description': 'Reserved',
                'is_bit': True,
                'mask': 1,
                'name': 'RSV_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Slave address',
                'is_bit': False,
                'mask': 224,
                'name': 'SLAVE_ADDR',
                'nof_bits': 3,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967040,
                'name': 'RSV_1',
                'nof_bits': 24,
                'reset_value': '0x0',
                'shiftr': 8}],
  'mask': 4294967295,
  'name': 'QSFP_2_ADR',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_ADR`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: RSV_0 [ rotate = 270, color = lightgrey ]
      1-4: [ color = lightgrey ]
      5-7: SLAVE_ADDR [ rotate = 270 ]
      8-31: RSV_1 [ color = lightgrey ]
   }

"""

QSFP_2_TX_FIFO_OCY = { 'addr': 528660,
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
  'name': 'QSFP_2_TX_FIFO_OCY',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_TX_FIFO_OCY`.

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

QSFP_2_RX_FIFO_OCY = { 'addr': 528664,
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
  'name': 'QSFP_2_RX_FIFO_OCY',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_RX_FIFO_OCY`.

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

QSFP_2_TEN_ADR = { 'addr': 528668,
  'description': 'Slave 10-bit Address Register',
  'fields': [ { 'description': 'The MSBs pf the 10bit address when in slave '
                               'mode',
                'is_bit': False,
                'mask': 7,
                'name': 'MSB_SLAVE_ADDR',
                'nof_bits': 3,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Reserved',
                'is_bit': False,
                'mask': 4294967264,
                'name': 'RSV_0',
                'nof_bits': 27,
                'reset_value': '0x0',
                'shiftr': 5}],
  'mask': 4294967295,
  'name': 'QSFP_2_TEN_ADR',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_TEN_ADR`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-2: MSB_SLAVE_ADDR [ rotate = 270 ]
      3-4: [ color = lightgrey ]
      5-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_2_RX_FIFO_PIRQ = { 'addr': 528672,
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
  'name': 'QSFP_2_RX_FIFO_PIRQ',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_RX_FIFO_PIRQ`.

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

QSFP_2_GPO = { 'addr': 528676,
  'description': 'General Purpose Output Register',
  'fields': [ { 'description': 'General purpose output 0',
                'is_bit': True,
                'mask': 1,
                'name': 'GPO_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'General purpose output 1',
                'is_bit': True,
                'mask': 2,
                'name': 'GPO_1',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'General purpose output 2',
                'is_bit': True,
                'mask': 4,
                'name': 'GPO_2',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'General purpose output 3',
                'is_bit': True,
                'mask': 8,
                'name': 'GPO_3',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'General purpose output 4',
                'is_bit': True,
                'mask': 16,
                'name': 'GPO_4',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'General purpose output 5',
                'is_bit': True,
                'mask': 32,
                'name': 'GPO_5',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': 'General purpose output 6',
                'is_bit': True,
                'mask': 64,
                'name': 'GPO_6',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'General purpose output 7',
                'is_bit': True,
                'mask': 128,
                'name': 'GPO_7',
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
  'name': 'QSFP_2_GPO',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_GPO`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: GPO_0 [ rotate = 270 ]
      1: GPO_1 [ rotate = 270 ]
      2: GPO_2 [ rotate = 270 ]
      3: GPO_3 [ rotate = 270 ]
      4: GPO_4 [ rotate = 270 ]
      5: GPO_5 [ rotate = 270 ]
      6: GPO_6 [ rotate = 270 ]
      7: GPO_7 [ rotate = 270 ]
      8-31: RSV_0 [ color = lightgrey ]
   }

"""

QSFP_2_TSUSTA = { 'addr': 528680,
  'description': 'TSUSTA Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_2_TSUSTA',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_TSUSTA`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_2_TSUSTA
   }

"""

QSFP_2_TSUSTO = { 'addr': 528684,
  'description': 'TSUSTO Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_2_TSUSTO',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_TSUSTO`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_2_TSUSTO
   }

"""

QSFP_2_THDSTA = { 'addr': 528688,
  'description': 'THDSTA Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_2_THDSTA',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_THDSTA`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_2_THDSTA
   }

"""

QSFP_2_TSUDAT = { 'addr': 528692,
  'description': 'TSUDAT Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_2_TSUDAT',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_TSUDAT`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_2_TSUDAT
   }

"""

QSFP_2_TBUF = { 'addr': 528696,
  'description': 'TBUF Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_2_TBUF',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_TBUF`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_2_TBUF
   }

"""

QSFP_2_THIGH = { 'addr': 528700,
  'description': 'THIGH Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_2_THIGH',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_THIGH`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_2_THIGH
   }

"""

QSFP_2_TLOW = { 'addr': 528704,
  'description': 'TLOW Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_2_TLOW',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_TLOW`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_2_TLOW
   }

"""

QSFP_2_THDDAT = { 'addr': 528708,
  'description': 'THDDAT Timing Parameter Register',
  'fields': [],
  'mask': 4294967295,
  'name': 'QSFP_2_THDDAT',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`QSFP_2_THDDAT`.

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: QSFP_2_THDDAT
   }

"""
