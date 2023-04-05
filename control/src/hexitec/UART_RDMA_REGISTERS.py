# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.

# *** This file was AUTO-GENERATED. Modifications to this file will be overwritten. ***
"""IC ID and Register dictionaries extracted from XML2VHDL formatted `xml` memory-map generation output file."""
HEXITEC_2X6_ID = {'addr_offset': 0, 'fields': [], 'name': 'HEXITEC_2X6_ID'}
"""XML2VHDL IC References generated from `XML2VHDL` output.

==============  ===============
**ID**          **Offset
HEXITEC_2X6_ID  ``0x0000_0000``
==============  ===============
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
