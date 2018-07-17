/*
 * FemClient.h - header file definition of FemClient class
 *
 *  Created on: Sep 15, 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef FEMCLIENT_H_
#define FEMCLIENT_H_

#include <boost/asio.hpp>
#include <boost/bind.hpp>
#include <boost/thread.hpp>
#include <boost/asio/io_service.hpp>
#include <boost/asio/deadline_timer.hpp>
#include "FemTransaction.h"
#include "FemException.h"
#include "FemClientAcquisition.h"

using boost::asio::ip::tcp;

/** FemClient::error - error codes returned by FemClient methods, typically
 *  embodied in a thrown FemClientException. The specific FemClient errors
 *  in the enumeration are indexed from 10000, to allow standard errno and
 *  boost ASIO error codes to be used also.
 */
typedef enum
{
  femClientOK = 0,                    ///< OK
  femClientDisconnected = 10000,      ///< Client disconnected by peer
  femClientTimeout,                   ///< Timeout occurred on a socket operation
  femClientResponseMismatch,           ///< Mismatch between requested command and response
  femClientMissingAck,                ///< Transaction command was not acknowledged in reponse
  femClientSendMismatch,              ///< Mismatch in length of send operation
  femClientReadMismatch,       ///< Mismatch in requested versus received access in read transaction
  femClientWriteMismatch, ///< Mismatch in requested versus acknowledged access in write transaction
  femClientIllegalSensor,             ///< Illegal sensor specified in tempSensorRead call
  femClientNextEnumRange = 20000      ///< Next enum range to use for derived class exceptions
} FemClientErrorCode;

typedef enum
{
  femBoardTemp = 0, femFpgaTemp
} FemTemperatureSensor;

class FemClientException : public FemException
{
public:
  FemClientException(const std::string aExText) :
      FemException(aExText)
  {
  }
  ;
  FemClientException(const FemClientErrorCode aExCode, const std::string aExText) :
      FemException((FemErrorCode) aExCode, aExText)
  {
  }
  ;
};

class FemClient
{

public:

  FemClient(const int femId, const char* aHostString, int aPortNum, unsigned int aTimeoutInMsecs = 0);
  virtual ~FemClient();

  void setTimeout(unsigned int aTimeoutInMsecs);
  void setTimeout(float aTimeoutInSecs);

  std::vector<u8> read(unsigned int aBus, unsigned int aWidth, unsigned int aAddress,
      unsigned int aLength);
  u32 write(unsigned int aBus, unsigned int aWidth, unsigned int aAddress,
      std::vector<u8>& aPayload);
  // added for zero copy
  u32 readNoCopy(unsigned int aBus, unsigned int aWidth, unsigned int aAddress, std::size_t aLength,
      u8* aPayload);
  u32 write(unsigned int aBus, unsigned int aWidth, unsigned int aAddress, u8* aPayload,
      std::size_t size);
  std::size_t send(std::vector<u8> encoded);
  FemTransaction receive(u8* payload);

  // end of added for zero copy

  virtual void command(unsigned int command);
  std::vector<u8> commandAcquire(unsigned int aAcqCommand, FemAcquireConfiguration* apConfig = 0);

  std::size_t send(FemTransaction aTrans);
  FemTransaction receive(void);

  // Bus-level transactions, implemented in femClientBusses.cpp
  std::vector<u8> i2cRead(unsigned int aAddress, unsigned int aLength);
  u32 i2cWrite(unsigned int aAddress, std::vector<u8>&aValues);
  std::vector<u8> rdmaRead(unsigned int aAddress, unsigned int aLength);
  u32 rdmaRead(unsigned int aAddress);
  u32 rdmaWrite(unsigned int aAddress, std::vector<u8>& aPayload);
  u32 rdmaWrite(unsigned int aAddress, std::vector<u32>& aPayload);
  void rdmaWrite(u32 address, u32 value);
  u32 spiWrite(unsigned int aAddress, std::vector<u8>& aPayload);
  std::vector<u8> spiRead(unsigned int aAddress, unsigned int aLength);
  u32 memoryWrite(unsigned int aAddress, u32* apPayload, unsigned int aLength);
  u32 memoryWrite(unsigned int aAddress, u8* apPayload, unsigned int aLength);

  // High-level FEM client functions, implemented in femClientHighLevel.cpp
  double tempSensorRead(FemTemperatureSensor aSensor);

  // Acquisition control functions implemented in FemClientAcquisition.cpp
  void acquireConfig(u32 aAcqMode, u32 aBufferSize, u32 aBufferCount, u32 aNumAcq, u32 aBdCoalesce);
  void acquireStart(void);
  void acquireStop(void);
  FemAcquireStatus acquireStatus(void);

  void runIoService(void); // test function

  u32 configUDP(
      const std::string sourceMacAddress, const std::string sourceIpAddress, const u32 sourcePort,
      const std::string destMacAddress[], const std::string destIpAddress[], const u32 destPort[],
      const u32 destPortOffset, const u32 num_lut_entries, const bool farmModeEnabled
  );
  char* getFpgaIpAddressFromHost(const char* ipAddr);
  int getMacAddressFromIP(const char *ipName, char* mac_str);

  u32 personalityWrite(unsigned int aCommand, unsigned int aWidth, u8* aPayload, std::size_t size);
  FemTransaction personalityCommand(unsigned int aCommand, unsigned int aWidth, u8* aPayload,
      std::size_t size);

protected:

  int mFemId; // FEM identifier

private:

  boost::asio::io_service mIoService; ///< Boost asio IO service
  tcp::endpoint mEndpoint;  ///< Boost asio TCP endpoint
  tcp::socket mSocket;    ///< Client connection socket
  boost::asio::deadline_timer mDeadline;  ///< Internal timeout deadline timer
  unsigned int mTimeout;   ///< timeout in milliseconds

  std::size_t receivePart(std::vector<u8>& aBuffer, boost::system::error_code& aError);
  void checkDeadline(void);
  static void asyncConnectHandler(const boost::system::error_code& ec,
      boost::system::error_code* apOutputErrorCode);
  static void asyncCompletionHandler(const boost::system::error_code& aErrorCode,
      std::size_t aLength, boost::system::error_code* apOutputErrorCode,
      std::size_t* apOutputLength);

  u32 configUDPCoreReg(const char* fpgaMACaddress, const char* fpgaIPaddress, u32 fpgaPort,
      const char* hostMACaddress, const char* hostIPaddress, u32 hostPort);
  u32 configUDPFarmMode(const std::string destMacAddress[], const std::string destIpAddress[],
      const u32 destPort[], const u32 destPortOffset, u32 numDestinations,
      const bool farmModeEnabled);

  void to_bytes(const char *ipName, unsigned char* b, int n, int base = 10);
  u32 farmIpRegFromStr(std::string ip_str);
  std::vector<u32> farmMacRegFromStr(std::string mac_str);
};

#endif /* FEMCLIENT_H_ */
