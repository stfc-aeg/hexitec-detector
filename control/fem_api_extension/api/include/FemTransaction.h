/*
 * FemTransaction.h
 *
 *  Created on: Nov 16, 2011
 *      Author: tcn45
 */

#ifndef FEMTRANSACTION_H_
#define FEMTRANSACTION_H_

#include <vector>
#include "protocol.h"
#include <ostream>

class FemTransaction
{

public:

  FemTransaction(u8 cmd = CMD_UNSUPPORTED, u8 bus = BUS_UNSUPPORTED, u8 width = WIDTH_UNSUPPORTED,
      u8 state = STATE_UNSUPPORTED, u32 address = 0);

  FemTransaction(u8 cmd, u8 bus, u8 width, u8 state, u32 address, u8* payload, u32 payloadSize);

  FemTransaction(const std::vector<u8>& byteStream);

  virtual ~FemTransaction();

  static const size_t headerLen(void)
  {
    return sizeof(struct protocol_header);
  }
  ;

  std::vector<u8> encode();
  void appendPayload(u8* aPayload, u32 aPayloadLen);
  void appendPayloadFromStream(const std::vector<u8>& byteStream, size_t offset = 0);
  void clearPayload(void);

  // Getter methods
  u8 getCommand(void);
  u8 getState(void);
  u32 getAddress(void);
  std::vector<u8> getPayload(void);

  bool payloadIncomplete(void);
  size_t payloadRemaining(void);

  friend std::ostream& operator<<(std::ostream& aOut, const FemTransaction& aTrans);

  int getErrorNum(void);
  std::string getErrorString(void);

  static std::size_t widthToSize(u8 aWidth);

  // added for zero copy
  std::vector<u8> encodeArray();
  void appendPayloadFromStream(const std::vector<u8>& byteStream, u8* aPayload, size_t offset = 0);
  u32 payloadLength(void);

private:

  struct protocol_header mHeader;
  std::vector<u8> mPayload;

  size_t mPayloadRemaining;

  // added for zero copy
  u8* thePayload;
  u32 payloadCompleted;
  std::vector<u8> encoded;
  u32 acklen;

  void u16Encode(std::vector<u8>& aEncoded, u16 aValue);
  void u32Encode(std::vector<u8>& aEncoded, u32 aValue);
  void u16Decode(std::vector<u8>& aDecoded, u16 aValue);
  void u32Decode(std::vector<u8>& aDecoded, u32 aValue);

  // added for zero copy
  void u32Decode(u8* aDecoded, u32 aValue);
  void u16Decode(u8* aDecoded, u16 aValue);

};

#endif /* FEMTRANSACTION_H_ */
