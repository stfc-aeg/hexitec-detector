"""
set_udp_registers.py - Python scripting for setting UDP header addresses and ports.

Christian Angelsen, STFC Detector Systems Software Group, 2020.
"""

import json

import sys
from QemCam import QemCam
from socket import error as socket_error


class set_udp_registers():
    """Class for configuring UDP core in firmware."""

    def __init__(self, json_file, fem_id):
        """Initialize the Object."""
        self.udp_settings = {}
        self.config_file = json_file
        self.id_number = fem_id

    def read_ip_settings(self):
        """Read the IP, MAC and port settings from the json file.

        Ripe for re-factoring into several functions..
        """
        try:
            with open(self.config_file, 'r') as f:
                self.udp_settings = json.load(f)
        except IOError as e:
            print("ERROR opening config file: %s" % e)
            return
        except Exception as e:
            print("ERROR: %s" % e)
            return

        print("Json object .keys()")
        print(self.udp_settings.keys())
        print("")

        try:
            self.qemcamera = QemCam()
            self.qemcamera.connect()
        except socket_error as e:
            print("ERROR establishing camera connection: %s" % e)
            return

        fem_id = "fem_{}".format(self.id_number)
        pc = self.udp_settings[fem_id]["pc"]
        fem = self.udp_settings[fem_id]["fem"]
        print("fem_id", fem_id)
        print("PC: ", pc)
        print("FEM: ", fem)

        fem_mac_tokens = fem["mac"].split(":")
        fem_mac_tokens.reverse()
        fem_mac_tokens = self.turn_unicode_list_into_string_list(fem_mac_tokens)

        pc_mac_tokens = pc["mac"].split(":")
        pc_mac_tokens.reverse()
        pc_mac_tokens = self.turn_unicode_list_into_string_list(pc_mac_tokens)

        self.data_address_00000000 = fem_mac_tokens[2] + fem_mac_tokens[3] + fem_mac_tokens[4] + fem_mac_tokens[5]
        self.data_address_00000001 = pc_mac_tokens[4] + pc_mac_tokens[5] + fem_mac_tokens[0] + fem_mac_tokens[1]
        self.data_address_00000002 = pc_mac_tokens[0] + pc_mac_tokens[1] + pc_mac_tokens[2] + pc_mac_tokens[3]

        # Split into a list of Unicode tokens
        fem_ip_tokens = fem["ip"].split(".")
        print("fem_ip_tokens: ", fem_ip_tokens)
        pc_ip_tokens = pc["ip"].split(".")
        tx_port = pc["port"]
        rx_port = fem["port"]
        rx_tokens = []
        # Reverve order, ie 'AABB' -> 'BB', 'AA'
        rx_tokens.append(hex(rx_port >> 8)[2:])
        rx_tokens.append(hex(rx_port & 0xFF)[2:])

        tx_tokens = []
        tx_tokens.append(hex(tx_port >> 8)[2:])
        tx_tokens.append(hex(tx_port & 0xFF)[2:])

        # Change from decimal to hexadecimal
        fem_ip_tokens = self.turn_decimal_list_into_hexadecimal_list(fem_ip_tokens)
        pc_ip_tokens = self.turn_decimal_list_into_hexadecimal_list(pc_ip_tokens)

        # Find existing (to remain unchanged) LSB (0x0..6) and MSB (0.0..9) halfs
        data_0x00000006 = self.qemcamera.x10g_rdma.read(0x00000006, 'N/A')
        # print "0x00000006 = %.8x" % data_0x00000006, type(data_0x00000006)

        data_0x00000009 = self.qemcamera.x10g_rdma.read(0x00000009, 'N/A')
        # print "0x00000009 = %.8x" % data_0x00000009, type(data_0x00000009)

        # Returned data format: '0x000877b8'; Thus [6:] = '77b8', [2:6] = '0008'
        data_0x00000006_LSB = format(data_0x00000006, '#010x')[6:]
        # '77b8'
        data_0x00000009_MSB = format(data_0x00000009, '#010x')[2:6]
        # '0008'

        self.data_address_00000006 = pc_ip_tokens[1] + pc_ip_tokens[0] + data_0x00000006_LSB
        self.data_address_00000007 = fem_ip_tokens[1] + fem_ip_tokens[0] + pc_ip_tokens[3] + pc_ip_tokens[2]
        self.data_address_00000008 = tx_tokens[1] + tx_tokens[0] + fem_ip_tokens[3] + fem_ip_tokens[2]
        self.data_address_00000009 = data_0x00000009_MSB + rx_tokens[1] + rx_tokens[0]

        print("-=-=-=-=- HEX'MAL -=-=-=-=-")
        print("0x00000000: ", self.data_address_00000000)
        print("0x00000001: ", self.data_address_00000001)
        print("0x00000002: ", self.data_address_00000002)
        print("0x00000006: ", self.data_address_00000006)
        print("0x00000007: ", self.data_address_00000007)
        print("0x00000008: ", self.data_address_00000008)
        print("0x00000009: ", self.data_address_00000009)

        # # Convert from Unicode hexadecimals to integers:
        # self.data_address_00000000 = int(data_address_00000000, 16)
        # self.data_address_00000001 = int(data_address_00000001, 16)
        # self.data_address_00000002 = int(data_address_00000002, 16)
        # self.data_address_00000006 = int(data_address_00000006, 16)
        # self.data_address_00000007 = int(data_address_00000007, 16)
        # self.data_address_00000008 = int(data_address_00000008, 16)
        # self.data_address_00000009 = int(data_address_00000009, 16)

        self.change_udp_register_value("0x00000000", self.data_address_00000000)
        self.change_udp_register_value("0x00000001", self.data_address_00000001)
        self.change_udp_register_value("0x00000002", self.data_address_00000002)
        self.change_udp_register_value("0x00000006", self.data_address_00000006)
        self.change_udp_register_value("0x00000007", self.data_address_00000007)
        self.change_udp_register_value("0x00000008", self.data_address_00000008)
        self.change_udp_register_value("0x00000009", self.data_address_00000009)

        try:
            self.qemcamera.disconnect()
        except socket_error as e:
            print("ERROR disconnecting camera: %s" % e)

    def turn_decimal_list_into_hexadecimal_list(self, token_list):
        """Turn a list of decimal Unicode strings into a list of hexadecimal strings.

        I.e. [u'10', u'5', u'3', u'2'] Becomes ['0a', '05', '03', '02']
        """
        new_list = []
        for element in token_list:
            token = int(element)
            token = format(token, '#04x')
            new_list.append(token[2:])
        return new_list

    def turn_unicode_list_into_string_list(self, token_list):
        """Turn a list of Unicode strings into a list of hexadecimal strings."""
        new_list = []
        for element in token_list:
            new_list.append(format(int(element, 16), '#04x')[2:])
        return new_list

    def change_udp_register_value(self, register, value):
        """Set register to value.

        Simple script used to update UDP register values, targeting
        0x00000000 - Data
        0x10000000 - Control
        """
        register = int(register, 16)
        value = int(value, 16)

        try:
            self.qemcamera.x10g_rdma.write(register, value, 'N/A')
            print(" Updated register %s to value: %s " % (format(register, '#010x'), format(value, '#010x')))
        except socket_error as e:
            print("ERROR updating register: %s: %s" % (format(register, '#010x'), e))


if __name__ == '__main__':
    try:
        q = set_udp_registers(sys.argv[1], sys.argv[2])
        q.read_ip_settings()
    except IndexError:
        print("Usage:")
        print("set_udp_registers.py <json_file> <fem_id>")
        print("such as:")
        print("set_udp_registers.py /path/to/control/src/hexitec/test_ui/fem_addresses.json 0")
