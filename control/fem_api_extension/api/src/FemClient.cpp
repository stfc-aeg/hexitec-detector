/*
 * FemClient.cpp - implementation of the FemClient class
 *
 *  Created on: Sep 15, 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "FemClient.h"
#include "FemLogger.h"
#include <iostream>
#include <sstream>

/** Constructor - initialises client connection to a FEM
 * @param aHostString string representation of FEM IP address in dotted quad format
 * @param aPortNum integer port number to connect to
 * @param aTimeoutInMsecs transaction timeout in milliseconds (defaults to zero, i.e. no timeout)
 * @return FemClient instance, connected to FEM
 */
FemClient::FemClient(const int femId, const char* aHostString, int aPortNum, unsigned int aTimeoutInMsecs) :
    mFemId(femId),
    mEndpoint(boost::asio::ip::address::from_string(aHostString), aPortNum),
    mSocket(mIoService),
    mDeadline(mIoService),
    mTimeout(aTimeoutInMsecs)
{

  // Initialise deadline timer to positive infinity so that no action will be taken until
  // a deadline is set
  mDeadline.expires_at(boost::posix_time::pos_infin);

  // Start the persistent deadline actor that checks for deadline expiry
  checkDeadline();

  // Attempt to connect to the FEM, catching and rethrowing any exception that occur
  try
  {

#ifdef SYNC_CONNNECT

    mSocket.connect(mEndpoint);

#else

    // If a client timeout is specified, set the deadline timer appropriately
    if (mTimeout > 0)
    {
      mDeadline.expires_from_now(boost::posix_time::milliseconds(mTimeout));
    }

    // Set error code to would_block as async operations guarantee not to set this value
    boost::system::error_code error = boost::asio::error::would_block;

    // Start the asynchronous connection attempt, which will call the appropriate handler
    // on completion
    mSocket.async_connect(mEndpoint, boost::bind(&FemClient::asyncConnectHandler, _1, &error));

    // Run the IO service and block until the connection handler completes
    do
    {
      mIoService.run_one();
    }
    while (error == boost::asio::error::would_block);

    // If the deadline timer has been called and cancelled the socket operation before
    // the connection established, a timeout has occurred
    if (error == boost::asio::error::operation_aborted)
    {
      mSocket.close();
      throw FemClientException(femClientTimeout, "Timeout establishing client connection");
    }
    // If another error occurred during connect - throw an exception
    else if (error)
    {
      mSocket.close();
      throw FemClientException((FemClientErrorCode) error.value(), error.message());

    }
#endif

  }
  catch (boost::system::system_error& e)
  {
    boost::system::error_code ec = e.code();
    const char* what = e.what();
    throw FemClientException((FemClientErrorCode) ec.value(), what);
  }
}

/** Destructor - destroys client connection to a FEM, closing socket connection cleanly
 */
FemClient::~FemClient()
{

  try
  {
    mSocket.close();
  }
  catch (boost::system::system_error& e)
  {
    FEMLOG(mFemId, logERROR) << "Exception caught closing FemClient connection: " << e.what();
    // Do nothing else, just catch the exception so it doesn't propagate out of the destructor
  }
}

/** setTimeout - sets FEM client timeout in milliseconds
 *
 * This function sets the FEM client timeout to a value specified in milliseconds.
 * Setting the timeout to zero disables the timeout so that client operations will
 * block indefinitely.
 *
 * @param aTimeoutInMsecs unsigned int timeout in milliseconds (0 = no timeout)
 */
void FemClient::setTimeout(unsigned int aTimeoutInMsecs)
{
  // Set timeout value
  mTimeout = aTimeoutInMsecs;
}

/** setTimeout - sets FEM client timeout in seconds
 *
 *  This function sets the FEM client timeout to a floating point value in seconds
 *  down to a precision of milliseconds, which is how the underlying deadline timer
 *  is configured. Setting the timeout to zero disables the timeout so that client
 *  operations will block indefinitely.
 *
 *  @param aTimeoutInSecs floating point timeout in seconds (0 = no timeout)
 */
void FemClient::setTimeout(float aTimeoutInSecs)
{
  // Convert timeout value to millseconds and set
  mTimeout = (unsigned int) (aTimeoutInSecs * 1000);
}

/** read - execute a read transaction on the connected FEM
 *
 * This function executes a read transaction on the connected FEM, returning the
 * read values decoded from the transaction response. The returned vector should
 * be decoded to the appropriate type according to the width specified.
 *
 * @param aBus FEM bus to write to
 * @param aWidth width of each write (byte, word, long)
 * @param aAddress address of first write transaction
 * @param aLength number of reads to successive addresses to perform
 * @return vector of read results as byte stream

 */
std::vector<u8> FemClient::read(unsigned int aBus, unsigned int aWidth, unsigned int aAddress,
    unsigned int aLength)
{

  // Create a read transaction based on the specified bus, width, address and length parameters
  u8 state = 0;
  SBIT(state, STATE_READ);
  FemTransaction request(CMD_ACCESS, aBus, aWidth, state, aAddress);
  u32 payload[] =
    { aLength };
  request.appendPayload((u8*) payload, sizeof(payload));

  // Send the request transaction
  this->send(request);

  // Receive the response and get the payload
  FemTransaction response = this->receive();
  std::vector<u8> readPayload = response.getPayload();

  // Check for an ACK and the absence of a NACK on the response
  u8 responseState = response.getState();
  if (!(CMPBIT(responseState, STATE_ACK)) || (CMPBIT(responseState, STATE_NACK)))
  {
    std::ostringstream msg;
    msg << "FEM read transaction to address 0x" << std::hex << aAddress << std::dec << " failed: "
        << response.getErrorString() << " (errno=" << response.getErrorNum() << ")";
    throw FemClientException(femClientMissingAck, msg.str());
  }

  // First word of payload should match the read length parameter requested. If it doesn't
  // return an exception
  u32 responseReadLen = (u32) (readPayload[0]);
  if (responseReadLen != aLength)
  {
    std::ostringstream msg;
    msg << "Length mismatch when reading: requested " << aLength << " got " << responseReadLen;
    throw FemClientException(femClientReadMismatch, msg.str());

  }

  // Erase the read length off the head of the payload
  readPayload.erase(readPayload.begin(), readPayload.begin() + 4);

  // Return the read values
  return readPayload;

}

/** read - execute a read transaction on the connected FEM
 *
 * This function executes a read transaction on the connected FEM, returning the
 * read values decoded from the transaction response. The returned vector should
 * be decoded to the appropriate type according to the width specified.
 *
 * @param aBus FEM bus to write to
 * @param aWidth width of each write (byte, word, long)
 * @param aAddress address of first write transaction
 * @param aLength number of reads to successive addresses to perform
 * @return vector of read results as byte stream

 */
u32 FemClient::readNoCopy(unsigned int aBus, unsigned int aWidth, unsigned int aAddress,
    std::size_t aLength, u8* aPayload)
{

  // Create a read transaction based on the specified bus, width, address and length parameters
  u8 state = 0;
  SBIT(state, STATE_READ);
  u32 payload[] =
    { aLength };
  FemTransaction request(CMD_ACCESS, aBus, aWidth, state, aAddress, (u8*) payload,
                         sizeof(u_int32_t));

  // Send the request transaction
  this->send(request.encodeArray());

  // Receive the response and get the payload
  FemTransaction response = this->receive(aPayload);

  // Check for an ACK and the absence of a NACK on the response
  u8 responseState = response.getState();
  if (!(CMPBIT(responseState, STATE_ACK)) || (CMPBIT(responseState, STATE_NACK)))
  {
    std::ostringstream msg;
    msg << "FEM read transaction to address 0x" << std::hex << aAddress << std::dec << " failed: "
        << response.getErrorString() << " (errno=" << response.getErrorNum() << ")";
    throw FemClientException(femClientMissingAck, msg.str());
  }

  // Read length parameter requested. If it doesn't return an exception
  u32 responseReadLen = response.payloadLength();
  if (responseReadLen != aLength)
  {
    std::ostringstream msg;
    msg << "Length mismatch when reading: requested " << aLength << " got " << responseReadLen;
    throw FemClientException(femClientReadMismatch, msg.str());

  }
  return response.payloadLength();
}

/** write - execute a write transaction on the connected FEM
 *
 * This function executes a write transaction on the connected FEM. The response
 * is checked to ensure that the number of writes performed by the FEM matches
 * the number requested, otherwise a femClientWriteMismatch exception is thrown
 *
 * @param aBus FEM bus to write to
 * @param aWidth width of each write (byte, word, long)
 * @param aAddress address of first write transaction
 * @param aPayload vector of writes of appropriate width
 * @return number of writes completed in transaction
 */
u32 FemClient::write(unsigned int aBus, unsigned int aWidth, unsigned int aAddress,
    std::vector<u8>& aPayload)
{

  // Create a write transaction based on the specified bus, width, address and payload
  // parameters.
  u8 state = 0;
  SBIT(state, STATE_WRITE);
  FemTransaction request(CMD_ACCESS, aBus, aWidth, state, aAddress);

  // Append write payload
  request.appendPayload((u8*) &(aPayload[0]), aPayload.size());

  // Send the write transaction
  this->send(request);

  // Receive the response
  FemTransaction response = this->receive();

  // Check for an ACK and the absence of a NACK on the response
  u8 responseState = response.getState();
  if (!(CMPBIT(responseState, STATE_ACK)) || (CMPBIT(responseState, STATE_NACK)))
  {
    std::ostringstream msg;
    msg << "FEM write transaction to address 0x" << std::hex << aAddress << std::dec << " failed: "
        << response.getErrorString() << " (errno=" << response.getErrorNum() << ")";
    throw FemClientException(femClientMissingAck, msg.str());
  }

  // The payload of the response to a write transaction should be a single
  // 32bit word indicating the number of write access completed. This should
  // match the number specified in the request.
  std::vector<u8> respPayload = response.getPayload();
  u32 responseWriteLen = (u32) *(u32*) &(respPayload[0]);

  u32 numWrites = aPayload.size() / FemTransaction::widthToSize(aWidth);
  if (responseWriteLen != numWrites)
  {
    std::ostringstream msg;
    msg << "Length mismatch during FEM write transaction: requested=" << numWrites << " responded="
        << responseWriteLen;
    throw FemClientException(femClientWriteMismatch, msg.str());
  }

  return responseWriteLen;
}

/** write - execute a write transaction on the connected FEM
 *
 * This function executes a write transaction on the connected FEM. The response
 * is checked to ensure that the number of writes performed by the FEM matches
 * the number requested, otherwise a femClientWriteMismatch exception is thrown
 *
 * @param aBus FEM bus to write to
 * @param aWidth width of each write (byte, word, long)
 * @param aAddress address of first write transaction
 * @param aPayload vector of writes of appropriate width
 * @return number of writes completed in transaction
 */
u32 FemClient::write(unsigned int aBus, unsigned int aWidth, unsigned int aAddress, u8* aPayload,
    std::size_t size)
{

  // Create a write transaction based on the specified bus, width, address and payload
  // parameters.
  u8 state = 0;
  SBIT(state, STATE_WRITE);
  FemTransaction request(CMD_ACCESS, aBus, aWidth, state, aAddress, aPayload, size);

  // Send the encoded write transaction
  this->send(request.encodeArray());

  // Receive the response
  u32 payload[] =
    { 0 };
  FemTransaction response = this->receive((u8*) payload);

  // Check for an ACK and the absence of a NACK on the response
  u8 responseState = response.getState();

  if (!(CMPBIT(responseState, STATE_ACK)) || (CMPBIT(responseState, STATE_NACK)))
  {
    std::ostringstream msg;
    msg << "FEM write transaction to address 0x" << std::hex << aAddress << std::dec << " failed: "
        << response.getErrorString() << " (errno=" << response.getErrorNum() << ")";
    throw FemClientException(femClientMissingAck, msg.str());
  }

  // The payload of the response to a write transaction should be a single
  // 32bit word indicating the number of write access completed. This should
  // match the number specified in the request.
  u32 responseWriteLen = response.payloadLength();

  u32 numWrites = size / FemTransaction::widthToSize(aWidth);
  if (responseWriteLen != numWrites)
  {
    std::ostringstream msg;
    msg << "Length mismatch during FEM write transaction: requested=" << numWrites << " responded="
        << responseWriteLen;
    throw FemClientException(femClientWriteMismatch, msg.str());
  }

  return responseWriteLen;
}

/** command - send a command transaction to the connected FEM
 *
 * This function encodes and transmits a command transaction to the connected FEM. The
 * repsonse is checked to ensure that the command is acknowledged. Error conditions
 * are signalled by thrown FemClientExceptions as appropriate. The operation will time out
 * according to the current timeout value.
 *
 * @param aCommand the FEM command to be sent
 */
void FemClient::command(unsigned int aCommand)
{

  // Create a command transaction based on the specified command. The command is passed in the
  // address field of the transaction header. Since there is no payload, the tranasaction
  // payload width is set to an arbitrary value.
  FemTransaction request(CMD_INTERNAL, 0, WIDTH_BYTE, 0, aCommand);

  // Send the command transaction
  this->send(request);

  // Receive the response
  FemTransaction response = this->receive();

  // Check that the response is an ACK of the correct command
  u8 responseCmd = response.getCommand();
  if (responseCmd != CMD_INTERNAL)
  {
    std::ostringstream msg;
    msg << "Mismatched command type in FEM response. Sent cmd: " << (unsigned int) CMD_INTERNAL
        << " recvd: " << (unsigned int) responseCmd;
    throw FemClientException(femClientResponseMismatch, msg.str());
  }

  u8 responseState = response.getState();
  if (!(CMPBIT(responseState, STATE_ACK)) || (CMPBIT(responseState, STATE_NACK)))
  {
    std::ostringstream msg;
    msg << "Command " << aCommand << " failed: " << response.getErrorString() << " (errno="
        << response.getErrorNum() << ")";
    throw FemClientException(femClientMissingAck, msg.str());
  }

  u32 responseAddr = response.getAddress();
  if (responseAddr != aCommand)
  {
    std::ostringstream msg;
    msg << "Mismached internal command in FEM response. Sent: " << aCommand << " recvd: "
        << responseAddr;
    throw FemClientException(femClientResponseMismatch, msg.str());
  }
}

/** commandAcquire - send an acquire command transaction to the connected FEM
 *
 * This function encodes and transmits an aquire command transaction to the connected FEM, to set
 * up the acquisition sequencing within the memory controller. The
 * repsonse is checked to ensure that the command is acknowledged. Error conditions
 * are signalled by thrown FemClientExceptions as appropriate. The operation will time out
 * according to the current timeout value.
 *
 * @param aAcqCommand the FEM command to be sent
 * @param apConfig pointer to protocol_acq_config structure to be sent as payload if any
 */
std::vector<u8> FemClient::commandAcquire(unsigned int aAcqCommand,
    FemAcquireConfiguration* apConfig)
{

  // Create an acquire command transaction based on the specified command and config structure.
  // If this command requires no config payload, set the size to zero
  FemTransaction request(CMD_ACQUIRE, 0, WIDTH_LONG, 0, aAcqCommand); //, (u8*)apConfig, configPayloadSize);
  if (apConfig != NULL)
  {
    request.appendPayload((u8*) apConfig, sizeof(FemAcquireConfiguration));
  }

  // Send the command transaction
  this->send(request);

  // Receive the response
  FemTransaction response = this->receive();

  // Check that the response is an ACK of the correct command
  u8 responseCmd = response.getCommand();
  if (responseCmd != CMD_ACQUIRE)
  {
    std::ostringstream msg;
    msg << "Mismatched command type in FEM response. Sent cmd: " << (unsigned int) CMD_ACQUIRE
        << " recvd: " << (unsigned int) responseCmd;
    throw FemClientException(femClientResponseMismatch, msg.str());
  }

  u8 responseState = response.getState();
  if (!(CMPBIT(responseState, STATE_ACK)) || (CMPBIT(responseState, STATE_NACK)))
  {
    std::ostringstream msg;
    msg << "Acquire command " << aAcqCommand << " failed: " << response.getErrorString()
        << " (errno=" << response.getErrorNum() << ")";
    throw FemClientException(femClientMissingAck, msg.str());
  }

  u32 responseAddr = response.getAddress();
  if (responseAddr != aAcqCommand)
  {
    std::ostringstream msg;
    msg << "Mismached acquire command in FEM response. Sent: " << aAcqCommand << " recvd: "
        << responseAddr;
    throw FemClientException(femClientResponseMismatch, msg.str());
  }

  std::vector<u8> responsePayload = response.getPayload();
  return responsePayload;
}

/** send - send a transaction to the connected FEM
 *
 * This function encodes and transmits a transaction to the FEM, handling error conditions
 * by throwing FemClientExceptions as appropriate. The operation will time out according to
 * the current timeout value.
 *
 * @param aTrans FemTransaction instance to be sent to the FEM
 * @return length of transaction sent to FEM as size_t
 */
std::size_t FemClient::send(FemTransaction aTrans)
{

  // Encode the transaction to be sent onto a byte stream
  std::vector<u8> encoded = aTrans.encode();

  // Set a deadline for the asynchronous receive operation if timeout is specified, otherwise
  // revert it back to +ve infinity to stall the deadline timer actor
  if (mTimeout > 0)
  {
    mDeadline.expires_from_now(boost::posix_time::milliseconds(mTimeout));
  }
  else
  {
    mDeadline.expires_at(boost::posix_time::pos_infin);
  }

  // Set up the variables that receive the result of the asynchronous operation. The error code
  // is set to would_block to signal that the operation is incomplete. ASIO guarantees that its
  // asynchronous operations never fail with would_block so any other value in error indicates
  // completion
  std::size_t sendLen = 0;
  boost::system::error_code error = boost::asio::error::would_block;

  // Start the asynchronous operation. The asyncCompletionHandler function is specified as a callback
  // to update the error and length variables
  boost::asio::async_write(
      mSocket, boost::asio::buffer(encoded),
      boost::bind(&FemClient::asyncCompletionHandler, _1, _2, &error, &sendLen));

  // Block until the asynchronous operation has completed
  do
  {
    mIoService.run_one();
  }
  while (error == boost::asio::error::would_block);

  // Handle any error conditions arising during asynchronous operation
  if (error == boost::asio::error::eof)
  {
    // Connection closed by peer
    throw FemClientException(femClientDisconnected, "Connection closed by FEM");
  }
  else if (error == boost::asio::error::operation_aborted)
  {
    // Timeout signalled by deadline actor
    throw FemClientException(femClientTimeout, "Timeout sending transaction to FEM");
  }
  else if (error)
  {
    throw FemClientException((FemClientErrorCode) error.value(), error.message());
  }
  else if (sendLen != encoded.size())
  {
    // Sent length doesn't match the size of the encoded transcation
    std::ostringstream msg;
    msg << "Size mismatch when sending transaction: wrote " << sendLen << " expected "
        << encoded.size();
    throw FemClientException(femClientSendMismatch, msg.str());
  }

  return sendLen;
}

/** send - send a transaction to the connected FEM
 *
 * This function encodes and transmits a transaction to the FEM, handling error conditions
 * by throwing FemClientExceptions as appropriate. The operation will time out according to
 * the current timeout value.
 *
 * @param aTrans FemTransaction instance to be sent to the FEM
 * @return length of transaction sent to FEM as size_t
 */
std::size_t FemClient::send(std::vector<u8> encoded)
{

  // Encode the transaction to be sent onto a byte stream
  //std::vector<u8> encoded = aTrans.encode();

  // Set a deadline for the asynchronous receive operation if timeout is specified, otherwise
  // revert it back to +ve infinity to stall the deadline timer actor
  if (mTimeout > 0)
  {
    mDeadline.expires_from_now(boost::posix_time::milliseconds(mTimeout));
  }
  else
  {
    mDeadline.expires_at(boost::posix_time::pos_infin);
  }

  // Set up the variables that receive the result of the asynchronous operation. The error code
  // is set to would_block to signal that the operation is incomplete. ASIO guarantees that its
  // asynchronous operations never fail with would_block so any other value in error indicates
  // completion
  std::size_t sendLen = 0;
  boost::system::error_code error = boost::asio::error::would_block;

  // Start the asynchronous operation. The asyncCompletionHandler function is specified as a callback
  // to update the error and length variables
  boost::asio::async_write(
      mSocket, boost::asio::buffer(encoded),
      boost::bind(&FemClient::asyncCompletionHandler, _1, _2, &error, &sendLen));

  // Block until the asynchronous operation has completed
  do
  {
    mIoService.run_one();
  }
  while (error == boost::asio::error::would_block);

  // Handle any error conditions arising during asynchronous operation
  if (error == boost::asio::error::eof)
  {
    // Connection closed by peer
    throw FemClientException(femClientDisconnected, "Connection closed by FEM");
  }
  else if (error == boost::asio::error::operation_aborted)
  {
    // Timeout signalled by deadline actor
    throw FemClientException(femClientTimeout, "Timeout sending transaction to FEM");
  }
  else if (error)
  {
    throw FemClientException((FemClientErrorCode) error.value(), error.message());
  }
  else if (sendLen != encoded.size())
  {
    // Sent length doesn't match the size of the encoded transcation
    std::ostringstream msg;
    msg << "Size mismatch when sending transaction: wrote " << sendLen << " expected "
        << encoded.size();
    throw FemClientException(femClientSendMismatch, msg.str());
  }

  return sendLen;
}

/** receive - receive a transaction response from a FEM
 *
 * This function receives a transaction response from a FEM, unpacking the byte stream
 * into a FemTransaction object and returning it to the caller
 *
 * @return a FemTransaction object received from the FEM
 */
FemTransaction FemClient::receive(void)
{

  // Error code and receive length variables
  boost::system::error_code error;
//	std::size_t recvLen = 0;

  // Receive a transaction header first to determine payload length
  const std::size_t headerLen = FemTransaction::headerLen();
  std::vector<u8> buffer(headerLen);

//	recvLen = receivePart(buffer, error);
  receivePart(buffer, error);
  if (error == boost::asio::error::eof)
  {
    // Connection closed by peer
    throw FemClientException(femClientDisconnected, "Connection closed by FEM");
  }
  else if (error == boost::asio::error::operation_aborted)
  {
    // Timeout signalled by deadline actor
    throw FemClientException(femClientTimeout, "Timeout receiving transaction header from FEM");
  }
  else if (error)
  {
    throw FemClientException((FemClientErrorCode) error.value(), error.message());
  }

  // Decode stream into header of new transaction
  FemTransaction recvTrans(buffer);

  // Read the payload and append to transaction until the payload is complete and matches header
  while (recvTrans.payloadIncomplete())
  {
    std::size_t remainingLen = recvTrans.payloadRemaining();
    std::vector<u8> recvBuffer(remainingLen);

//		recvLen = receivePart(recvBuffer, error);
    receivePart(recvBuffer, error);

    if (error == boost::asio::error::eof)
    {
      // Connection closed by peer
      throw FemClientException(femClientDisconnected, "Connection closed by FEM");
    }
    else if (error == boost::asio::error::operation_aborted)
    {
      // Timeout signalled by deadline actor
      throw FemClientException(femClientTimeout, "Timeout receiving transaction payload from FEM");
    }
    else if (error)
    {
      throw FemClientException((FemClientErrorCode) error.value(), error.message());
    }

    recvTrans.appendPayloadFromStream(recvBuffer);

  }

  return recvTrans;
}

FemTransaction FemClient::receive(u8* aPayload)
{

  // Error code and receive length variables
  boost::system::error_code error;
//	std::size_t recvLen = 0;

  // Receive a transaction header first to determine payload length
  const std::size_t headerLen = FemTransaction::headerLen();
  std::vector<u8> buffer(headerLen);

  receivePart(buffer, error);
  if (error == boost::asio::error::eof)
  {
    // Connection closed by peer
    throw FemClientException(femClientDisconnected, "Connection closed by FEM");
  }
  else if (error == boost::asio::error::operation_aborted)
  {
    // Timeout signalled by deadline actor
    throw FemClientException(femClientTimeout, "Timeout receiving transaction header from FEM");
  }
  else if (error)
  {
    throw FemClientException((FemClientErrorCode) error.value(), error.message());
  }

  // Decode stream into header of new transaction
  FemTransaction recvTrans(buffer);

  // Read the payload and append to transaction until the payload is complete and matches header
  while (recvTrans.payloadIncomplete())
  {
    std::size_t remainingLen = recvTrans.payloadRemaining();
    std::vector<u8> recvBuffer(remainingLen);

    receivePart(recvBuffer, error);

    if (error == boost::asio::error::eof)
    {
      // Connection closed by peer
      throw FemClientException(femClientDisconnected, "Connection closed by FEM");
    }
    else if (error == boost::asio::error::operation_aborted)
    {
      // Timeout signalled by deadline actor
      throw FemClientException(femClientTimeout, "Timeout receiving transaction payload from FEM");
    }
    else if (error)
    {
      throw FemClientException((FemClientErrorCode) error.value(), error.message());
    }

    recvTrans.appendPayloadFromStream(recvBuffer, aPayload);

  }

  return recvTrans;
}

/** receivePart - receive part of a transaction from a FEM
 *
 * This private method receives an arbitrary length transaction fragment from a FEM and
 * places it into a buffer for decoding into a transaction. The receive is handed off to
 * an asynchronous operation and blocks until that operation completes or a timeout occurs.
 * A completion handler fills the error code and length values into the appropriate argument
 * and return value for decoding by the calling function.
 *
 * @param aBuffer reference to std::vector byte buffer to receive data into
 * @param aError  reference to boost error object to place error code in
 * @return size_t size of received data in bytes
 */
std::size_t FemClient::receivePart(std::vector<u8>& aBuffer, boost::system::error_code& aError)
{

  // Set a deadline for the asynchronous receive operation if timeout is specified, otherwise
  // revert it back to +ve infinity to stall the deadline timer actor
  if (mTimeout > 0)
  {
    mDeadline.expires_from_now(boost::posix_time::milliseconds(mTimeout));
  }
  else
  {
    mDeadline.expires_at(boost::posix_time::pos_infin);
  }

  // Set up the variables that receive the result of the asynchronous operation. The aError code
  // is set to would_block to signal that the operation is incomplete. ASIO guarantees that its
  // asynchronous operations never fail with would_block so any other value in aError indicates
  // completion
  aError = boost::asio::error::would_block;
  std::size_t recvLen = 0;

  // Start the asynchronous operation. The asyncCompletionHandler function is specified as a callback
  // to update the error and length variables
  mSocket.async_read_some(
      boost::asio::buffer(aBuffer),
      boost::bind(&FemClient::asyncCompletionHandler, _1, _2, &aError, &recvLen));

  // Block until the asynchronous operation has completed
  do
  {
    mIoService.run_one();
  }
  while (aError == boost::asio::error::would_block);
  return recvLen;
}

/** checkDeadline - check if deadline timer has expired and handle accordingly
 *
 * This function implements the deadline timer actor functionality, which allows
 * socket operations to time out. It checks if an active deadline timer has expired
 * when called: if so, a timeout has occurred so any pending socket operation is
 * cancelled, allowing the blocking operation to return. The deadline timer is then
 * put back to sleep for the appropriate time.
 */
void FemClient::checkDeadline(void)
{

  // Handle deadline if expired
  if (mDeadline.expires_at() <= boost::asio::deadline_timer::traits_type::now())
  {

    // Cancel any pending socket operation
    mSocket.cancel();

    // No longer an active deadline so set the expiry to positive infinity
    mDeadline.expires_at(boost::posix_time::pos_infin);
  }

  // Put the deadline actor back to sleep
  mDeadline.async_wait(boost::bind(&FemClient::checkDeadline, this));

}

/** asyncConnectHandkler - handler called when an asynchronous connect opertation completes
 *
 * This function is called as the completion handler on the asynschronous socket connect
 * operation during initialisation. The handler simply fills the completion error code
 * into the output error code for use in the calling function. The incoming error
 * code is specified in the binding of the handler.
 *
 * @param aErrorCode reference to error code state at end of operation
 * @param aOuptputErrorCode pointer to variable to receive error code
 */
void FemClient::asyncConnectHandler(const boost::system::error_code& aErrorCode,
    boost::system::error_code* apOutputErrorCode)
{

  *apOutputErrorCode = aErrorCode;

}

/** asyncCompletionHandler - handler called when an asynchronous operation completes
 *
 * This function is called as the completion handler on all asynchronous socket
 * operations (read and write) and serves to fill in the final error state and
 * operation read/write length into the necessary variables. The incoming error code
 * and length are as specified in the binding of this handler to the async operation.
 *
 * @param aErrorCode reference to error code state at end of operation
 * @param aLength reference to length in bytes of completed socket operation
 * @param apOutputErrorCode pointer to variable to receive error code
 * @param apOutputLength pointer to variable to receive operation length
 */
void FemClient::asyncCompletionHandler(const boost::system::error_code& aErrorCode,
    std::size_t aLength, boost::system::error_code* apOutputErrorCode, std::size_t* apOutputLength)
{
  *apOutputErrorCode = aErrorCode;
  *apOutputLength = aLength;
}

// Temp function to allow testing of timeouts etc - DELETE
void FemClient::runIoService(void)
{
  mIoService.run();
}
