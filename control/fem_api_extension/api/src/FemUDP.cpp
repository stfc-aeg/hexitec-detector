/*
 * FemRdma.cpp
 *
 *  Created on: Mar 13, 2012
 *      Author: gm
 */

#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <ifaddrs.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <netinet/in.h>
#include <string.h>

#include "FemLogger.h"
#include "FemClient.h"

#define IP_FLAG_FRAG 0x00
#define IP_TIME_TO_LIVE 0x80
#define IP_PROTOCOL_UDP 0x11
#define IP_IDENT_COUNT 0xDB00
#define IP_PKT_LENGTH_BASE 0x1c
#define UDP_LENGTH_BASE 0x0008
#define PACKET_SPLIT_SIZE 0x3e6
#define INT_PKT_GAP_VAL 0x800

#define INT_PKT_GAP_EN 0x11
#define DEBUG_MODE_EN  0x2
#define DEBUG_MODE_STEP 0x4
#define FXD_PKT_SZE	0x8

const u32 kTenGigUdpRdmaAddr = 0x00000000;
const u32 kTenGigUdpFarmModePortTable = kTenGigUdpRdmaAddr + 0x10000;
const u32 kTenGigUdpFarmModeIpTable   = kTenGigUdpRdmaAddr + 0x10100;
const u32 kTenGigUdpFarmModeMacTable  = kTenGigUdpRdmaAddr + 0x10200;

const unsigned int kFarmModeLutSize = 256;

/** configUDP - configure the FEM X10G UDP block
 *
 */
u32 FemClient::configUDP(
    const std::string sourceMacAddress, const std::string sourceIpAddress, const u32 sourcePort,
    const std::string destMacAddress[], const std::string destIpAddress[], const u32 destPort[],
    const u32 destPortOffset, const u32 num_lut_entries, const bool farmModeEnabled
)
{
  u32 core_rc, farm_rc;

  core_rc = this->configUDPCoreReg(
      sourceMacAddress.c_str(), sourceIpAddress.c_str(), sourcePort,
      destMacAddress[0].c_str(), destIpAddress[0].c_str(), destPort[0] + destPortOffset
  );
  if (core_rc != 0) {
   return core_rc;
  }

  farm_rc = this->configUDPFarmMode(destMacAddress, destIpAddress, destPort, destPortOffset,
                                    num_lut_entries, farmModeEnabled);

  return farm_rc;
}

/** configUDP - configure the core registers of the FEM X10G UDP block
 *
 * @param fpgaMACaddress string representation of an IP address in dotted quad format
 * @param fpgaIPaddress string representation of an IP address in dotted quad format
 * @param fpgaPort integer containing the port number of the FEM fpga
 * @param hostIPaddress string representation of an IP address in dotted quad format
 * @param hostPort integer containing the port number of the host PC
 * @return 0 if success else -1
 */
u32 FemClient::configUDPCoreReg(
    const char* fpgaMACaddress, const char* fpgaIPaddress, const u32 fpgaPort,
    const char* hostMACaddress, const char* hostIPaddress, const u32 hostPort)
{

  int rc = 0;
  u_int32_t value;

  unsigned char hostMAC[6];
  unsigned char fpgaMAC[6];
  unsigned char fpgaIP[4];
  unsigned char hostIP[4];

  try
  {

    to_bytes(hostMACaddress, hostMAC, 6, 16);
    to_bytes(fpgaMACaddress, fpgaMAC, 6, 16);
    to_bytes(fpgaIPaddress, fpgaIP, 4, 10);
    to_bytes(hostIPaddress, hostIP, 4, 10);

    value = (fpgaMAC[3] << 24) + (fpgaMAC[2] << 16) + (fpgaMAC[1] << 8) + fpgaMAC[0];
    this->rdmaWrite(kTenGigUdpRdmaAddr + 0, value); // UDP Block 0 MAC Source Lower 32

    value = (hostMAC[1] << 24) + (hostMAC[0] << 16) + (fpgaMAC[5] << 8) + (fpgaMAC[4]);
    this->rdmaWrite(kTenGigUdpRdmaAddr + 1, value); // UDP Block 0 MAC Source Upper 16/Dest Lower 16

    value = (hostMAC[5] << 24) + (hostMAC[4] << 16) + (hostMAC[3] << 8) + hostMAC[2];
    this->rdmaWrite(kTenGigUdpRdmaAddr + 2, value); // UDP Block 0 MAC Dest Upper 32

    value = (IP_IDENT_COUNT << 16) + IP_PKT_LENGTH_BASE;
    this->rdmaWrite(kTenGigUdpRdmaAddr + 4, value); // UDP Block 0 IP Ident / Header Length

    value = (IP_PROTOCOL_UDP << 24) + (IP_TIME_TO_LIVE << 16) + IP_FLAG_FRAG;
    this->rdmaWrite(kTenGigUdpRdmaAddr + 5, value); // UDP protocol, TTL, flags & fragment count

    value = (hostIP[1] << 24) + (hostIP[0] << 16) + (0xDE << 8) + 0xAD;
    this->rdmaWrite(kTenGigUdpRdmaAddr + 6, value); // UDP Block 0 IP Dest Addr / Checksum

    value = (fpgaIP[1] << 24) + (fpgaIP[0] << 16) + (hostIP[3] << 8) + hostIP[2];
    this->rdmaWrite(kTenGigUdpRdmaAddr + 7, value); // UDP Block 0 IP Src Addr / Dest Addr

    value = ((fpgaPort & 0xff) << 24) + ((fpgaPort & 0xff00) << 8) + (fpgaIP[3] << 8) + fpgaIP[2];
    this->rdmaWrite(kTenGigUdpRdmaAddr + 8, value); // UDP Block 0 IP Src Port / Src Addr

    value = (UDP_LENGTH_BASE << 16) + ((hostPort & 0xff) << 8) + (hostPort >> 8);
    this->rdmaWrite(kTenGigUdpRdmaAddr + 9, value); // UDP Block 0 UDP Length / Dest Port

    value = PACKET_SPLIT_SIZE;
    this->rdmaWrite(kTenGigUdpRdmaAddr + 0xC, value); // UDP Block 0 Packet Size

    value = INT_PKT_GAP_VAL;
    this->rdmaWrite(kTenGigUdpRdmaAddr + 0xD, value); // UDP Block 0 IFG Value

    uint32_t mode_reg = this->rdmaRead(kTenGigUdpRdmaAddr + 0xF);
    mode_reg |= INT_PKT_GAP_EN;
    this->rdmaWrite(kTenGigUdpRdmaAddr + 0xF, mode_reg); // UDP Block 0 IFG Enable

  }
  catch (FemClientException& e)
  {
    FEMLOG(mFemId, logERROR) << "Exception caught during configUDP: " << e.what();
    rc = -1;
  }
  return rc;
}

u32 FemClient::configUDPFarmMode
(
    const std::string destMacAddress[], const std::string destIpAddress[],
    const u32 destPort[], const u32 destPortOffset, u32 num_lut_entries, const bool farmModeEnabled
)
{
  u32 rc = 0;
  std::vector<u32> ip_regs;
  std::vector<u32> mac_regs;
  std::vector<u32> port_regs;

  // Extract and parse the farm mode destination MAC, IP and port settings, limiting
  // to valid entries only. Pack the parsed values into vectors to be loaded into
  // the appropriate RDMA registers
  for (unsigned int idx = 0; idx < num_lut_entries; idx++)
  {

    FEMLOG(mFemId, logDEBUG) << "LUT table entry " << idx << " :  IP:" << destIpAddress[idx]
              << " MAC:" << destMacAddress[idx]
              << " port:" << destPort[idx] + destPortOffset;

    ip_regs.push_back(farmIpRegFromStr(destIpAddress[idx]));
    std::vector<u32> mac_reg_vals = farmMacRegFromStr(destMacAddress[idx]);
    mac_regs.insert(mac_regs.end(), mac_reg_vals.begin(), mac_reg_vals.end());
    port_regs.push_back(destPort[idx] + destPortOffset);
  }

  // Write the port, IP and MAC settings into the appropriate RDMA registers
  this->rdmaWrite(kTenGigUdpFarmModePortTable, port_regs);
  this->rdmaWrite(kTenGigUdpFarmModeIpTable, ip_regs);
  this->rdmaWrite(kTenGigUdpFarmModeMacTable, mac_regs);

  // Set the LUT location register to point to the location in the LocalLink header where the
  // farm mode LUT index is located
  this->rdmaWrite(kTenGigUdpRdmaAddr + 0xA, 1);

  // Modify the farm mode enable bit in the register as appropriate
  FEMLOG(mFemId, logDEBUG) << "Setting UDP farm mode to " << (farmModeEnabled ? "enabled" : "disabled");
  u32 mode_reg = this->rdmaRead(kTenGigUdpRdmaAddr + 0xF);
  mode_reg = (farmModeEnabled ? (mode_reg | (1 << 5)) : (mode_reg & ~(1<<5)));
  this->rdmaWrite(kTenGigUdpRdmaAddr + 0xF, mode_reg);

  return rc;
}

void FemClient::to_bytes(const char *ipName, unsigned char* b, int n, int base)
{
  char *end;
  const char* iptr = ipName;
  for (int i = 0; i < n; i++)
  {
    b[i] = (unsigned char) strtol(iptr, &end, base);
    iptr = end + 1;
  }
}

u32 FemClient::farmIpRegFromStr(std::string ip_str)
{
  std::string octet;
  std::istringstream octet_stream(ip_str);
  u32 ip_reg = 0;

  while (std::getline(octet_stream, octet, '.'))
  {
    char *end;
    ip_reg = (ip_reg << 8) | ((strtol(octet.c_str(), &end, 10)) & 0xFF);
  }

  return ip_reg;
}

std::vector<u32> FemClient::farmMacRegFromStr(std::string mac_str)
{
  std::string octet;
  std::istringstream octet_stream(mac_str);
  u32 reg_val = 0;
  std::vector<u32> mac_reg;

  unsigned int octet_count = 0;
  while (std::getline(octet_stream, octet, ':'))
  {
    char *end;
    reg_val = (reg_val << 8) | ((strtol(octet.c_str(), &end, 16)) & 0xFF);
    if (++octet_count == 2) {
      mac_reg.insert(mac_reg.begin(), reg_val);
      reg_val = 0;
    }
  }
  mac_reg.insert(mac_reg.begin(), reg_val);

  return mac_reg;

}

/** getMacAddressFromIP - get the MAC address corresponding to the given IP address
 *
 * @param ipAddress string representation of an IP address in dotted quad format
 * @param ip byte array containing the IP address
 * @return the mac address of the interface as a byte array or NULL if not found
 */
int FemClient::getMacAddressFromIP(const char *ipName, char* mac_str)
{

  struct ifaddrs *ifaddr, *ifa;
  int family, s;
  char host[NI_MAXHOST];
  struct sockaddr *sdl;
  unsigned char *ptr;
  char *ifa_name = NULL;
  unsigned char* mac_addr = (unsigned char*) calloc(sizeof(unsigned char), 6);

  if (getifaddrs(&ifaddr) == -1)
  {
    return -1;
  }

  //iterate to find interface name for given server_ip
  for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next)
  {
    if (ifa->ifa_addr != NULL)
    {
      family = ifa->ifa_addr->sa_family;
      if (family == AF_INET)
      {
        s = getnameinfo(
            ifa->ifa_addr,
            (family == AF_INET) ? sizeof(struct sockaddr_in) : sizeof(struct sockaddr_in6), host,
            NI_MAXHOST,
            NULL, 0, NI_NUMERICHOST);
        if (s != 0)
        {
          return -1;
        }
        if (strcmp(host, ipName) == 0)
        {
          ifa_name = ifa->ifa_name;
        }
      }
    }
  }
  if (ifa_name == NULL)
  {
    return -1;
  }

  int i;
  //iterate to find corresponding MAC address
  for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next)
  {
    family = ifa->ifa_addr->sa_family;
    if (family == PF_PACKET && strcmp(ifa_name, ifa->ifa_name) == 0)
    {
      sdl = (struct sockaddr *) (ifa->ifa_addr);
      ptr = (unsigned char *) sdl->sa_data;
      ptr += 10;
      for (i = 0; i < 6; i++)
      {
        mac_addr[i] = *ptr++;
      }
      break;
    }
  }
  freeifaddrs(ifaddr);

  sprintf(mac_str, "%02x:%02x:%02x:%02x:%02x:%02x", mac_addr[0], mac_addr[1], mac_addr[2],
          mac_addr[3], mac_addr[4], mac_addr[5]);

  return 0;
}

char* FemClient::getFpgaIpAddressFromHost(const char *ipAddr)
{

  struct in_addr addr;
  if (inet_aton(ipAddr, &addr) == 0)
  {
    FEMLOG(mFemId, logERROR) << "Invalid address: " << ipAddr;
    return NULL;
  }
  addr.s_addr += 1 << 24;
  return inet_ntoa(addr);

}
