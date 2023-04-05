# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.

# *** This file was AUTO-GENERATED. Modifications to this file will be overwritten. ***
"""IC ID and Register dictionaries extracted from XML2VHDL formatted `xml` memory-map generation output file."""
VSR_FPGA_REGS_V0_5_ID = {'addr_offset': 0, 'fields': [], 'name': 'VSR_FPGA_REGS_V0_5_ID'}
"""XML2VHDL IC References generated from `XML2VHDL` output.

=====================  ===============
**ID**                 **Offset
VSR_FPGA_REGS_V0_5_ID  ``0x0000_0000``
=====================  ===============
"""

REG1 = { 'addr': 1,
  'description': 'VSR module control',
  'fields': [ { 'description': 'Enable State-Machine',
                'is_bit': True,
                'mask': 1,
                'name': 'SM_EN',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 0},
              { 'description': 'Outputs tri-state',
                'is_bit': True,
                'mask': 2,
                'name': 'OUTPUTS_TRI',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': "Video data: '0' Spectr | '1' = counting mode",
                'is_bit': True,
                'mask': 4,
                'name': 'DATA_MODE',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': "Output mode: '0' DATALINE[3] = DATA[3], "
                               "DATALINE[5] = output_clk | '1' DATALINE[3] = "
                               'output_clk, DATALINE[5] = DATA[3]',
                'is_bit': True,
                'mask': 8,
                'name': 'OUTPUT_MODE',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'Use sync clock from DAQ board',
                'is_bit': True,
                'mask': 16,
                'name': 'SYNC_CLK_SEL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Reset serial interface to DAQ board',
                'is_bit': True,
                'mask': 32,
                'name': 'SERIAL_IFACE_RST',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5},
              { 'description': "Use own serial training pattern: '0' "
                               "100000000000000 | '1' from Reg255 and Reg254",
                'is_bit': True,
                'mask': 64,
                'name': 'TRAINING_PATTERN_SEL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'Enable serial training pattern',
                'is_bit': True,
                'mask': 128,
                'name': 'TRAINING_PATTERN_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 7}],
  'mask': 4294967295,
  'name': 'REG1',
  'nof_bits': 32,
  'reset_value': '0x01',
  'shiftr': 0}
""":const:`REG1` generated from `XML2VHDL` output.

====================  ======================================================================================================================  ===============  ==============  ===============
**Register**
**Name:**             REG1
**Address:**          ``0x0000_0001``
**Description:**      VSR module control
**Bit Fields**        **Description**                                                                                                         **Mask**         **Permission**  **Reset Value**
SM_EN                 Enable State-Machine                                                                                                    ``0x0000_0001``  Read/Write      ``0x0000_0001``
OUTPUTS_TRI           Outputs tri-state                                                                                                       ``0x0000_0002``  Read/Write      ``0x0000_0000``
DATA_MODE             Video data: '0' Spectr | '1' = counting mode                                                                            ``0x0000_0004``  Read/Write      ``0x0000_0000``
OUTPUT_MODE           Output mode: '0' DATALINE[3] = DATA[3], DATALINE[5] = output_clk | '1' DATALINE[3] = output_clk, DATALINE[5] = DATA[3]  ``0x0000_0008``  Read/Write      ``0x0000_0000``
SYNC_CLK_SEL          Use sync clock from DAQ board                                                                                           ``0x0000_0010``  Read/Write      ``0x0000_0000``
SERIAL_IFACE_RST      Reset serial interface to DAQ board                                                                                     ``0x0000_0020``  Read/Write      ``0x0000_0000``
TRAINING_PATTERN_SEL  Use own serial training pattern: '0' 100000000000000 | '1' from Reg255 and Reg254                                       ``0x0000_0040``  Read/Write      ``0x0000_0000``
TRAINING_PATTERN_EN   Enable serial training pattern                                                                                          ``0x0000_0080``  Read/Write      ``0x0000_0000``
====================  ======================================================================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: SM_EN [ rotate = 270 ]
      1: OUTPUTS_TRI [ rotate = 270 ]
      2: DATA_MODE [ rotate = 270 ]
      3: OUTPUT_MODE [ rotate = 270 ]
      4: SYNC_CLK_SEL [ rotate = 270 ]
      5: SERIAL_IFACE_RST [ rotate = 270 ]
      6: TRAINING_PATTERN_SEL [ rotate = 270 ]
      7: TRAINING_PATTERN_EN [ rotate = 270 ]
      8-31:  [ color = lightgrey ]
   }

"""

REG2 = { 'addr': 2,
  'description': 'RowS1 Low Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG2',
  'nof_bits': 8,
  'reset_value': '0x01',
  'shiftr': 0}
""":const:`REG2` generated from `XML2VHDL` output.

================  ===============
**Register**
**Name:**         REG2
**Address:**      ``0x0000_0002``
**Description:**  RowS1 Low Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0001``
================  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG2
      8-31:  [ color = lightgrey ]
   }

"""

REG3 = { 'addr': 3,
  'description': 'RowS1 High Byte',
  'fields': [],
  'mask': 63,
  'name': 'REG3',
  'nof_bits': 6,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG3` generated from `XML2VHDL` output.

================  ===============
**Register**
**Name:**         REG3
**Address:**      ``0x0000_0003``
**Description:**  RowS1 High Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: REG3
      6-31:  [ color = lightgrey ]
   }

"""

REG4 = { 'addr': 4,
  'description': 'S1Sph',
  'fields': [],
  'mask': 63,
  'name': 'REG4',
  'nof_bits': 6,
  'reset_value': '0x01',
  'shiftr': 0}
""":const:`REG4` generated from `XML2VHDL` output.

================  ===============
**Register**
**Name:**         REG4
**Address:**      ``0x0000_0004``
**Description:**  S1Sph
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0001``
================  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: REG4
      6-31:  [ color = lightgrey ]
   }

"""

REG5 = { 'addr': 5,
  'description': 'SphS2',
  'fields': [],
  'mask': 63,
  'name': 'REG5',
  'nof_bits': 6,
  'reset_value': '0x06',
  'shiftr': 0}
""":const:`REG5` generated from `XML2VHDL` output.

================  ===============
**Register**
**Name:**         REG5
**Address:**      ``0x0000_0005``
**Description:**  SphS2
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0006``
================  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: REG5
      6-31:  [ color = lightgrey ]
   }

"""

REG6 = { 'addr': 6,
  'description': 'Gain control',
  'fields': [ { 'description': "Gain select: '0' High gain | '1' Low gain",
                'is_bit': True,
                'mask': 1,
                'name': 'GAIN_SEL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 1,
  'name': 'REG6',
  'nof_bits': 1,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG6` generated from `XML2VHDL` output.

================  =========================================  ===============  ==============  ===============
**Register**
**Name:**         REG6
**Address:**      ``0x0000_0006``
**Description:**  Gain control
**Bit Fields**    **Description**                            **Mask**         **Permission**  **Reset Value**
GAIN_SEL          Gain select: '0' High gain | '1' Low gain  ``0x0000_0001``  Read/Write      ``0x0000_0000``
================  =========================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: GAIN_SEL [ rotate = 270 ]
      1-31:  [ color = lightgrey ]
   }

"""

REG7 = { 'addr': 7,
  'description': 'PLL control',
  'fields': [ { 'description': 'Enable PLL',
                'is_bit': True,
                'mask': 1,
                'name': 'ENABLE_PLL',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 0},
              { 'description': 'Enable ADC PLL',
                'is_bit': True,
                'mask': 2,
                'name': 'ENABLE_ADC_PLL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1}],
  'mask': 3,
  'name': 'REG7',
  'nof_bits': 2,
  'reset_value': '0x01',
  'shiftr': 0}
""":const:`REG7` generated from `XML2VHDL` output.

================  ===============  ===============  ==============  ===============
**Register**
**Name:**         REG7
**Address:**      ``0x0000_0007``
**Description:**  PLL control
**Bit Fields**    **Description**  **Mask**         **Permission**  **Reset Value**
ENABLE_PLL        Enable PLL       ``0x0000_0001``  Read/Write      ``0x0000_0001``
ENABLE_ADC_PLL    Enable ADC PLL   ``0x0000_0002``  Read/Write      ``0x0000_0000``
================  ===============  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: ENABLE_PLL [ rotate = 270 ]
      1: ENABLE_ADC_PLL [ rotate = 270 ]
      2-31:  [ color = lightgrey ]
   }

"""

REG8 = { 'addr': 8,
  'description': 'No description in documentation',
  'fields': [],
  'mask': 1,
  'name': 'REG8',
  'nof_bits': 1,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG8` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG8
**Address:**      ``0x0000_0008``
**Description:**  No description in documentation
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: REG8 [ rotate = 270 ]
      1-31:  [ color = lightgrey ]
   }

"""

REG9 = { 'addr': 9,
  'description': 'ADC clock delay',
  'fields': [],
  'mask': 31,
  'name': 'REG9',
  'nof_bits': 5,
  'reset_value': '0x02',
  'shiftr': 0}
""":const:`REG9` generated from `XML2VHDL` output.

================  ===============
**Register**
**Name:**         REG9
**Address:**      ``0x0000_0009``
**Description:**  ADC clock delay
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0002``
================  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-4: REG9
      5-31:  [ color = lightgrey ]
   }

"""

REG10 = { 'addr': 10,
  'description': 'Trigger control',
  'fields': [ { 'description': 'Enable synchronised State-Machine start via '
                               'Trigger[1]',
                'is_bit': True,
                'mask': 1,
                'name': 'TRIGGER_START_SM',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 0},
              { 'description': 'Enable trigger mode Trigger [2] and [3]',
                'is_bit': True,
                'mask': 2,
                'name': 'TRIGGER_MODE_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Enable trigger input [2] and [3]',
                'is_bit': True,
                'mask': 4,
                'name': 'TRIGGER_INPUT_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'No description in documentation',
                'is_bit': False,
                'mask': 120,
                'name': 'RSV_0',
                'nof_bits': 4,
                'reset_value': '0x0',
                'shiftr': 3}],
  'mask': 255,
  'name': 'REG10',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG10` generated from `XML2VHDL` output.

================  ======================================================  ===============  ==============  ===============
**Register**
**Name:**         REG10
**Address:**      ``0x0000_000A``
**Description:**  Trigger control
**Bit Fields**    **Description**                                         **Mask**         **Permission**  **Reset Value**
TRIGGER_START_SM  Enable synchronised State-Machine start via Trigger[1]  ``0x0000_0001``  Read/Write      ``0x0000_0001``
TRIGGER_MODE_EN   Enable trigger mode Trigger [2] and [3]                 ``0x0000_0002``  Read/Write      ``0x0000_0000``
TRIGGER_INPUT_EN  Enable trigger input [2] and [3]                        ``0x0000_0004``  Read/Write      ``0x0000_0000``
RSV_0             No description in documentation                         ``0x0000_0078``  Read/Write      ``0x0000_0000``
================  ======================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: TRIGGER_START_SM [ rotate = 270 ]
      1: TRIGGER_MODE_EN [ rotate = 270 ]
      2: TRIGGER_INPUT_EN [ rotate = 270 ]
      3-6: RSV_0 [ color = lightgrey ]
      7-31:  [ color = lightgrey ]
   }

"""

REG11 = { 'addr': 11,
  'description': 'No description in documentation',
  'fields': [],
  'mask': 255,
  'name': 'REG11',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG11` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG11
**Address:**      ``0x0000_000B``
**Description:**  No description in documentation
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG11
      8-31:  [ color = lightgrey ]
   }

"""

REG12 = { 'addr': 12,
  'description': 'No description in documentation',
  'fields': [],
  'mask': 255,
  'name': 'REG12',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG12` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG12
**Address:**      ``0x0000_000C``
**Description:**  No description in documentation
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG12
      8-31:  [ color = lightgrey ]
   }

"""

REG13 = { 'addr': 13,
  'description': 'No description in documentation',
  'fields': [],
  'mask': 255,
  'name': 'REG13',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG13` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG13
**Address:**      ``0x0000_000D``
**Description:**  No description in documentation
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG13
      8-31:  [ color = lightgrey ]
   }

"""

REG14 = { 'addr': 14,
  'description': 'ADC Fval/Lval signal delay',
  'fields': [],
  'mask': 255,
  'name': 'REG14',
  'nof_bits': 8,
  'reset_value': '0x0A',
  'shiftr': 0}
""":const:`REG14` generated from `XML2VHDL` output.

================  ==========================
**Register**
**Name:**         REG14
**Address:**      ``0x0000_000E``
**Description:**  ADC Fval/Lval signal delay
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_000A``
================  ==========================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG14
      8-31:  [ color = lightgrey ]
   }

"""

REG20 = { 'addr': 20,
  'description': 'State-Machine start control',
  'fields': [ { 'description': "'0' Start State-Machine on rising edge of ADC "
                               "clock | '1' Start State-Machine on falling "
                               'edge of ADC clock',
                'is_bit': True,
                'mask': 1,
                'name': 'SM_START_EDGE',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 0}],
  'mask': 1,
  'name': 'REG20',
  'nof_bits': 1,
  'reset_value': '0x1',
  'shiftr': 0}
""":const:`REG20` generated from `XML2VHDL` output.

================  ==========================================================================================================  ===============  ==============  ===============
**Register**
**Name:**         REG20
**Address:**      ``0x0000_0014``
**Description:**  State-Machine start control
**Bit Fields**    **Description**                                                                                             **Mask**         **Permission**  **Reset Value**
SM_START_EDGE     '0' Start State-Machine on rising edge of ADC clock | '1' Start State-Machine on falling edge of ADC clock  ``0x0000_0001``  Read/Write      ``0x0000_0001``
================  ==========================================================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: SM_START_EDGE [ rotate = 270 ]
      1-31:  [ color = lightgrey ]
   }

"""

REG24 = { 'addr': 24,
  'description': 'State-Machine Vcal clock Low Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG24',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG24` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG24
**Address:**      ``0x0000_0018``
**Description:**  State-Machine Vcal clock Low Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG24
      8-31:  [ color = lightgrey ]
   }

"""

REG25 = { 'addr': 25,
  'description': 'State-Machine Vcal clock High Byte',
  'fields': [],
  'mask': 127,
  'name': 'REG25',
  'nof_bits': 7,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG25` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG25
**Address:**      ``0x0000_0019``
**Description:**  State-Machine Vcal clock High Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-6: REG25
      7-31:  [ color = lightgrey ]
   }

"""

REG26 = { 'addr': 26,
  'description': 'State-Machine Column wait clock',
  'fields': [],
  'mask': 255,
  'name': 'REG26',
  'nof_bits': 8,
  'reset_value': '0x1',
  'shiftr': 0}
""":const:`REG26` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG26
**Address:**      ``0x0000_001A``
**Description:**  State-Machine Column wait clock
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0001``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG26
      8-31:  [ color = lightgrey ]
   }

"""

REG27 = { 'addr': 27,
  'description': 'State-Machine Row wait clock',
  'fields': [],
  'mask': 255,
  'name': 'REG27',
  'nof_bits': 8,
  'reset_value': '0x8',
  'shiftr': 0}
""":const:`REG27` generated from `XML2VHDL` output.

================  ============================
**Register**
**Name:**         REG27
**Address:**      ``0x0000_001B``
**Description:**  State-Machine Row wait clock
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0008``
================  ============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG27
      8-31:  [ color = lightgrey ]
   }

"""

REG31 = { 'addr': 31,
  'description': 'Read back register',
  'fields': [],
  'mask': 255,
  'name': 'REG31',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG31` generated from `XML2VHDL` output.

================  ==================
**Register**
**Name:**         REG31
**Address:**      ``0x0000_001F``
**Description:**  Read back register
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ==================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG31
      8-31:  [ color = lightgrey ]
   }

"""

REG32 = { 'addr': 32,
  'description': 'State-Machine X clock Vcal Low Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG32',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG32` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         REG32
**Address:**      ``0x0000_0020``
**Description:**  State-Machine X clock Vcal Low Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG32
      8-31:  [ color = lightgrey ]
   }

"""

REG33 = { 'addr': 33,
  'description': 'State-Machine X clock Vcal High Byte',
  'fields': [],
  'mask': 63,
  'name': 'REG33',
  'nof_bits': 6,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG33` generated from `XML2VHDL` output.

================  ====================================
**Register**
**Name:**         REG33
**Address:**      ``0x0000_0021``
**Description:**  State-Machine X clock Vcal High Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ====================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: REG33
      6-31:  [ color = lightgrey ]
   }

"""

REG34 = { 'addr': 34,
  'description': 'State-Machine Y clock Vcal Low Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG34',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG34` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         REG34
**Address:**      ``0x0000_0022``
**Description:**  State-Machine Y clock Vcal Low Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG34
      8-31:  [ color = lightgrey ]
   }

"""

REG35 = { 'addr': 35,
  'description': 'State-Machine Y clock Vcal Low Byte',
  'fields': [],
  'mask': 63,
  'name': 'REG35',
  'nof_bits': 6,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG35` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         REG35
**Address:**      ``0x0000_0023``
**Description:**  State-Machine Y clock Vcal Low Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: REG35
      6-31:  [ color = lightgrey ]
   }

"""

REG36 = { 'addr': 36,
  'description': 'DC control',
  'fields': [ { 'description': 'Overwrite the average picture',
                'is_bit': True,
                'mask': 1,
                'name': 'OVERWRITE_AVG_PICT',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Capture the average picture',
                'is_bit': True,
                'mask': 2,
                'name': 'CAPT_AVG_PICT',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Enable DC counting mode',
                'is_bit': True,
                'mask': 4,
                'name': 'COUNTING_MODE_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Enable DC spectroscopic mode',
                'is_bit': True,
                'mask': 8,
                'name': 'SPECTROSCOPIC_MODE_EN',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 3},
              { 'description': 'Send the average picture',
                'is_bit': True,
                'mask': 16,
                'name': 'SEND_ACG_PICT',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Disable the Vcal pulse',
                'is_bit': True,
                'mask': 32,
                'name': 'VCAL_PULSE_DISABLE',
                'nof_bits': 1,
                'reset_value': '0x1',
                'shiftr': 5},
              { 'description': 'Enable Test Mode',
                'is_bit': True,
                'mask': 64,
                'name': 'TEST_MODE_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 6},
              { 'description': 'Enable triggered frame in DC counting mode',
                'is_bit': True,
                'mask': 128,
                'name': 'TRIGGERED_FRAME_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 7}],
  'mask': 4294967295,
  'name': 'REG36',
  'nof_bits': 32,
  'reset_value': '0x28',
  'shiftr': 0}
""":const:`REG36` generated from `XML2VHDL` output.

=====================  ==========================================  ===============  ==============  ===============
**Register**
**Name:**              REG36
**Address:**           ``0x0000_0024``
**Description:**       DC control
**Bit Fields**         **Description**                             **Mask**         **Permission**  **Reset Value**
OVERWRITE_AVG_PICT     Overwrite the average picture               ``0x0000_0001``  Read/Write      ``0x0000_0000``
CAPT_AVG_PICT          Capture the average picture                 ``0x0000_0002``  Read/Write      ``0x0000_0000``
COUNTING_MODE_EN       Enable DC counting mode                     ``0x0000_0004``  Read/Write      ``0x0000_0000``
SPECTROSCOPIC_MODE_EN  Enable DC spectroscopic mode                ``0x0000_0008``  Read/Write      ``0x0000_0001``
SEND_ACG_PICT          Send the average picture                    ``0x0000_0010``  Read/Write      ``0x0000_0000``
VCAL_PULSE_DISABLE     Disable the Vcal pulse                      ``0x0000_0020``  Read/Write      ``0x0000_0001``
TEST_MODE_EN           Enable Test Mode                            ``0x0000_0040``  Read/Write      ``0x0000_0000``
TRIGGERED_FRAME_EN     Enable triggered frame in DC counting mode  ``0x0000_0080``  Read/Write      ``0x0000_0000``
=====================  ==========================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: OVERWRITE_AVG_PICT [ rotate = 270 ]
      1: CAPT_AVG_PICT [ rotate = 270 ]
      2: COUNTING_MODE_EN [ rotate = 270 ]
      3: SPECTROSCOPIC_MODE_EN [ rotate = 270 ]
      4: SEND_ACG_PICT [ rotate = 270 ]
      5: VCAL_PULSE_DISABLE [ rotate = 270 ]
      6: TEST_MODE_EN [ rotate = 270 ]
      7: TRIGGERED_FRAME_EN [ rotate = 270 ]
      8-31:  [ color = lightgrey ]
   }

"""

REG37 = { 'addr': 37,
  'description': 'DC/ED memory input data Low Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG37',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG37` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG37
**Address:**      ``0x0000_0025``
**Description:**  DC/ED memory input data Low Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG37
      8-31:  [ color = lightgrey ]
   }

"""

REG38 = { 'addr': 38,
  'description': 'DC/ED memory input data High Byte',
  'fields': [],
  'mask': 63,
  'name': 'REG38',
  'nof_bits': 6,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG38` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG38
**Address:**      ``0x0000_0026``
**Description:**  DC/ED memory input data High Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: REG38
      6-31:  [ color = lightgrey ]
   }

"""

REG39 = { 'addr': 39,
  'description': 'ED control',
  'fields': [ { 'description': 'Overwrite threshold values',
                'is_bit': True,
                'mask': 1,
                'name': 'OVERWRITE_THRS',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Disable counting mode',
                'is_bit': True,
                'mask': 2,
                'name': 'COUNTING_MODE_DISABLE',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Enable test mode',
                'is_bit': True,
                'mask': 4,
                'name': 'TEST_MODE_EN',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2}],
  'mask': 4294967295,
  'name': 'REG39',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG39` generated from `XML2VHDL` output.

=====================  ==========================  ===============  ==============  ===============
**Register**
**Name:**              REG39
**Address:**           ``0x0000_0027``
**Description:**       ED control
**Bit Fields**         **Description**             **Mask**         **Permission**  **Reset Value**
OVERWRITE_THRS         Overwrite threshold values  ``0x0000_0001``  Read/Write      ``0x0000_0000``
COUNTING_MODE_DISABLE  Disable counting mode       ``0x0000_0002``  Read/Write      ``0x0000_0000``
TEST_MODE_EN           Enable test mode            ``0x0000_0004``  Read/Write      ``0x0000_0000``
=====================  ==========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: OVERWRITE_THRS [ rotate = 270 ]
      1: COUNTING_MODE_DISABLE [ rotate = 270 ]
      2: TEST_MODE_EN [ rotate = 270 ]
      3-31:  [ color = lightgrey ]
   }

"""

REG40 = { 'addr': 40,
  'description': 'ED number of cycles Low Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG40',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG40` generated from `XML2VHDL` output.

================  ============================
**Register**
**Name:**         REG40
**Address:**      ``0x0000_0028``
**Description:**  ED number of cycles Low Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG40
      8-31:  [ color = lightgrey ]
   }

"""

REG41 = { 'addr': 41,
  'description': 'ED number of cycles High Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG41',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG41` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG41
**Address:**      ``0x0000_0029``
**Description:**  ED number of cycles High Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG41
      8-31:  [ color = lightgrey ]
   }

"""

REG42 = { 'addr': 42,
  'description': 'Number of frames in trigger mode [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG42',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG42` generated from `XML2VHDL` output.

================  =======================================
**Register**
**Name:**         REG42
**Address:**      ``0x0000_002A``
**Description:**  Number of frames in trigger mode [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =======================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG42
      8-31:  [ color = lightgrey ]
   }

"""

REG43 = { 'addr': 43,
  'description': 'Number of frames in trigger mode [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG43',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG43` generated from `XML2VHDL` output.

================  ========================================
**Register**
**Name:**         REG43
**Address:**      ``0x0000_002B``
**Description:**  Number of frames in trigger mode [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG43
      8-31:  [ color = lightgrey ]
   }

"""

REG44 = { 'addr': 44,
  'description': 'Number of frames in trigger mode [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG44',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG44` generated from `XML2VHDL` output.

================  =========================================
**Register**
**Name:**         REG44
**Address:**      ``0x0000_002C``
**Description:**  Number of frames in trigger mode [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG44
      8-31:  [ color = lightgrey ]
   }

"""

REG45 = { 'addr': 45,
  'description': 'Number of frames in trigger mode [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG45',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG45` generated from `XML2VHDL` output.

================  =========================================
**Register**
**Name:**         REG45
**Address:**      ``0x0000_002D``
**Description:**  Number of frames in trigger mode [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =========================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG45
      8-31:  [ color = lightgrey ]
   }

"""

REG46 = { 'addr': 46,
  'description': 'No description in documentation',
  'fields': [],
  'mask': 255,
  'name': 'REG46',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG46` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG46
**Address:**      ``0x0000_002E``
**Description:**  No description in documentation
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG46
      8-31:  [ color = lightgrey ]
   }

"""

REG47 = { 'addr': 47,
  'description': 'ASIC1 Row power enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG47',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG47` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG47
**Address:**      ``0x0000_002F``
**Description:**  ASIC1 Row power enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG47
      8-31:  [ color = lightgrey ]
   }

"""

REG48 = { 'addr': 48,
  'description': 'ASIC1 Row power enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG48',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG48` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG48
**Address:**      ``0x0000_0030``
**Description:**  ASIC1 Row power enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG48
      8-31:  [ color = lightgrey ]
   }

"""

REG49 = { 'addr': 49,
  'description': 'ASIC1 Row power enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG49',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG49` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG49
**Address:**      ``0x0000_0031``
**Description:**  ASIC1 Row power enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG49
      8-31:  [ color = lightgrey ]
   }

"""

REG50 = { 'addr': 50,
  'description': 'ASIC1 Row power enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG50',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG50` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG50
**Address:**      ``0x0000_0032``
**Description:**  ASIC1 Row power enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG50
      8-31:  [ color = lightgrey ]
   }

"""

REG51 = { 'addr': 51,
  'description': 'ASIC1 Row power enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG51',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG51` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG51
**Address:**      ``0x0000_0033``
**Description:**  ASIC1 Row power enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG51
      8-31:  [ color = lightgrey ]
   }

"""

REG52 = { 'addr': 52,
  'description': 'ASIC1 Row power enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG52',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG52` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG52
**Address:**      ``0x0000_0034``
**Description:**  ASIC1 Row power enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG52
      8-31:  [ color = lightgrey ]
   }

"""

REG53 = { 'addr': 53,
  'description': 'ASIC1 Row power enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG53',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG53` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG53
**Address:**      ``0x0000_0035``
**Description:**  ASIC1 Row power enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG53
      8-31:  [ color = lightgrey ]
   }

"""

REG54 = { 'addr': 54,
  'description': 'ASIC1 Row power enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG54',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG54` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG54
**Address:**      ``0x0000_0036``
**Description:**  ASIC1 Row power enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG54
      8-31:  [ color = lightgrey ]
   }

"""

REG55 = { 'addr': 55,
  'description': 'ASIC1 Row power enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG55',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG55` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG55
**Address:**      ``0x0000_0037``
**Description:**  ASIC1 Row power enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG55
      8-31:  [ color = lightgrey ]
   }

"""

REG56 = { 'addr': 56,
  'description': 'ASIC1 Row power enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG56',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG56` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG56
**Address:**      ``0x0000_0038``
**Description:**  ASIC1 Row power enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG56
      8-31:  [ color = lightgrey ]
   }

"""

REG57 = { 'addr': 57,
  'description': 'ASIC1 Row cal enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG57',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG57` generated from `XML2VHDL` output.

================  ===========================
**Register**
**Name:**         REG57
**Address:**      ``0x0000_0039``
**Description:**  ASIC1 Row cal enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===========================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG57
      8-31:  [ color = lightgrey ]
   }

"""

REG58 = { 'addr': 58,
  'description': 'ASIC1 Row cal enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG58',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG58` generated from `XML2VHDL` output.

================  ============================
**Register**
**Name:**         REG58
**Address:**      ``0x0000_003A``
**Description:**  ASIC1 Row cal enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG58
      8-31:  [ color = lightgrey ]
   }

"""

REG59 = { 'addr': 59,
  'description': 'ASIC1 Row cal enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG59',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG59` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG59
**Address:**      ``0x0000_003B``
**Description:**  ASIC1 Row cal enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG59
      8-31:  [ color = lightgrey ]
   }

"""

REG60 = { 'addr': 60,
  'description': 'ASIC1 Row cal enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG60',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG60` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG60
**Address:**      ``0x0000_003C``
**Description:**  ASIC1 Row cal enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG60
      8-31:  [ color = lightgrey ]
   }

"""

REG61 = { 'addr': 61,
  'description': 'ASIC1 Row cal enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG61',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG61` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG61
**Address:**      ``0x0000_003D``
**Description:**  ASIC1 Row cal enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG61
      8-31:  [ color = lightgrey ]
   }

"""

REG62 = { 'addr': 62,
  'description': 'ASIC1 Row cal enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG62',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG62` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG62
**Address:**      ``0x0000_003E``
**Description:**  ASIC1 Row cal enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG62
      8-31:  [ color = lightgrey ]
   }

"""

REG63 = { 'addr': 63,
  'description': 'ASIC1 Row cal enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG63',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG63` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG63
**Address:**      ``0x0000_003F``
**Description:**  ASIC1 Row cal enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG63
      8-31:  [ color = lightgrey ]
   }

"""

REG64 = { 'addr': 64,
  'description': 'ASIC1 Row cal enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG64',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG64` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG64
**Address:**      ``0x0000_0040``
**Description:**  ASIC1 Row cal enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG64
      8-31:  [ color = lightgrey ]
   }

"""

REG65 = { 'addr': 65,
  'description': 'ASIC1 Row cal enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG65',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG65` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG65
**Address:**      ``0x0000_0041``
**Description:**  ASIC1 Row cal enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG65
      8-31:  [ color = lightgrey ]
   }

"""

REG66 = { 'addr': 66,
  'description': 'ASIC1 Row cal enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG66',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG66` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG66
**Address:**      ``0x0000_0042``
**Description:**  ASIC1 Row cal enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG66
      8-31:  [ color = lightgrey ]
   }

"""

REG67 = { 'addr': 67,
  'description': 'ASIC1 Row read enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG67',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG67` generated from `XML2VHDL` output.

================  ============================
**Register**
**Name:**         REG67
**Address:**      ``0x0000_0043``
**Description:**  ASIC1 Row read enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG67
      8-31:  [ color = lightgrey ]
   }

"""

REG68 = { 'addr': 68,
  'description': 'ASIC1 Row read enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG68',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG68` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG68
**Address:**      ``0x0000_0044``
**Description:**  ASIC1 Row read enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG68
      8-31:  [ color = lightgrey ]
   }

"""

REG69 = { 'addr': 69,
  'description': 'ASIC1 Row read enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG69',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG69` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG69
**Address:**      ``0x0000_0045``
**Description:**  ASIC1 Row read enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG69
      8-31:  [ color = lightgrey ]
   }

"""

REG70 = { 'addr': 70,
  'description': 'ASIC1 Row read enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG70',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG70` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG70
**Address:**      ``0x0000_0046``
**Description:**  ASIC1 Row read enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG70
      8-31:  [ color = lightgrey ]
   }

"""

REG71 = { 'addr': 71,
  'description': 'ASIC1 Row read enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG71',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG71` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG71
**Address:**      ``0x0000_0047``
**Description:**  ASIC1 Row read enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG71
      8-31:  [ color = lightgrey ]
   }

"""

REG72 = { 'addr': 72,
  'description': 'ASIC1 Row read enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG72',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG72` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG72
**Address:**      ``0x0000_0048``
**Description:**  ASIC1 Row read enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG72
      8-31:  [ color = lightgrey ]
   }

"""

REG73 = { 'addr': 73,
  'description': 'ASIC1 Row read enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG73',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG73` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG73
**Address:**      ``0x0000_0049``
**Description:**  ASIC1 Row read enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG73
      8-31:  [ color = lightgrey ]
   }

"""

REG74 = { 'addr': 74,
  'description': 'ASIC1 Row read enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG74',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG74` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG74
**Address:**      ``0x0000_004A``
**Description:**  ASIC1 Row read enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG74
      8-31:  [ color = lightgrey ]
   }

"""

REG75 = { 'addr': 75,
  'description': 'ASIC1 Row read enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG75',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG75` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG75
**Address:**      ``0x0000_004B``
**Description:**  ASIC1 Row read enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG75
      8-31:  [ color = lightgrey ]
   }

"""

REG76 = { 'addr': 76,
  'description': 'ASIC1 Row read enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG76',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG76` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG76
**Address:**      ``0x0000_004C``
**Description:**  ASIC1 Row read enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG76
      8-31:  [ color = lightgrey ]
   }

"""

REG77 = { 'addr': 77,
  'description': 'ASIC1 Column power enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG77',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG77` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG77
**Address:**      ``0x0000_004D``
**Description:**  ASIC1 Column power enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG77
      8-31:  [ color = lightgrey ]
   }

"""

REG78 = { 'addr': 78,
  'description': 'ASIC1 Column power enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG78',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG78` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG78
**Address:**      ``0x0000_004E``
**Description:**  ASIC1 Column power enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG78
      8-31:  [ color = lightgrey ]
   }

"""

REG79 = { 'addr': 79,
  'description': 'ASIC1 Column power enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG79',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG79` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG79
**Address:**      ``0x0000_004F``
**Description:**  ASIC1 Column power enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG79
      8-31:  [ color = lightgrey ]
   }

"""

REG80 = { 'addr': 80,
  'description': 'ASIC1 Column power enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG80',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG80` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG80
**Address:**      ``0x0000_0050``
**Description:**  ASIC1 Column power enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG80
      8-31:  [ color = lightgrey ]
   }

"""

REG81 = { 'addr': 81,
  'description': 'ASIC1 Column power enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG81',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG81` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG81
**Address:**      ``0x0000_0051``
**Description:**  ASIC1 Column power enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG81
      8-31:  [ color = lightgrey ]
   }

"""

REG82 = { 'addr': 82,
  'description': 'ASIC1 Column power enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG82',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG82` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG82
**Address:**      ``0x0000_0052``
**Description:**  ASIC1 Column power enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG82
      8-31:  [ color = lightgrey ]
   }

"""

REG83 = { 'addr': 83,
  'description': 'ASIC1 Column power enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG83',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG83` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG83
**Address:**      ``0x0000_0053``
**Description:**  ASIC1 Column power enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG83
      8-31:  [ color = lightgrey ]
   }

"""

REG84 = { 'addr': 84,
  'description': 'ASIC1 Column power enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG84',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG84` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG84
**Address:**      ``0x0000_0054``
**Description:**  ASIC1 Column power enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG84
      8-31:  [ color = lightgrey ]
   }

"""

REG85 = { 'addr': 85,
  'description': 'ASIC1 Column power enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG85',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG85` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG85
**Address:**      ``0x0000_0055``
**Description:**  ASIC1 Column power enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG85
      8-31:  [ color = lightgrey ]
   }

"""

REG86 = { 'addr': 86,
  'description': 'ASIC1 Column power enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG86',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG86` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG86
**Address:**      ``0x0000_0056``
**Description:**  ASIC1 Column power enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG86
      8-31:  [ color = lightgrey ]
   }

"""

REG87 = { 'addr': 87,
  'description': 'ASIC1 Column cal enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG87',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG87` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG87
**Address:**      ``0x0000_0057``
**Description:**  ASIC1 Column cal enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG87
      8-31:  [ color = lightgrey ]
   }

"""

REG88 = { 'addr': 88,
  'description': 'ASIC1 Column cal enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG88',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG88` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG88
**Address:**      ``0x0000_0058``
**Description:**  ASIC1 Column cal enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG88
      8-31:  [ color = lightgrey ]
   }

"""

REG89 = { 'addr': 89,
  'description': 'ASIC1 Column cal enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG89',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG89` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG89
**Address:**      ``0x0000_0059``
**Description:**  ASIC1 Column cal enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG89
      8-31:  [ color = lightgrey ]
   }

"""

REG90 = { 'addr': 90,
  'description': 'ASIC1 Column cal enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG90',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG90` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG90
**Address:**      ``0x0000_005A``
**Description:**  ASIC1 Column cal enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG90
      8-31:  [ color = lightgrey ]
   }

"""

REG91 = { 'addr': 91,
  'description': 'ASIC1 Column cal enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG91',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG91` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG91
**Address:**      ``0x0000_005B``
**Description:**  ASIC1 Column cal enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG91
      8-31:  [ color = lightgrey ]
   }

"""

REG92 = { 'addr': 92,
  'description': 'ASIC1 Column cal enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG92',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG92` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG92
**Address:**      ``0x0000_005C``
**Description:**  ASIC1 Column cal enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG92
      8-31:  [ color = lightgrey ]
   }

"""

REG93 = { 'addr': 93,
  'description': 'ASIC1 Column cal enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG93',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG93` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG93
**Address:**      ``0x0000_005D``
**Description:**  ASIC1 Column cal enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG93
      8-31:  [ color = lightgrey ]
   }

"""

REG94 = { 'addr': 94,
  'description': 'ASIC1 Column cal enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG94',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG94` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG94
**Address:**      ``0x0000_005E``
**Description:**  ASIC1 Column cal enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG94
      8-31:  [ color = lightgrey ]
   }

"""

REG95 = { 'addr': 95,
  'description': 'ASIC1 Column cal enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG95',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG95` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG95
**Address:**      ``0x0000_005F``
**Description:**  ASIC1 Column cal enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG95
      8-31:  [ color = lightgrey ]
   }

"""

REG96 = { 'addr': 96,
  'description': 'ASIC1 Column cal enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG96',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG96` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG96
**Address:**      ``0x0000_0060``
**Description:**  ASIC1 Column cal enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG96
      8-31:  [ color = lightgrey ]
   }

"""

REG97 = { 'addr': 97,
  'description': 'ASIC1 Column read enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG97',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG97` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG97
**Address:**      ``0x0000_0061``
**Description:**  ASIC1 Column read enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG97
      8-31:  [ color = lightgrey ]
   }

"""

REG98 = { 'addr': 98,
  'description': 'ASIC1 Column read enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG98',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG98` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG98
**Address:**      ``0x0000_0062``
**Description:**  ASIC1 Column read enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG98
      8-31:  [ color = lightgrey ]
   }

"""

REG99 = { 'addr': 99,
  'description': 'ASIC1 Column read enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG99',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG99` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG99
**Address:**      ``0x0000_0063``
**Description:**  ASIC1 Column read enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG99
      8-31:  [ color = lightgrey ]
   }

"""

REG100 = { 'addr': 100,
  'description': 'ASIC1 Column read enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG100',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG100` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG100
**Address:**      ``0x0000_0064``
**Description:**  ASIC1 Column read enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG100
      8-31:  [ color = lightgrey ]
   }

"""

REG101 = { 'addr': 101,
  'description': 'ASIC1 Column read enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG101',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG101` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG101
**Address:**      ``0x0000_0065``
**Description:**  ASIC1 Column read enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG101
      8-31:  [ color = lightgrey ]
   }

"""

REG102 = { 'addr': 102,
  'description': 'ASIC1 Column read enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG102',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG102` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG102
**Address:**      ``0x0000_0066``
**Description:**  ASIC1 Column read enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG102
      8-31:  [ color = lightgrey ]
   }

"""

REG103 = { 'addr': 103,
  'description': 'ASIC1 Column read enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG103',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG103` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG103
**Address:**      ``0x0000_0067``
**Description:**  ASIC1 Column read enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG103
      8-31:  [ color = lightgrey ]
   }

"""

REG104 = { 'addr': 104,
  'description': 'ASIC1 Column read enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG104',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG104` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG104
**Address:**      ``0x0000_0068``
**Description:**  ASIC1 Column read enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG104
      8-31:  [ color = lightgrey ]
   }

"""

REG105 = { 'addr': 105,
  'description': 'ASIC1 Column read enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG105',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG105` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG105
**Address:**      ``0x0000_0069``
**Description:**  ASIC1 Column read enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG105
      8-31:  [ color = lightgrey ]
   }

"""

REG106 = { 'addr': 106,
  'description': 'ASIC1 Column read enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG106',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG106` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG106
**Address:**      ``0x0000_006A``
**Description:**  ASIC1 Column read enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG106
      8-31:  [ color = lightgrey ]
   }

"""

REG128 = { 'addr': 128,
  'description': 'Firmware customer ID',
  'fields': [],
  'mask': 63,
  'name': 'REG128',
  'nof_bits': 6,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG128` generated from `XML2VHDL` output.

================  ====================
**Register**
**Name:**         REG128
**Address:**      ``0x0000_0080``
**Description:**  Firmware customer ID
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ====================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: REG128
      6-31:  [ color = lightgrey ]
   }

"""

REG129 = { 'addr': 129,
  'description': 'Firmware project ID',
  'fields': [],
  'mask': 63,
  'name': 'REG129',
  'nof_bits': 6,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG129` generated from `XML2VHDL` output.

================  ===================
**Register**
**Name:**         REG129
**Address:**      ``0x0000_0081``
**Description:**  Firmware project ID
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-5: REG129
      6-31:  [ color = lightgrey ]
   }

"""

REG130 = { 'addr': 130,
  'description': 'Firmware version ID',
  'fields': [],
  'mask': 255,
  'name': 'REG130',
  'nof_bits': 8,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG130` generated from `XML2VHDL` output.

================  ===================
**Register**
**Name:**         REG130
**Address:**      ``0x0000_0082``
**Description:**  Firmware version ID
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG130
      8-31:  [ color = lightgrey ]
   }

"""

REG131 = { 'addr': 131,
  'description': 'Hexitec number of columns',
  'fields': [],
  'mask': 255,
  'name': 'REG131',
  'nof_bits': 8,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG131` generated from `XML2VHDL` output.

================  =========================
**Register**
**Name:**         REG131
**Address:**      ``0x0000_0083``
**Description:**  Hexitec number of columns
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =========================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG131
      8-31:  [ color = lightgrey ]
   }

"""

REG132 = { 'addr': 132,
  'description': 'Hexitec number of rows',
  'fields': [],
  'mask': 255,
  'name': 'REG132',
  'nof_bits': 8,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG132` generated from `XML2VHDL` output.

================  ======================
**Register**
**Name:**         REG132
**Address:**      ``0x0000_0084``
**Description:**  Hexitec number of rows
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ======================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG132
      8-31:  [ color = lightgrey ]
   }

"""

REG133 = { 'addr': 133,
  'description': 'Pleora trigger input status',
  'fields': [ { 'description': 'Pleora connector out 0',
                'is_bit': True,
                'mask': 1,
                'name': 'TRIGGER_1',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'Pleora connector out 1',
                'is_bit': True,
                'mask': 2,
                'name': 'TRIGGER_2',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1},
              { 'description': 'Pleora connector out 2',
                'is_bit': True,
                'mask': 4,
                'name': 'TRIGGER_3',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 2},
              { 'description': 'Pleora GPIO out 0',
                'is_bit': True,
                'mask': 8,
                'name': 'GPIO_0',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 3},
              { 'description': 'Pleora GPIO out 1',
                'is_bit': True,
                'mask': 16,
                'name': 'GPIO_1',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 4},
              { 'description': 'Pleora GPIO out 2',
                'is_bit': True,
                'mask': 32,
                'name': 'GPIO_2',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 5}],
  'mask': 4294967295,
  'name': 'REG133',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG133` generated from `XML2VHDL` output.

================  ===========================  ===============  ==============  ===============
**Register**
**Name:**         REG133
**Address:**      ``0x0000_0085``
**Description:**  Pleora trigger input status
**Bit Fields**    **Description**              **Mask**         **Permission**  **Reset Value**
TRIGGER_1         Pleora connector out 0       ``0x0000_0001``  Read/Write      ``0x0000_0000``
TRIGGER_2         Pleora connector out 1       ``0x0000_0002``  Read/Write      ``0x0000_0000``
TRIGGER_3         Pleora connector out 2       ``0x0000_0004``  Read/Write      ``0x0000_0000``
GPIO_0            Pleora GPIO out 0            ``0x0000_0008``  Read/Write      ``0x0000_0000``
GPIO_1            Pleora GPIO out 1            ``0x0000_0010``  Read/Write      ``0x0000_0000``
GPIO_2            Pleora GPIO out 2            ``0x0000_0020``  Read/Write      ``0x0000_0000``
================  ===========================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: TRIGGER_1 [ rotate = 270 ]
      1: TRIGGER_2 [ rotate = 270 ]
      2: TRIGGER_3 [ rotate = 270 ]
      3: GPIO_0 [ rotate = 270 ]
      4: GPIO_1 [ rotate = 270 ]
      5: GPIO_2 [ rotate = 270 ]
      6-31:  [ color = lightgrey ]
   }

"""

REG134 = { 'addr': 134,
  'description': 'No description in documentation',
  'fields': [],
  'mask': 255,
  'name': 'REG134',
  'nof_bits': 8,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG134` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG134
**Address:**      ``0x0000_0086``
**Description:**  No description in documentation
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG134
      8-31:  [ color = lightgrey ]
   }

"""

REG135 = { 'addr': 135,
  'description': 'No description in documentation',
  'fields': [],
  'mask': 255,
  'name': 'REG135',
  'nof_bits': 8,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG135` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG135
**Address:**      ``0x0000_0087``
**Description:**  No description in documentation
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG135
      8-31:  [ color = lightgrey ]
   }

"""

REG136 = { 'addr': 136,
  'description': 'ASIC calibration status',
  'fields': [ { 'description': 'Calibration data of both ASICs results in the '
                               'same image size',
                'is_bit': True,
                'mask': 1,
                'name': 'SAME_IMG_SIZE',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 1,
  'name': 'REG136',
  'nof_bits': 1,
  'reset_value': '0x00',
  'shiftr': 0}
""":const:`REG136` generated from `XML2VHDL` output.

================  =============================================================  ===============  ==============  ===============
**Register**
**Name:**         REG136
**Address:**      ``0x0000_0088``
**Description:**  ASIC calibration status
**Bit Fields**    **Description**                                                **Mask**         **Permission**  **Reset Value**
SAME_IMG_SIZE     Calibration data of both ASICs results in the same image size  ``0x0000_0001``  Read/Write      ``0x0000_0000``
================  =============================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: SAME_IMG_SIZE [ rotate = 270 ]
      1-31:  [ color = lightgrey ]
   }

"""

REG137 = { 'addr': 137,
  'description': 'Status',
  'fields': [ { 'description': 'Capture DC ready',
                'is_bit': True,
                'mask': 1,
                'name': 'CAPTURE_RDY',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0},
              { 'description': 'PLL locked',
                'is_bit': True,
                'mask': 2,
                'name': 'PLL_LOCKED',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 1}],
  'mask': 4294967295,
  'name': 'REG137',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG137` generated from `XML2VHDL` output.

================  ================  ===============  ==============  ===============
**Register**
**Name:**         REG137
**Address:**      ``0x0000_0089``
**Description:**  Status
**Bit Fields**    **Description**   **Mask**         **Permission**  **Reset Value**
CAPTURE_RDY       Capture DC ready  ``0x0000_0001``  Read/Write      ``0x0000_0000``
PLL_LOCKED        PLL locked        ``0x0000_0002``  Read/Write      ``0x0000_0000``
================  ================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: CAPTURE_RDY [ rotate = 270 ]
      1: PLL_LOCKED [ rotate = 270 ]
      2-31:  [ color = lightgrey ]
   }

"""

REG143 = { 'addr': 143,
  'description': 'ASIC calibration control',
  'fields': [ { 'description': 'Use the same calibration data for both ASICs '
                               '(as described in register 47..106)',
                'is_bit': True,
                'mask': 1,
                'name': 'SAME_CAL',
                'nof_bits': 1,
                'reset_value': '0x0',
                'shiftr': 0}],
  'mask': 4294967295,
  'name': 'REG143',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG143` generated from `XML2VHDL` output.

================  ===============================================================================  ===============  ==============  ===============
**Register**
**Name:**         REG143
**Address:**      ``0x0000_008F``
**Description:**  ASIC calibration control
**Bit Fields**    **Description**                                                                  **Mask**         **Permission**  **Reset Value**
SAME_CAL          Use the same calibration data for both ASICs (as described in register 47..106)  ``0x0000_0001``  Read/Write      ``0x0000_0000``
================  ===============================================================================  ===============  ==============  ===============

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0: SAME_CAL [ rotate = 270 ]
      1-31:  [ color = lightgrey ]
   }

"""

REG144 = { 'addr': 144,
  'description': 'ASIC2 Row power enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG144',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG144` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG144
**Address:**      ``0x0000_0090``
**Description:**  ASIC2 Row power enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG144
      8-31:  [ color = lightgrey ]
   }

"""

REG145 = { 'addr': 145,
  'description': 'ASIC2 Row power enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG145',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG145` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG145
**Address:**      ``0x0000_0091``
**Description:**  ASIC2 Row power enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG145
      8-31:  [ color = lightgrey ]
   }

"""

REG146 = { 'addr': 146,
  'description': 'ASIC2 Row power enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG146',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG146` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG146
**Address:**      ``0x0000_0092``
**Description:**  ASIC2 Row power enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG146
      8-31:  [ color = lightgrey ]
   }

"""

REG147 = { 'addr': 147,
  'description': 'ASIC2 Row power enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG147',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG147` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG147
**Address:**      ``0x0000_0093``
**Description:**  ASIC2 Row power enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG147
      8-31:  [ color = lightgrey ]
   }

"""

REG148 = { 'addr': 148,
  'description': 'ASIC2 Row power enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG148',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG148` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG148
**Address:**      ``0x0000_0094``
**Description:**  ASIC2 Row power enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG148
      8-31:  [ color = lightgrey ]
   }

"""

REG149 = { 'addr': 149,
  'description': 'ASIC2 Row power enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG149',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG149` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG149
**Address:**      ``0x0000_0095``
**Description:**  ASIC2 Row power enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG149
      8-31:  [ color = lightgrey ]
   }

"""

REG150 = { 'addr': 150,
  'description': 'ASIC2 Row power enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG150',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG150` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG150
**Address:**      ``0x0000_0096``
**Description:**  ASIC2 Row power enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG150
      8-31:  [ color = lightgrey ]
   }

"""

REG151 = { 'addr': 151,
  'description': 'ASIC2 Row power enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG151',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG151` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG151
**Address:**      ``0x0000_0097``
**Description:**  ASIC2 Row power enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG151
      8-31:  [ color = lightgrey ]
   }

"""

REG152 = { 'addr': 152,
  'description': 'ASIC2 Row power enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG152',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG152` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG152
**Address:**      ``0x0000_0098``
**Description:**  ASIC2 Row power enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG152
      8-31:  [ color = lightgrey ]
   }

"""

REG153 = { 'addr': 153,
  'description': 'ASIC2 Row power enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG153',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG153` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG153
**Address:**      ``0x0000_0099``
**Description:**  ASIC2 Row power enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG153
      8-31:  [ color = lightgrey ]
   }

"""

REG154 = { 'addr': 154,
  'description': 'ASIC2 Row cal enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG154',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG154` generated from `XML2VHDL` output.

================  ===========================
**Register**
**Name:**         REG154
**Address:**      ``0x0000_009A``
**Description:**  ASIC2 Row cal enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===========================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG154
      8-31:  [ color = lightgrey ]
   }

"""

REG155 = { 'addr': 155,
  'description': 'ASIC2 Row cal enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG155',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG155` generated from `XML2VHDL` output.

================  ============================
**Register**
**Name:**         REG155
**Address:**      ``0x0000_009B``
**Description:**  ASIC2 Row cal enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG155
      8-31:  [ color = lightgrey ]
   }

"""

REG156 = { 'addr': 156,
  'description': 'ASIC2 Row cal enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG156',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG156` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG156
**Address:**      ``0x0000_009C``
**Description:**  ASIC2 Row cal enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG156
      8-31:  [ color = lightgrey ]
   }

"""

REG157 = { 'addr': 157,
  'description': 'ASIC2 Row cal enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG157',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG157` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG157
**Address:**      ``0x0000_009D``
**Description:**  ASIC2 Row cal enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG157
      8-31:  [ color = lightgrey ]
   }

"""

REG158 = { 'addr': 158,
  'description': 'ASIC2 Row cal enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG158',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG158` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG158
**Address:**      ``0x0000_009E``
**Description:**  ASIC2 Row cal enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG158
      8-31:  [ color = lightgrey ]
   }

"""

REG159 = { 'addr': 159,
  'description': 'ASIC2 Row cal enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG159',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG159` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG159
**Address:**      ``0x0000_009F``
**Description:**  ASIC2 Row cal enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG159
      8-31:  [ color = lightgrey ]
   }

"""

REG160 = { 'addr': 160,
  'description': 'ASIC2 Row cal enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG160',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG160` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG160
**Address:**      ``0x0000_00A0``
**Description:**  ASIC2 Row cal enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG160
      8-31:  [ color = lightgrey ]
   }

"""

REG161 = { 'addr': 161,
  'description': 'ASIC2 Row cal enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG161',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG161` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG161
**Address:**      ``0x0000_00A1``
**Description:**  ASIC2 Row cal enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG161
      8-31:  [ color = lightgrey ]
   }

"""

REG162 = { 'addr': 162,
  'description': 'ASIC2 Row cal enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG162',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG162` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG162
**Address:**      ``0x0000_00A2``
**Description:**  ASIC2 Row cal enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG162
      8-31:  [ color = lightgrey ]
   }

"""

REG163 = { 'addr': 163,
  'description': 'ASIC2 Row cal enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG163',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG163` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG163
**Address:**      ``0x0000_00A3``
**Description:**  ASIC2 Row cal enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG163
      8-31:  [ color = lightgrey ]
   }

"""

REG164 = { 'addr': 164,
  'description': 'ASIC2 Row read enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG164',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG164` generated from `XML2VHDL` output.

================  ============================
**Register**
**Name:**         REG164
**Address:**      ``0x0000_00A4``
**Description:**  ASIC2 Row read enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG164
      8-31:  [ color = lightgrey ]
   }

"""

REG165 = { 'addr': 165,
  'description': 'ASIC2 Row read enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG165',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG165` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG165
**Address:**      ``0x0000_00A5``
**Description:**  ASIC2 Row read enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG165
      8-31:  [ color = lightgrey ]
   }

"""

REG166 = { 'addr': 166,
  'description': 'ASIC2 Row read enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG166',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG166` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG166
**Address:**      ``0x0000_00A6``
**Description:**  ASIC2 Row read enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG166
      8-31:  [ color = lightgrey ]
   }

"""

REG167 = { 'addr': 167,
  'description': 'ASIC2 Row read enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG167',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG167` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG167
**Address:**      ``0x0000_00A7``
**Description:**  ASIC2 Row read enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG167
      8-31:  [ color = lightgrey ]
   }

"""

REG168 = { 'addr': 168,
  'description': 'ASIC2 Row read enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG168',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG168` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG168
**Address:**      ``0x0000_00A8``
**Description:**  ASIC2 Row read enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG168
      8-31:  [ color = lightgrey ]
   }

"""

REG169 = { 'addr': 169,
  'description': 'ASIC2 Row read enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG169',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG169` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG169
**Address:**      ``0x0000_00A9``
**Description:**  ASIC2 Row read enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG169
      8-31:  [ color = lightgrey ]
   }

"""

REG170 = { 'addr': 170,
  'description': 'ASIC2 Row read enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG170',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG170` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG170
**Address:**      ``0x0000_00AA``
**Description:**  ASIC2 Row read enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG170
      8-31:  [ color = lightgrey ]
   }

"""

REG171 = { 'addr': 171,
  'description': 'ASIC2 Row read enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG171',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG171` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG171
**Address:**      ``0x0000_00AB``
**Description:**  ASIC2 Row read enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG171
      8-31:  [ color = lightgrey ]
   }

"""

REG172 = { 'addr': 172,
  'description': 'ASIC2 Row read enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG172',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG172` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG172
**Address:**      ``0x0000_00AC``
**Description:**  ASIC2 Row read enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG172
      8-31:  [ color = lightgrey ]
   }

"""

REG173 = { 'addr': 173,
  'description': 'ASIC2 Row read enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG173',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG173` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG173
**Address:**      ``0x0000_00AD``
**Description:**  ASIC2 Row read enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG173
      8-31:  [ color = lightgrey ]
   }

"""

REG174 = { 'addr': 174,
  'description': 'ASIC2 Column power enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG174',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG174` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG174
**Address:**      ``0x0000_00AE``
**Description:**  ASIC2 Column power enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG174
      8-31:  [ color = lightgrey ]
   }

"""

REG175 = { 'addr': 175,
  'description': 'ASIC2 Column power enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG175',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG175` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG175
**Address:**      ``0x0000_00AF``
**Description:**  ASIC2 Column power enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG175
      8-31:  [ color = lightgrey ]
   }

"""

REG176 = { 'addr': 176,
  'description': 'ASIC2 Column power enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG176',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG176` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG176
**Address:**      ``0x0000_00B0``
**Description:**  ASIC2 Column power enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG176
      8-31:  [ color = lightgrey ]
   }

"""

REG177 = { 'addr': 177,
  'description': 'ASIC2 Column power enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG177',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG177` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG177
**Address:**      ``0x0000_00B1``
**Description:**  ASIC2 Column power enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG177
      8-31:  [ color = lightgrey ]
   }

"""

REG178 = { 'addr': 178,
  'description': 'ASIC2 Column power enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG178',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG178` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG178
**Address:**      ``0x0000_00B2``
**Description:**  ASIC2 Column power enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG178
      8-31:  [ color = lightgrey ]
   }

"""

REG179 = { 'addr': 179,
  'description': 'ASIC2 Column power enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG179',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG179` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG179
**Address:**      ``0x0000_00B3``
**Description:**  ASIC2 Column power enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG179
      8-31:  [ color = lightgrey ]
   }

"""

REG180 = { 'addr': 180,
  'description': 'ASIC2 Column power enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG180',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG180` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG180
**Address:**      ``0x0000_00B4``
**Description:**  ASIC2 Column power enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG180
      8-31:  [ color = lightgrey ]
   }

"""

REG181 = { 'addr': 181,
  'description': 'ASIC2 Column power enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG181',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG181` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG181
**Address:**      ``0x0000_00B5``
**Description:**  ASIC2 Column power enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG181
      8-31:  [ color = lightgrey ]
   }

"""

REG182 = { 'addr': 182,
  'description': 'ASIC2 Column power enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG182',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG182` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG182
**Address:**      ``0x0000_00B6``
**Description:**  ASIC2 Column power enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG182
      8-31:  [ color = lightgrey ]
   }

"""

REG183 = { 'addr': 183,
  'description': 'ASIC2 Column power enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG183',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG183` generated from `XML2VHDL` output.

================  ==================================
**Register**
**Name:**         REG183
**Address:**      ``0x0000_00B7``
**Description:**  ASIC2 Column power enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG183
      8-31:  [ color = lightgrey ]
   }

"""

REG184 = { 'addr': 184,
  'description': 'ASIC2 Column cal enable 0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG184',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG184` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         REG184
**Address:**      ``0x0000_00B8``
**Description:**  ASIC2 Column cal enable 0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG184
      8-31:  [ color = lightgrey ]
   }

"""

REG185 = { 'addr': 185,
  'description': 'ASIC2 Column cal enable 8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG185',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG185` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         REG185
**Address:**      ``0x0000_00B9``
**Description:**  ASIC2 Column cal enable 8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG185
      8-31:  [ color = lightgrey ]
   }

"""

REG186 = { 'addr': 186,
  'description': 'ASIC2 Column cal enable 16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG186',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG186` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG186
**Address:**      ``0x0000_00BA``
**Description:**  ASIC2 Column cal enable 16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG186
      8-31:  [ color = lightgrey ]
   }

"""

REG187 = { 'addr': 187,
  'description': 'ASIC2 Column cal enable 24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG187',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG187` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG187
**Address:**      ``0x0000_00BB``
**Description:**  ASIC2 Column cal enable 24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG187
      8-31:  [ color = lightgrey ]
   }

"""

REG188 = { 'addr': 188,
  'description': 'ASIC2 Column cal enable 32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG188',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG188` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG188
**Address:**      ``0x0000_00BC``
**Description:**  ASIC2 Column cal enable 32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG188
      8-31:  [ color = lightgrey ]
   }

"""

REG189 = { 'addr': 189,
  'description': 'ASIC2 Column cal enable 40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG189',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG189` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG189
**Address:**      ``0x0000_00BD``
**Description:**  ASIC2 Column cal enable 40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG189
      8-31:  [ color = lightgrey ]
   }

"""

REG190 = { 'addr': 190,
  'description': 'ASIC2 Column cal enable 48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG190',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG190` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG190
**Address:**      ``0x0000_00BE``
**Description:**  ASIC2 Column cal enable 48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG190
      8-31:  [ color = lightgrey ]
   }

"""

REG191 = { 'addr': 191,
  'description': 'ASIC2 Column cal enable 56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG191',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG191` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG191
**Address:**      ``0x0000_00BF``
**Description:**  ASIC2 Column cal enable 56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG191
      8-31:  [ color = lightgrey ]
   }

"""

REG192 = { 'addr': 192,
  'description': 'ASIC2 Column cal enable 64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG192',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG192` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG192
**Address:**      ``0x0000_00C0``
**Description:**  ASIC2 Column cal enable 64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG192
      8-31:  [ color = lightgrey ]
   }

"""

REG193 = { 'addr': 193,
  'description': 'ASIC2 Column cal enable 72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG193',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG193` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG193
**Address:**      ``0x0000_00C1``
**Description:**  ASIC2 Column cal enable 72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG193
      8-31:  [ color = lightgrey ]
   }

"""

REG194 = { 'addr': 194,
  'description': 'ASIC2 Column read enable [0..7]',
  'fields': [],
  'mask': 255,
  'name': 'REG194',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG194` generated from `XML2VHDL` output.

================  ===============================
**Register**
**Name:**         REG194
**Address:**      ``0x0000_00C2``
**Description:**  ASIC2 Column read enable [0..7]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ===============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG194
      8-31:  [ color = lightgrey ]
   }

"""

REG195 = { 'addr': 195,
  'description': 'ASIC2 Column read enable [8..15]',
  'fields': [],
  'mask': 255,
  'name': 'REG195',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG195` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG195
**Address:**      ``0x0000_00C3``
**Description:**  ASIC2 Column read enable [8..15]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG195
      8-31:  [ color = lightgrey ]
   }

"""

REG196 = { 'addr': 196,
  'description': 'ASIC2 Column read enable [16..23]',
  'fields': [],
  'mask': 255,
  'name': 'REG196',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG196` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG196
**Address:**      ``0x0000_00C4``
**Description:**  ASIC2 Column read enable [16..23]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG196
      8-31:  [ color = lightgrey ]
   }

"""

REG197 = { 'addr': 197,
  'description': 'ASIC2 Column read enable [24..31]',
  'fields': [],
  'mask': 255,
  'name': 'REG197',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG197` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG197
**Address:**      ``0x0000_00C5``
**Description:**  ASIC2 Column read enable [24..31]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG197
      8-31:  [ color = lightgrey ]
   }

"""

REG198 = { 'addr': 198,
  'description': 'ASIC2 Column read enable [32..39]',
  'fields': [],
  'mask': 255,
  'name': 'REG198',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG198` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG198
**Address:**      ``0x0000_00C6``
**Description:**  ASIC2 Column read enable [32..39]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG198
      8-31:  [ color = lightgrey ]
   }

"""

REG199 = { 'addr': 199,
  'description': 'ASIC2 Column read enable [40..47]',
  'fields': [],
  'mask': 255,
  'name': 'REG199',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG199` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG199
**Address:**      ``0x0000_00C7``
**Description:**  ASIC2 Column read enable [40..47]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG199
      8-31:  [ color = lightgrey ]
   }

"""

REG200 = { 'addr': 200,
  'description': 'ASIC2 Column read enable [48..55]',
  'fields': [],
  'mask': 255,
  'name': 'REG200',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG200` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG200
**Address:**      ``0x0000_00C8``
**Description:**  ASIC2 Column read enable [48..55]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG200
      8-31:  [ color = lightgrey ]
   }

"""

REG201 = { 'addr': 201,
  'description': 'ASIC2 Column read enable [56..63]',
  'fields': [],
  'mask': 255,
  'name': 'REG201',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG201` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG201
**Address:**      ``0x0000_00C9``
**Description:**  ASIC2 Column read enable [56..63]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG201
      8-31:  [ color = lightgrey ]
   }

"""

REG202 = { 'addr': 202,
  'description': 'ASIC2 Column read enable [64..71]',
  'fields': [],
  'mask': 255,
  'name': 'REG202',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG202` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG202
**Address:**      ``0x0000_00CA``
**Description:**  ASIC2 Column read enable [64..71]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG202
      8-31:  [ color = lightgrey ]
   }

"""

REG203 = { 'addr': 203,
  'description': 'ASIC2 Column read enable [72..79]',
  'fields': [],
  'mask': 255,
  'name': 'REG203',
  'nof_bits': 8,
  'reset_value': '0xFF',
  'shiftr': 0}
""":const:`REG203` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG203
**Address:**      ``0x0000_00CB``
**Description:**  ASIC2 Column read enable [72..79]
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_00FF``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG203
      8-31:  [ color = lightgrey ]
   }

"""

REG254 = { 'addr': 254,
  'description': 'Serial training pattern Low Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG254',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG254` generated from `XML2VHDL` output.

================  ================================
**Register**
**Name:**         REG254
**Address:**      ``0x0000_00FE``
**Description:**  Serial training pattern Low Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  ================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG254
      8-31:  [ color = lightgrey ]
   }

"""

REG255 = { 'addr': 255,
  'description': 'Serial training pattern High Byte',
  'fields': [],
  'mask': 255,
  'name': 'REG255',
  'nof_bits': 8,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`REG255` generated from `XML2VHDL` output.

================  =================================
**Register**
**Name:**         REG255
**Address:**      ``0x0000_00FF``
**Description:**  Serial training pattern High Byte
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0000``
================  =================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-7: REG255
      8-31:  [ color = lightgrey ]
   }

"""
