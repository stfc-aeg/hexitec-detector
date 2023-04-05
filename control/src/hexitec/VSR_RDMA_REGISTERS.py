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
