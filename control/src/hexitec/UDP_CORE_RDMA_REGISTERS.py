# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.

# *** This file was AUTO-GENERATED. Modifications to this file will be overwritten. ***
"""IC ID and Register dictionaries extracted from XML2VHDL formatted `xml` memory-map generation output file."""
UDP_CORE_CONTROL_ID = {'addr_offset': 0, 'fields': [], 'name': 'UDP_CORE_CONTROL_ID'}
"""XML2VHDL IC References generated from `XML2VHDL` output.

===================  ===============
**ID**               **Offset
UDP_CORE_CONTROL_ID  ``0x0000_0000``
===================  ===============
"""

UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER = { 'addr': 0,
  'description': 'Source MAC Address Lower',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER',
  'nof_bits': 32,
  'reset_value': '0x00000201',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         UDP_CORE_CONTROL_SRC_MAC_ADDR_LOWER
**Address:**      ``0x0000_0000``
**Description:**  Source MAC Address Lower
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_0201``
================  ===================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SRC_MAC_ADDR_LOWER
   }

"""

UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER = { 'addr': 4,
  'description': 'Source MAC Address Upper',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER',
  'nof_bits': 16,
  'reset_value': '0x6200',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         UDP_CORE_CONTROL_SRC_MAC_ADDR_UPPER
**Address:**      ``0x0000_0004``
**Description:**  Source MAC Address Upper
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_6200``
================  ===================================

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

UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER = { 'addr': 12,
  'description': 'Destination MAC Address Lower',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER',
  'nof_bits': 32,
  'reset_value': '0x00000FF00',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         UDP_CORE_CONTROL_DST_MAC_ADDR_LOWER
**Address:**      ``0x0000_000C``
**Description:**  Destination MAC Address Lower
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_FF00``
================  ===================================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DST_MAC_ADDR_LOWER
   }

"""

UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER = { 'addr': 16,
  'description': 'Destination MAC Address Upper',
  'fields': [],
  'mask': 65535,
  'name': 'UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER',
  'nof_bits': 16,
  'reset_value': '0x6200',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER` generated from `XML2VHDL` output.

================  ===================================
**Register**
**Name:**         UDP_CORE_CONTROL_DST_MAC_ADDR_UPPER
**Address:**      ``0x0000_0010``
**Description:**  Destination MAC Address Upper
**Permission:**   Read/Write
**Reset Value:**  ``0x0000_6200``
================  ===================================

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

UDP_CORE_CONTROL_DST_IP_ADDR = { 'addr': 36,
  'description': 'UDP Destination IP Address',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_DST_IP_ADDR',
  'nof_bits': 32,
  'reset_value': '0xC0A80201',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_DST_IP_ADDR` generated from `XML2VHDL` output.

================  ============================
**Register**
**Name:**         UDP_CORE_CONTROL_DST_IP_ADDR
**Address:**      ``0x0000_0024``
**Description:**  UDP Destination IP Address
**Permission:**   Read/Write
**Reset Value:**  ``0xC0A8_0201``
================  ============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: DST_IP_ADDR
   }

"""

UDP_CORE_CONTROL_SRC_IP_ADDR = { 'addr': 40,
  'description': 'UDP Source IP Address',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_SRC_IP_ADDR',
  'nof_bits': 32,
  'reset_value': '0xC0A8020B',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_SRC_IP_ADDR` generated from `XML2VHDL` output.

================  ============================
**Register**
**Name:**         UDP_CORE_CONTROL_SRC_IP_ADDR
**Address:**      ``0x0000_0028``
**Description:**  UDP Source IP Address
**Permission:**   Read/Write
**Reset Value:**  ``0xC0A8_020B``
================  ============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: SRC_IP_ADDR
   }

"""

UDP_CORE_CONTROL_UDP_PORTS = { 'addr': 44,
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
  'name': 'UDP_CORE_CONTROL_UDP_PORTS',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_UDP_PORTS` generated from `XML2VHDL` output.

================  ==========================  ===============  ==============  ===============
**Register**
**Name:**         UDP_CORE_CONTROL_UDP_PORTS
**Address:**      ``0x0000_002C``
**Description:**  UDP Ports
**Bit Fields**    **Description**             **Mask**         **Permission**  **Reset Value**
SRC_PORT          UDP Source Port             ``0x0000_FFFF``  Read/Write      ``0x0000_F0D0``
DST_PORT          UDP Destination Port        ``0xFFFF_0000``  Read/Write      ``0x0000_F0D1``
================  ==========================  ===============  ==============  ===============

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

UDP_CORE_CONTROL_FILTER_CONTROL = { 'addr': 56,
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
  'name': 'UDP_CORE_CONTROL_FILTER_CONTROL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_FILTER_CONTROL` generated from `XML2VHDL` output.

==================  ================================================================  ===============  ==============  ===============
**Register**
**Name:**           UDP_CORE_CONTROL_FILTER_CONTROL
**Address:**        ``0x0000_0038``
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

UDP_CORE_CONTROL_CONTROL = { 'addr': 72,
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
  'name': 'UDP_CORE_CONTROL_CONTROL',
  'nof_bits': 32,
  'reset_value': '0x0',
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_CONTROL` generated from `XML2VHDL` output.

=================  ===========================================================================  ===============  ==============  ===============
**Register**
**Name:**          UDP_CORE_CONTROL_CONTROL
**Address:**       ``0x0000_0048``
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

UDP_CORE_CONTROL_UDP_COUNT = { 'addr': 76,
  'description': 'Counter For Valid UDP Packets',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_UDP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_UDP_COUNT` generated from `XML2VHDL` output.

================  =============================
**Register**
**Name:**         UDP_CORE_CONTROL_UDP_COUNT
**Address:**      ``0x0000_004C``
**Description:**  Counter For Valid UDP Packets
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  =============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: UDP_COUNT
   }

"""

UDP_CORE_CONTROL_PING_COUNT = { 'addr': 80,
  'description': 'Counter For Valid Ping Packets',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_PING_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_PING_COUNT` generated from `XML2VHDL` output.

================  ==============================
**Register**
**Name:**         UDP_CORE_CONTROL_PING_COUNT
**Address:**      ``0x0000_0050``
**Description:**  Counter For Valid Ping Packets
**Permission:**   Read-Only
**Reset Value:**  \-\-\-
================  ==============================

.. packetdiag::

   packetdiag {
      colwidth = 32
      node_height = 144
      scale_direction = right_to_left
      scale_interval = 8

      0-31: PING_COUNT
   }

"""

UDP_CORE_CONTROL_ARP_COUNT = { 'addr': 84,
  'description': 'Counter For Valid ARP Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_ARP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_ARP_COUNT` generated from `XML2VHDL` output.

================  ================================================
**Register**
**Name:**         UDP_CORE_CONTROL_ARP_COUNT
**Address:**      ``0x0000_0054``
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

UDP_CORE_CONTROL_UNS_ETYPE_COUNT = { 'addr': 88,
  'description': 'Counter Unsupported Etype Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_UNS_ETYPE_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_UNS_ETYPE_COUNT` generated from `XML2VHDL` output.

================  ====================================================
**Register**
**Name:**         UDP_CORE_CONTROL_UNS_ETYPE_COUNT
**Address:**      ``0x0000_0058``
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

UDP_CORE_CONTROL_UNS_PRO_COUNT = { 'addr': 92,
  'description': 'Counter Unsupported Protocol Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_UNS_PRO_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_UNS_PRO_COUNT` generated from `XML2VHDL` output.

================  =======================================================
**Register**
**Name:**         UDP_CORE_CONTROL_UNS_PRO_COUNT
**Address:**      ``0x0000_005C``
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

UDP_CORE_CONTROL_DROPPED_MAC_COUNT = { 'addr': 96,
  'description': 'Counter For Dropped Mac Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_DROPPED_MAC_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_DROPPED_MAC_COUNT` generated from `XML2VHDL` output.

================  =======================================================
**Register**
**Name:**         UDP_CORE_CONTROL_DROPPED_MAC_COUNT
**Address:**      ``0x0000_0060``
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

UDP_CORE_CONTROL_DROPPED_IP_COUNT = { 'addr': 100,
  'description': 'Counter For Dropped IP Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_DROPPED_IP_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_DROPPED_IP_COUNT` generated from `XML2VHDL` output.

================  ======================================================
**Register**
**Name:**         UDP_CORE_CONTROL_DROPPED_IP_COUNT
**Address:**      ``0x0000_0064``
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

UDP_CORE_CONTROL_DROPPED_PORT_COUNT = { 'addr': 104,
  'description': 'Counter For Dropped Port Addr Packets Detected In Filter',
  'fields': [],
  'mask': 4294967295,
  'name': 'UDP_CORE_CONTROL_DROPPED_PORT_COUNT',
  'nof_bits': 32,
  'reset_value': None,
  'shiftr': 0}
""":const:`UDP_CORE_CONTROL_DROPPED_PORT_COUNT` generated from `XML2VHDL` output.

================  ========================================================
**Register**
**Name:**         UDP_CORE_CONTROL_DROPPED_PORT_COUNT
**Address:**      ``0x0000_0068``
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
