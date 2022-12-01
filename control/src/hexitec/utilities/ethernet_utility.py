"""
Some tool(s) for obtaining Ethernet card information.

Christian Angelsen, STFC Detector Systems Software Group
"""

from __future__ import print_function

import socket
import sys
import os
import re


class EthernetUtility():
    """Obtain NIC information from /sbin/ifconfig utility."""

    def __init__(self, interface="eth0"):
        """Extract NIC information."""
        self.interface = interface
        self.macAddress = ""
        self.ipAddress = ""
        self.ifconfig_data = os.popen("/sbin/ifconfig %s" % self.interface)
        try:
            for line in self.ifconfig_data.readlines():
                if 'ether' in line:
                    self.macLine = line
                if 'inet ' in line:
                    self.ipLine = line
        except Exception as e:
            print("EthernetUtility error: ", e)
        self.ifconfig_data.close()

    def macAddressGet(self):
        """Get MAC Address (from ifconfig command)."""
        self.macAddress = None
        try:
            mac = re.compile(r'ether (\w+\:\w+\:\w+\:\w+\:\w+\:\w+)')
            self.macAddress = mac.search(self.macLine).group(1)
        except IOError as e:
            (errno, strerror) = e.args
            print("MAC Address IO Error(%s): %s" % (errno, strerror))
        except AttributeError:
            print("Error extracting MAC address")
        else:
            # Replace ':' in MAC address with '' (i.e. nothing)
            self.macAddress = self.macAddress.replace(":", "")
        return self.macAddress

    def ipAddressGet(self):
        """Get IP Address (from ifconfig command)."""
        self.ipAddress = None
        try:
            address = re.compile(r'inet (\d+\.\d+\.\d+\.\d+)')
            self.ipAddress = address.search(self.ipLine).group(1)
        except AttributeError:
            print("EthernetUtility: Unable to extract IP address")
        except IOError as e:
            (errno, strerror) = e.args
            print("IP Address IO Error(%s): %s" % (errno, strerror))
        return self.ipAddress


if __name__ == '__main__':

    try:
        ethCard = EthernetUtility(sys.argv[1])

        print("In ethernet interface: %s" % ethCard.interface)
        mac = ethCard.macAddressGet()
        srcIp = ethCard.ipAddressGet()
        print("Src MAC: %r (%r)" % (mac, type(mac)))
        print("Src IP:  %r (%r)" % (srcIp, type(srcIp)))
        print("  Matching MR's format:")
        print(" 0x2000C 0x{}".format(mac[4:].upper().zfill(8)))
        print(" 0x20010 0x{}".format(mac[:4].upper().zfill(8)))
        ip = socket.inet_aton(srcIp).hex().upper()
        print(" 0x20024 0x{}".format(ip))
    except IndexError:
        print("Valid syntax: python3 te7wendolene_utility.py <NIC>")
        print("e.g. python3 te7wendolene_utility.py eth0")
