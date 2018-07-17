/*
 * FemTransaction.cpp
 *
 *  Created on: Nov 16, 2011
 *      Author: tcn45
 */

#include "FemTransaction.h"
#include <arpa/inet.h>
#include <iostream>

FemTransaction::FemTransaction(u8 cmd, u8 bus, u8 width, u8 state, u32 address, u8* payload,
    u32 payloadSize)
{
  // Constructor for near zero copy
  // Initialize header values
  mHeader.magic = PROTOCOL_MAGIC_WORD;
  mHeader.command = cmd;
  mHeader.bus_target = bus;
  mHeader.data_width = width;
  mHeader.state = state;
  mHeader.address = address;
  mHeader.payload_sz = 0;
  mHeader.payload_sz = payloadSize;
  thePayload = payload;
  payloadCompleted = 0;
  encoded.clear();
}

FemTransaction::FemTransaction(u8 cmd, u8 bus, u8 width, u8 state, u32 address)
{
  // Initialize header values
  mHeader.magic = PROTOCOL_MAGIC_WORD;
  mHeader.command = cmd;
  mHeader.bus_target = bus;
  mHeader.data_width = width;
  mHeader.state = state;
  mHeader.address = address;
  mHeader.payload_sz = 0;

  // Clear payload remaining counter
  mPayloadRemaining = 0;
}

FemTransaction::FemTransaction(const std::vector<u8>& byteStream)
{
  // Intialise header from byte stream
  mHeader = *(struct protocol_header*) &byteStream[0];

  // Convert byte order of appropriate header fields
  mHeader.magic = ntohl(mHeader.magic);
  mHeader.address = ntohl(mHeader.address);
  mHeader.payload_sz = ntohl(mHeader.payload_sz);

  // Clear payload remaining counter
  mPayloadRemaining = 0;

  payloadCompleted = 0;
  // Unpack payload from byte stream, converting from network byte order as appropriate
  appendPayloadFromStream(byteStream, headerLen());
}

FemTransaction::~FemTransaction()
{
  // TODO Auto-generated destructor stub
}

std::vector<u8> FemTransaction::encode()
{
  // Encode header onto output byte stream with appropriate byte ordering
  u32Encode(encoded, mHeader.magic);
  encoded.push_back(mHeader.command);
  encoded.push_back(mHeader.bus_target);
  encoded.push_back(mHeader.data_width);
  encoded.push_back(mHeader.state);
  u32Encode(encoded, mHeader.address);
  u32Encode(encoded, mHeader.payload_sz);

  // Append payload, converting to network byte order as appropriate. A read transaction
  // always has a fixed length payload (read length) encoded as a long word
  if ((mHeader.command == CMD_ACCESS) && (CMPBIT(mHeader.state, STATE_READ)))
  {
    for (unsigned int i = 0; i < mHeader.payload_sz; i += sizeof(u32))
    {
      u32 value = (u32) (*(u32*) &(mPayload[i]));
      u32Encode(encoded, value);
    }
  }
  else
  {
    switch (mHeader.data_width)
    {

      case WIDTH_BYTE:
        for (unsigned int i = 0; i < mHeader.payload_sz; i++)
        {
          encoded.push_back(mPayload[i]);
        }
        break;

      case WIDTH_WORD:
        for (unsigned int i = 0; i < mHeader.payload_sz; i += sizeof(u16))
        {
          u16 value = (u16) (*(u16*) &(mPayload[i]));
          u16Encode(encoded, value);
        }
        break;

      case WIDTH_LONG:
        for (unsigned int i = 0; i < mHeader.payload_sz; i += sizeof(u32))
        {
          u32 value = (u32) (*(u32*) &(mPayload[i]));
          u32Encode(encoded, value);
        }
        break;

      case WIDTH_UNSUPPORTED:
        // Fall-thru
      default:
        // TODO - handle unsupported or illegal width - throw exception?
        break;
    }
  }
  return encoded;
}

std::vector<u8> FemTransaction::encodeArray()
{
  // Encode header onto output byte stream with appropriate byte ordering
  u32Encode(encoded, mHeader.magic);
  encoded.push_back(mHeader.command);
  encoded.push_back(mHeader.bus_target);
  encoded.push_back(mHeader.data_width);
  encoded.push_back(mHeader.state);
  u32Encode(encoded, mHeader.address);
  u32Encode(encoded, mHeader.payload_sz);

  // Append payload, converting to network byte order as appropriate. A read transaction
  // always has a fixed length payload (read length) encoded as a long word
  if ((mHeader.command == CMD_ACCESS) && (CMPBIT(mHeader.state, STATE_READ)))
  {
    u32* payloadPtr = (u32*) thePayload;
    for (unsigned int i = 0; i < mHeader.payload_sz / sizeof(u32); i++)
    {
      u32 value = *payloadPtr++;
      u32Encode(encoded, value);
    }
  }
  else if (mHeader.payload_sz != 0)
  {
    switch (mHeader.data_width)
    {

      case WIDTH_BYTE:
      {
        u8* payloadPtr = (u8*) thePayload;
        for (unsigned int i = 0; i < mHeader.payload_sz; i++)
        {
          encoded.push_back(*payloadPtr++);
        }
        break;
      }
      case WIDTH_WORD:
      {
        u16* payloadPtr = (u16*) thePayload;
        for (unsigned int i = 0; i < mHeader.payload_sz / sizeof(u16); i++)
        {
          u16Encode(encoded, *payloadPtr++);
        }
        break;
      }
      case WIDTH_LONG:
      {
        u32* payloadPtr = (u32*) thePayload;
        for (unsigned int i = 0; i < mHeader.payload_sz / sizeof(u32); i++)
        {
          u32Encode(encoded, *payloadPtr++);
        }
        break;
      }
      case WIDTH_UNSUPPORTED:
        // Fall-thru
      default:
        // TODO - handle unsupported or illegal width - throw exception?
        break;
    }
  }
  return encoded;
}

void FemTransaction::appendPayload(u8* aPayload, u32 aAppendLen)
{
  for (unsigned int i = 0; i < aAppendLen; i++)
  {
    mPayload.push_back(*(aPayload + i));
  }
  mHeader.payload_sz = (mHeader.payload_sz - mPayloadRemaining) + aAppendLen;
  mPayloadRemaining = mHeader.payload_sz - mPayload.size();
}

void FemTransaction::appendPayloadFromStream(const std::vector<u8>& aByteStream, size_t offset)
{

  unsigned int copyStart = 0;
  size_t copySize = aByteStream.size() - offset;

  // If the transaction is a read/write command acknowledgement, the first four bytes
  // are the access length as u32 and should be swapped as such. Then skip decoding
  // of this word in subsequent processing by offsetting copyStart from zero.
  if ((mHeader.command == CMD_ACCESS) && (CMPBIT(mHeader.state, STATE_ACK)) && (offset == 0))
  {
    u32 ackLen = (u32) *(u32*) &(aByteStream[0]);
    u32Decode(mPayload, ackLen);
    copyStart = sizeof(u32);
  }

  switch (mHeader.data_width)
  {
    case WIDTH_BYTE:
      for (unsigned int i = copyStart; i < copySize; i++)
      {
        mPayload.push_back(aByteStream[i + offset]);
      }
      break;

    case WIDTH_WORD:
      for (unsigned int i = copyStart; i < copySize; i += sizeof(u16))
      {
        u16 value = (u16) *(u16*) &(aByteStream[i + offset]);
        u16Decode(mPayload, value);
      }
      break;

    case WIDTH_LONG:
      for (unsigned int i = copyStart; i < copySize; i += sizeof(u32))
      {
        u32 value = (u32) *(u32*) &(aByteStream[i + offset]);
        u32Decode(mPayload, value);
      }
      break;

    case WIDTH_UNSUPPORTED:
      // Fall-thru
    default:
      // TODO Throw exception here?
      break;
  }

  mHeader.payload_sz = (mHeader.payload_sz - mPayloadRemaining) + copySize;
  mPayloadRemaining = mHeader.payload_sz - mPayload.size();

}

void FemTransaction::appendPayloadFromStream(const std::vector<u8>& aByteStream, u8* aPayload,
    size_t offset)
{

  unsigned int copyStart = 0;
  size_t copySize = aByteStream.size() - offset;

  // If the transaction is a read/write command acknowledgement, the first four bytes
  // are the access length as u32 and should be swapped as such. Then skip decoding
  // of this word in subsequent processing by offsetting copyStart from zero.
  if ((mHeader.command == CMD_ACCESS || mHeader.command == CMD_PERSONALITY)
      && (CMPBIT(mHeader.state, STATE_ACK)) && (offset == 0))
  {
    u32 ackLen = (u32) *(u32*) &(aByteStream[0]);
    copyStart = sizeof(u32);
    u32 aout[] =
      { 0 };
    u8* aPtr = (u8*) aout;
    u32Decode(aPtr, ackLen);
    this->acklen = aout[0];
  }

  switch (mHeader.data_width)
  {
    case WIDTH_BYTE:
    {
      u8* aPayloadPtr = (u8*) aPayload;
      for (unsigned int i = copyStart; i < copySize; i++)
      {
        *aPayloadPtr++ = aByteStream[i + offset];
      }
      break;
    }
    case WIDTH_WORD:
    {
      u16* aPayloadPtr = (u16*) aPayload;
      for (unsigned int i = copyStart; i < copySize; i += sizeof(u16))
      {
        u16 value = (u16) *(u16*) &(aByteStream[i + offset]);
        u16Decode((u8*) aPayloadPtr, value);
        aPayloadPtr++;
      }
      break;
    }
    case WIDTH_LONG:
    {
      u32* aPayloadPtr = (u32*) aPayload;
      aPayloadPtr += payloadCompleted;
      for (unsigned int i = copyStart; i < copySize; i += sizeof(u32))
      {
        u32 value = (u32) *(u32*) &(aByteStream[i + offset]);
        u32Decode((u8*) aPayloadPtr, value);
        aPayloadPtr++;
      }
      break;
    }
    case WIDTH_UNSUPPORTED:
      // Fall-thru
    default:
      // TODO Throw exception here?
      break;
  }
  mHeader.payload_sz = (mHeader.payload_sz - mPayloadRemaining) + copySize;
  payloadCompleted += copySize - copyStart;
  mPayloadRemaining = mHeader.payload_sz - payloadCompleted - 4;

}

void FemTransaction::clearPayload(void)
{
  mPayload.clear();
  mHeader.payload_sz = 0;
}

std::vector<u8> FemTransaction::getPayload(void)
{
  return mPayload;
}

bool FemTransaction::payloadIncomplete(void)
{
  bool incomplete = (mPayloadRemaining != 0);
  return incomplete;
}
//	std::vector<u8> encoded(0);

size_t FemTransaction::payloadRemaining(void)
{
  return mPayloadRemaining;
}

u32 FemTransaction::payloadLength(void)
{
  return acklen;
}

u8 FemTransaction::getCommand(void)
{
  return mHeader.command;
}

u8 FemTransaction::getState(void)
{
  return mHeader.state;
}

u32 FemTransaction::getAddress(void)
{
  return mHeader.address;
}

std::ostream& operator<<(std::ostream& aOut, const FemTransaction &aTrans)
{

  aOut << "Magic word     : 0x" << std::hex << (u32) aTrans.mHeader.magic << std::endl;
  aOut << "Command        : 0x" << std::hex << (u32) aTrans.mHeader.command << std::endl;
  aOut << "Bus            : 0x" << std::hex << (u32) aTrans.mHeader.bus_target << std::endl;
  aOut << "Width          : 0x" << std::hex << (u32) aTrans.mHeader.data_width << std::endl;
  aOut << "State          : 0x" << std::hex << (u32) aTrans.mHeader.state << std::endl;
  aOut << "Address        : 0x" << std::hex << (u32) aTrans.mHeader.address << std::endl;
  aOut << "Payload length : 0x" << std::hex << (u32) aTrans.mHeader.payload_sz << std::endl;
  aOut << "Payload        : ";

//    for (unsigned int i = 0; i < aTrans.mHeader.payload_sz; i++) {
  for (unsigned int i = 0; i < aTrans.mPayload.size(); i++)
  {
    aOut << "0x" << std::hex << (u32) aTrans.mPayload[i] << " ";
    if (i && (i % 8 == 0))
    {
      aOut << "                 " << std::endl;
    }
  }
  aOut << std::dec;

  return aOut;

}

int FemTransaction::getErrorNum(void)
{
  int errorCode = -1;
  if (mPayload.size() > 0)
  {
    errorCode = (int) mPayload[0];
  }
  return errorCode;
}

std::string FemTransaction::getErrorString(void)
{
  if (mPayload.size() > 1)
  {
    return std::string(mPayload.begin() + 1, mPayload.end());
  }
  else
  {
    return std::string("No error string in transaction payload");
  }
}

std::size_t FemTransaction::widthToSize(u8 aWidth)
{
  std::size_t widthSize;

  switch (aWidth)
  {

    case WIDTH_BYTE:
      widthSize = sizeof(u8);
      break;

    case WIDTH_WORD:
      widthSize = sizeof(u16);
      break;

    case WIDTH_LONG:
      widthSize = sizeof(u32);
      break;

    case WIDTH_UNSUPPORTED:
      // Deliberate fall-through
    default:
      widthSize = 0;
      break;
  }
  return widthSize;
}

inline void FemTransaction::u16Encode(std::vector<u8>& aEncoded, u16 aValue)
{
  u16 encodedValue = htons(aValue);
  for (unsigned int byte = 0; byte < sizeof(encodedValue); byte++)
  {
    aEncoded.push_back((u8) *(((u8*) &encodedValue) + byte));
  }
}

inline void FemTransaction::u32Encode(std::vector<u8>& aEncoded, u32 aValue)
{
  u32 encodedValue = htonl(aValue);
  for (unsigned int byte = 0; byte < sizeof(encodedValue); byte++)
  {
    aEncoded.push_back((u8) *(((u8*) &encodedValue) + byte));
  }
}

inline void FemTransaction::u16Decode(std::vector<u8>& aDecoded, u16 aValue)
{
  u16 decodedValue = ntohs(aValue);
  for (unsigned int byte = 0; byte < sizeof(decodedValue); byte++)
  {
    aDecoded.push_back((u8) *(((u8*) &decodedValue) + byte));
  }
}

inline void FemTransaction::u32Decode(std::vector<u8>& aDecoded, u32 aValue)
{
  u32 decodedValue = ntohl(aValue);
  for (unsigned int byte = 0; byte < sizeof(decodedValue); byte++)
  {
    aDecoded.push_back((u8) *(((u8*) &decodedValue) + byte));
  }
}
inline void FemTransaction::u32Decode(u8* aDecoded, u32 aValue)
{
  u32 decodedValue = ntohl(aValue);
  for (unsigned int byte = 0; byte < sizeof(decodedValue); byte++)
  {
    *aDecoded++ = *(((u8*) &decodedValue) + byte);
  }
}

inline void FemTransaction::u16Decode(u8* aDecoded, u16 aValue)
{
  u16 decodedValue = ntohs(aValue);
  for (unsigned int byte = 0; byte < sizeof(decodedValue); byte++)
  {
    *aDecoded++ = *(((u8*) &decodedValue) + byte);
  }
}

