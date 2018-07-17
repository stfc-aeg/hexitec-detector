/*
 * FemDataReceiver.h
 *
 *  Created on: 7 Dec 2011
 *      Author: tcn
 */

#ifndef FEMDATARECEIVER_H_
#define FEMDATARECEIVER_H_

#include <boost/thread/thread.hpp>
#include <boost/asio.hpp>
#include <boost/function.hpp>
#include <boost/bind.hpp>
#include <boost/asio/io_service.hpp>
#include <boost/asio/deadline_timer.hpp>
#include <boost/shared_ptr.hpp>

#include <dataTypes.h>
#include <time.h>

typedef struct bufferInfo_t
{
  u8* addr;
  unsigned int length;
} BufferInfo;

typedef struct packetHeader_t
{
  u32 frameNumber;
  u32 packetNumberFlags;
} PacketHeader;

const u32 kStartOfFrameMarker = 1 << 31;
const u32 kEndOfFrameMarker = 1 << 30;
const u32 kPacketNumberMask = 0x3FFFFFFF;

typedef enum
{
  headerAtStart, headerAtEnd
} FemDataReceiverHeaderPosition;

typedef u64 FrameNumber;

typedef boost::function<BufferInfo(void)> allocateCallback_t;
typedef boost::function<void(int)> freeCallback_t;
typedef boost::function<void(int, time_t)> receiveCallback_t;
typedef boost::function<void(int)> signalCallback_t;

typedef struct callbackBundle_t
{
  allocateCallback_t allocate;
  freeCallback_t free;
  receiveCallback_t receive;
  signalCallback_t signal;

} CallbackBundle;

namespace FemDataReceiverSignal
{
  typedef enum
  {
    femAcquisitionNullSignal, femAcquisitionComplete, femAcquisitionCorruptImage
  } FemDataReceiverSignals;
}

const unsigned int kWatchdogHandlerIntervalMs = 1000;

class FemDataReceiver
{
public:

  FemDataReceiver(unsigned int aRecvPort);
  virtual ~FemDataReceiver();

  void startAcquisition(void);
  void stopAcquisition(unsigned int framesRead);

  void registerCallbacks(CallbackBundle* aBundle);

  void setNumFrames(unsigned int aNumFrames);
  void setFrameLength(unsigned int mFrameLength);
  void setFrameHeaderLength(unsigned int aHeaderLength);
  void setFrameHeaderPosition(FemDataReceiverHeaderPosition aPosition);
  void setNumSubFrames(unsigned int aNumSubFrames);

  void setAcquisitionPeriod(unsigned int aPeriodMs);
  void setAcquisitionTime(unsigned int aTimeMs);
  void enableFrameCounter(bool aEnable);
  void enableFrameCounterCheck(bool aEnable);

  bool acqusitionActive(void);

private:

  boost::asio::io_service mIoService;
  boost::asio::ip::udp::endpoint mRemoteEndpoint;
  boost::asio::ip::udp::socket mRecvSocket;
  boost::asio::deadline_timer mWatchdogTimer;
  boost::shared_ptr<boost::thread> mReceiverThread;

  unsigned int mRecvWatchdogCounter;

  CallbackBundle mCallbacks;

  bool mAcquiring;
  unsigned int mRemainingFrames;
  unsigned int mCompleteAfterNumFrames;

  unsigned int mNumFrames;
  unsigned int mFrameLength;
  unsigned int mFrameHeaderLength;
  FemDataReceiverHeaderPosition mHeaderPosition;
  unsigned int mAcquisitionPeriod;
  unsigned int mAcquisitionTime;
  unsigned int mNumSubFrames;
  unsigned int mSubFrameLength;
  bool mHasFrameCounter;
  bool mEnableFrameCounterCheck;

  PacketHeader mPacketHeader;
  BufferInfo mCurrentBuffer;
  FrameNumber mCurrentFrameNumber;
  FrameNumber mLatchedFrameNumber;

  unsigned int mFrameTotalBytesReceived;
  unsigned int mFramePayloadBytesReceived;
  unsigned int mSubFramePacketsReceived;
  unsigned int mSubFramesReceived;
  unsigned int mSubFrameBytesReceived;
  unsigned int mFramesReceived;

  FemDataReceiverSignal::FemDataReceiverSignals mLatchedErrorSignal;

  void* lScratchBuffer;

  void handleReceive(const boost::system::error_code& errorCode, std::size_t bytesReceived);
  void simulateReceive(BufferInfo aBuffer);
  void watchdogHandler(void);
};

#endif /* FEMDATARECEIVER_H_ */
