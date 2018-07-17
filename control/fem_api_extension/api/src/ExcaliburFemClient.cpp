/*
 * ExcaliburFemClient.cpp - EXCALIBUR FEM client class implementation
 *
 *  Created on: 7 Dec 2011
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "ExcaliburFemClient.h"
#include "ExcaliburFrontEndDevices.h"
#include "asicControlParameters.h"
#include "mpx3Parameters.h"
#include "FemLogger.h"
#include "time.h"
#include <map>
#include <iostream>
#include <iomanip>
#include <sstream>


typedef void (ExcaliburFemClient::*ExcaliburScanFunc)(void);

ExcaliburFemClient::ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
    const CtlConfig* aConfig, unsigned int aTimeoutInMsecs) :
    FemClient(aConfig->femNumber, aConfig->femAddress, aConfig->femPort, aTimeoutInMsecs),
    mMpx3GlobalTestPulseEnable(false),
    mMpx3TestPulseCount(4000),
    mDataReceiverEnable(true),
    mCtlHandle(aCtlHandle),
    mCallbacks(aCallbacks),
    mConfig(aConfig),
    mAsicDataReorderMode(reorderedDataMode),
    mNumSubFrames(2),
    mTriggerMode(excaliburTriggerModeInternal),
    mTriggerPolarity(excaliburTriggerPolarityActiveHigh),
    mBurstModeSubmitPeriod(0),
    mLfsrBypassEnable(false),
    mEnableDeferredBufferRelease(false),
    mDacScanDac(0),
    mDacScanStart(0),
    mDacScanStop(0),
    mDacScanStep(0)
{

  // Initialize MPX3 DAC settings, values and pixel config caches to zero
  for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
  {
    for (unsigned int iDac = 0; iDac < numExcaliburDacs; iDac++)
    {
      mMpx3DacCache[iChip][iDac] = 0;
    }

    for (unsigned int iConfig = 0; iConfig < numPixelConfigs; iConfig++)
    {
      for (unsigned int iPixel = 0; iPixel < kNumPixelsPerAsic; iPixel++)
      {
        mMpx3PixelConfigCache[iChip][iConfig][iPixel] = 0;
      }
    }

    // Initialise default values for some standard parameters used in all
    // OMR transactions
    mMpx3OmrParams[iChip].readWriteMode = sequentialReadWriteMode;
//		mMpx3OmrParams[iChip].polarity              = electronPolarity;
    mMpx3OmrParams[iChip].polarity = holePolarity;
    mMpx3OmrParams[iChip].readoutWidth = readoutWidth8;
    mMpx3OmrParams[iChip].discCsmSpm = discCsmSpmDiscL;
    mMpx3OmrParams[iChip].testPulseEnable = 0;
    mMpx3OmrParams[iChip].counterDepth = counterDepth12;
    mMpx3OmrParams[iChip].columnBlock = 0;
    mMpx3OmrParams[iChip].columnBlockSelect = 0;
    mMpx3OmrParams[iChip].rowBlock = 0;
    mMpx3OmrParams[iChip].rowBlockSelect = 0;
    mMpx3OmrParams[iChip].equalizationMode = equalizationModeDisabled;
    mMpx3OmrParams[iChip].colourMode = monochromeMode;
    mMpx3OmrParams[iChip].csmSpmMode = csmSpmModeSpm;
    mMpx3OmrParams[iChip].infoHeaderEnable = 0;
    mMpx3OmrParams[iChip].fuseSel = 0;
    mMpx3OmrParams[iChip].fusePulseWidth = 0;
    mMpx3OmrParams[iChip].gainMode = gainModeSuperLow;
    mMpx3OmrParams[iChip].dacSense = 0;
    mMpx3OmrParams[iChip].dacExternal = 0;
    mMpx3OmrParams[iChip].externalBandGapSelect = 0;

    // Initialise chip column test pulse enables
    for (unsigned int iCol = 0; iCol < kNumColsPerAsic; iCol++)
    {
      mMpx3ColumnTestPulseEnable[iChip][iCol] = 0;
    }

    // Initialise chip enable flag
    mMpx3Enable[iChip] = true;

  }

  // Reset the ASIC control f/w block and ASICS
//	this->asicControlReset();
//	this->asicControlAsicReset();

  // Initialise front-end DACs
  //this->frontEndDacInitialise();

  // Build callback bundle to be registered with the data receiver
  mCallbackBundle.allocate = boost::bind(&ExcaliburFemClient::allocateCallback, this);
  mCallbackBundle.free = boost::bind(&ExcaliburFemClient::freeCallback, this, _1);
  mCallbackBundle.receive = boost::bind(&ExcaliburFemClient::receiveCallback, this, _1, _2);
  mCallbackBundle.signal = boost::bind(&ExcaliburFemClient::signalCallback, this, _1);

  // Clear data source and destination addressing tables
  for (unsigned int i = 0; i < kFarmModeLutSize; i++)
  {
    mDataDestIpAddress[i] = "0.0.0.0";
    mDataDestMacAddress[i] = "00:00:00:00:00:00";
    mDataDestPort[i] = 0;
  }

  // Set up default source and destination data connection addresses and ports
  mDataDestIpAddress[0] = "10.0.2.1";
  char dest_mac[18];

  if (this->getMacAddressFromIP(mDataDestIpAddress[0].c_str(), (char*) dest_mac) == 0)
  {
    mDataDestMacAddress[0] = dest_mac;
  }
  else
  {
    FEMLOG(mFemId, logWARNING) << "Failed to resolve default destination MAC address, setting to zero";
    mDataDestMacAddress[0] = "00:00:00:00:00:00";
  }
  mDataDestPort[0] = kDataDestPort;

  mDataSourceIpAddress = this->getFpgaIpAddressFromHost(mDataDestIpAddress[0].c_str());
  mDataSourceMacAddress = "62:00:00:00:00:01";
  mDataSourcePort = kDataSourcePort;

  mDataDestPortOffset = 0;
  mDataFarmModeEnable = false;
  mDataFarmModeNumDestinations = 1;

  // Check DMA engine acquisition state and reset to IDLE if in a different state
  FemAcquireStatus acqStatus = this->acquireStatus();
  if (acqStatus.state != acquireIdle)
  {
      FEMLOG(mFemId, logINFO) << "Acquisition state at startup is "
              << acqStatus.state << " sending stop to reset";
    this->acquireStop();
  }
  else
  {
    FEMLOG(mFemId, logINFO) << "Acquisition state is IDLE at startup";
  }
}

ExcaliburFemClient::~ExcaliburFemClient()
{

  // Delete the data receiver object if it was created
  if (mFemDataReceiver)
  {
    delete (mFemDataReceiver);
  }

}

int ExcaliburFemClient::get_id(void)
{

  return mFemId;
}

BufferInfo ExcaliburFemClient::allocateCallback(void)
{

  BufferInfo buffer;
  CtlFrame* frame;

  // If the frame queue is empty (i.e. no pre-allocated frame buffers), request
  // a frame via the callback, otherwise use the front-most frame in the queue

  if (mFrameQueue.empty())
  {
    frame = mCallbacks->ctlAllocate(mCtlHandle);
    mFrameQueue.push_back(frame);
  }
  else
  {
    frame = mFrameQueue.front();
  }

  // TODO handle frame being NULL here

  // Map the frame information into the buffer to return
  buffer.addr = (u8*) (frame->buffer);
  buffer.length = (frame->bufferLength);

  return buffer;

}

void ExcaliburFemClient::freeCallback(int aVal)
{

  mCallbacks->ctlFree(mCtlHandle, 0);

}

void ExcaliburFemClient::receiveCallback(int aFrameCounter, time_t aRecvTime)
{

  // Get the first frame on our queue
  CtlFrame* frame = mFrameQueue.front();

  // Fill fields into frame metadata
  frame->frameCounter = aFrameCounter;
  frame->timeStamp = aRecvTime;

  // If deferred buffer release is enabled, queue the completed
  // frame on the release queue, otherwise call the receive callback
  // to release the frame
  if (mEnableDeferredBufferRelease)
  {
    mReleaseQueue.push_back(frame);
  }
  else
  {
    mCallbacks->ctlReceive(mCtlHandle, frame);
  }

  // Pop the frame off the queue
  mFrameQueue.pop_front();

}

void ExcaliburFemClient::signalCallback(int aSignal)
{

  int theSignal;

  switch (aSignal)
  {

    case FemDataReceiverSignal::femAcquisitionComplete:

      theSignal = FEM_OP_ACQUISITIONCOMPLETE;
      FEMLOG(mFemId, logDEBUG) << "Got acquisition complete signal";
      //this->acquireStop();
      //this->stopAcquisition();

      // If deferred buffer release is enabled, drain the release queue
      // out through the receive callback at the requested rate
      if (mEnableDeferredBufferRelease)
      {
        this->releaseAllFrames();
      }
      break;

    case FemDataReceiverSignal::femAcquisitionCorruptImage:
      theSignal = FEM_OP_CORRUPTIMAGE;
      FEMLOG(mFemId, logDEBUG) << "Got corrupt image signal";
      break;

    default:
      theSignal = aSignal;
      break;

  }

  mCallbacks->ctlSignal(mCtlHandle, theSignal);

}

void ExcaliburFemClient::preallocateFrames(unsigned int aNumFrames)
{
  for (unsigned int i = 0; i < aNumFrames; i++)
  {
    CtlFrame* frame = mCallbacks->ctlAllocate(mCtlHandle);
    if (frame != NULL)
    {
      mFrameQueue.push_back(frame);
    }
    else
    {
      throw FemClientException((FemClientErrorCode) excaliburFemClientBufferAllocateFailed,
                               "Buffer allocation callback failed");
    }
  }
  FEMLOG(mFemId, logINFO) << "Preallocate complete - frame queue size is now " << mFrameQueue.size();
}

void ExcaliburFemClient::releaseAllFrames(void)
{
  int numFramesToRelease = mReleaseQueue.size();
  FEMLOG(mFemId, logINFO) << "Deferred buffer release - draining release queue of " << numFramesToRelease
      << " frames";

  // Build a timespec for the release period
  time_t releaseSecs = (time_t) ((int) mBurstModeSubmitPeriod);
  long releaseNsecs = (long) ((mBurstModeSubmitPeriod - releaseSecs) * 1E9);
  struct timespec releasePeriod =
    { releaseSecs, releaseNsecs };

  struct timespec startTime, endTime;
  clock_gettime(CLOCK_REALTIME, &startTime);

  while (mReleaseQueue.size() > 0)
  {
    CtlFrame* frame = mReleaseQueue.front();
    mCallbacks->ctlReceive(mCtlHandle, frame);
    mReleaseQueue.pop_front();
    if (mBurstModeSubmitPeriod > 0.0)
    {
      nanosleep((const struct timespec *) &releasePeriod, NULL);
    }
  }

  clock_gettime(CLOCK_REALTIME, &endTime);
  double startSecs = startTime.tv_sec + ((double) startTime.tv_nsec / 1.0E9);
  double endSecs = endTime.tv_sec + ((double) endTime.tv_nsec / 1.0E9);
  double elapsedSecs = endSecs - startSecs;
  double elapsedRate = (double) numFramesToRelease / elapsedSecs;

  FEMLOG(mFemId, logINFO) << "Release completed: " << numFramesToRelease << " frames released in " << elapsedSecs
      << " secs, rate: " << elapsedRate << " Hz";

}

void ExcaliburFemClient::freeAllFrames(void)
{

  while (mFrameQueue.size() > 0)
  {
    CtlFrame* frame = mFrameQueue.front();
    mCallbacks->ctlFree(mCtlHandle, frame);
    mFrameQueue.pop_front();
  }

}
void ExcaliburFemClient::command(unsigned int aCommand)
{

  unsigned int theCommand = 0;
  switch (aCommand)
  {
    case FEM_OP_STARTACQUISITION:
      this->startAcquisition();
      //this->toyAcquisition();
      break;

    case FEM_OP_STOPACQUISITION:
      this->stopAcquisition();
      break;

    case FEM_OP_RESET_UDP_COUNTER:
      FEMLOG(mFemId, logDEBUG) << "Resetting UDP frame counter";
      this->asicControlUdpCounterReset();
      break;

    default:
      theCommand = aCommand;
      FemClient::command(theCommand);
      break;
  }

}

void ExcaliburFemClient::toyAcquisition(void)
{
  FEMLOG(mFemId, logINFO) << "Running toy acquisition loop for numFrames=" << mNumFrames;
  for (unsigned int iBuffer = 0; iBuffer < mNumFrames; iBuffer++)
  {
    BufferInfo aBuffer = this->allocateCallback();
    this->receiveCallback(iBuffer, (time_t) 1234);
  }
  this->signalCallback(FemDataReceiverSignal::femAcquisitionComplete);
  FEMLOG(mFemId, logINFO) << "Ending toy acq loop";

}

void ExcaliburFemClient::startAcquisition(void)
{

  struct timespec startTime, endTime;

  clock_gettime(CLOCK_REALTIME, &startTime);

  // Default values for various acquisition parameters
  u32 acqMode, numAcq, bdCoalesce = 0;
  unsigned int numRxFrames = mNumFrames; // Default data receiver to receive specified number of frames
  bool bufferPreAllocate = false;
  bool clientAcquisitionControl = true;
  bool enableFrameCounterCheck = true;
  ExcaliburScanFunc theScanFunc = NULL;
  unsigned int executeCmd = asicPixelMatrixRead;
  mpx3CounterSelect counterSelect = mMpx3CounterSelect;
  bool doMatrixClearFirst = true;

  // Select various parameters based on operation mode
  switch (mOperationMode)
  {

    case excaliburOperationModeNormal:
      acqMode = ACQ_MODE_NORMAL;
      numAcq = 0; // Let the acquire config command configure all buffers in this mode
      bdCoalesce = 1;
      mEnableDeferredBufferRelease = false;
      break;

    case excaliburOperationModeBurst:
      acqMode = ACQ_MODE_BURST;
      numAcq = mNumFrames;
      bdCoalesce = 1;
      mEnableDeferredBufferRelease = true;
      enableFrameCounterCheck = false;
      bufferPreAllocate = true;
      break;

    case excaliburOperationModeDacScan:
      acqMode = ACQ_MODE_NORMAL;
      numAcq = 0;
      bdCoalesce = 1;
      mEnableDeferredBufferRelease = false;
      enableFrameCounterCheck = false;
      numRxFrames = this->dacScanNumSteps(); // Override number of frames to receive based on number of steps in scan
      clientAcquisitionControl = false; // FEM will be in control of acquisition sequence for DAC scan
      theScanFunc = &ExcaliburFemClient::dacScanExecute; // Set scan function pointer to DAC scan execute member function
      break;

    case excaliburOperationModeMatrixRead:
      acqMode = ACQ_MODE_NORMAL;
      numAcq = 0;
      bdCoalesce = 1;
      mEnableDeferredBufferRelease = false;
      enableFrameCounterCheck = false;
      numRxFrames = 1; // Override number of frames for a single read of the pixel matrix
      executeCmd = asicPixelConfigRead; // Override default execute command for this mode
      doMatrixClearFirst = false;
      break;

    case excaliburOperationModeHistogram:
      // Deliberate fall-thru as histogram mode not yet supported

    default:
    {
      std::ostringstream msg;
      msg << "Cannot start acquisition, illegal operation mode specified: " << mOperationMode;
      throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalOperationMode,
                               msg.str());
    }
      break;
  }

  // Select LFSR decoding and data reordering modes based on defaults and counter depth

  asicLfsrDecodeMode lfsrMode;
  asicDataReorderMode reorderMode = mAsicDataReorderMode;
  if (mLfsrBypassEnable)
  {
      FEMLOG(mFemId, logDEBUG) << "LFSR decoding bypass is enabled";
  }
  switch (mMpx3OmrParams[0].counterDepth)
  {
    case counterDepth1:
      lfsrMode = lfsr12Bypass;
      reorderMode = rawDataMode;
      enableFrameCounterCheck = false;
      break;
    case counterDepth6:
      lfsrMode = mLfsrBypassEnable ? lfsr6Bypass : lfsr6Enable;
      break;
    case counterDepth12:
    case counterDepth24:
      lfsrMode = mLfsrBypassEnable ? lfsr12Bypass : lfsr12Enable;
      break;
    default:
    {
      std::ostringstream msg;
      msg << "Cannot start acquisition, illegal counter depth specified: "
          << mMpx3OmrParams[0].counterDepth;
      throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalCounterDepth,
                               msg.str());
    }
      break;
  }

  // Reset the 10GigE UDP counters on the FEM unless this is a matrix read of counter 0 in 24-bit
  // mode, in which case the frame counter should increment

//  if ((mMpx3OmrParams[0].counterDepth == counterDepth24) &&
//      (mOperationMode == excaliburOperationModeMatrixRead) &&
//      (mMpx3CounterSelect == mpx3Counter0))
  if (mMpx3OmrParams[0].counterDepth == counterDepth24)
  {
//    FEMLOG(mFemId, logDEBUG) << "Not resetting UDP frame counter in 24-bit C0 read acquisition";
    FEMLOG(mFemId, logDEBUG) << "Not resetting UDP frame counter in 24-bit acquisition";
  }
  else
  {
    FEMLOG(mFemId, logDEBUG) << "Resetting UDP frame counter";
    this->asicControlUdpCounterReset();
  }

  // Configure the 10GigE UDP interface on the FEM
  FEMLOG(mFemId, logDEBUG) << "Configuring UDP data interface: source IP:" << mDataSourceIpAddress << " MAC:"
      << mDataSourceMacAddress << " port:" << mDataSourcePort << " dest IP:" << mDataDestIpAddress[0]
      << " MAC:" << mDataDestMacAddress[0] << " port:" << mDataDestPort[0];

  // Validate the farm mode LUT parameters, determining the number of consecutive valid entries
  u32 valid_lut_entries = 0;
  while ((mDataDestMacAddress[valid_lut_entries] != "00:00:00:00:00:00") &&
      (mDataDestIpAddress[valid_lut_entries] != "0.0.0.0") &&
      (mDataDestPort[valid_lut_entries] > 0))
  {
    valid_lut_entries++;
  }
  FEMLOG(mFemId, logDEBUG) << "UDP farm mode configuration has " << valid_lut_entries << " valid LUT entries";

  // Determine the number of farm mode destinations to use, warning and truncating if this is greater
  // than the number of valid LUT entries
  if (mDataFarmModeNumDestinations > valid_lut_entries)
  {
    FEMLOG(mFemId, logWARNING) << "Requested number of farm mode destinations " <<
        mDataFarmModeNumDestinations << "exceeds valid LUT entries, truncating";
    mDataFarmModeNumDestinations = valid_lut_entries;
  }
  FEMLOG(mFemId, logDEBUG) << "Setting number of UDP farm mode destinations to " << mDataFarmModeNumDestinations;

  // For 24-bit mode expand out the LUT to double-up consecutive entries, as the FEM
  // sends two frames per image (C1 and C0), which both need to go to the same readout node
  bool expand_lut = false;
  unsigned int dataFarmModeNumDestinations = mDataFarmModeNumDestinations;
  std::string dataDestMacAddress[kFarmModeLutSize];
  std::string dataDestIpAddress[kFarmModeLutSize];
  unsigned int dataDestPort[kFarmModeLutSize];

  if (mMpx3OmrParams[0].counterDepth == counterDepth24)
  {
      expand_lut = true;
      dataFarmModeNumDestinations *= 2;
      FEMLOG(mFemId, logDEBUG) << "Expanding farm mode LUT to " << dataFarmModeNumDestinations
              << " to accommodate 24 bit mode readout";
  }
  for (unsigned int idx = 0, expand_idx = 0; idx < mDataFarmModeNumDestinations; idx++, expand_idx++)
  {
      dataDestMacAddress[expand_idx] = mDataDestMacAddress[idx];
      dataDestIpAddress[expand_idx] = mDataDestIpAddress[idx];
      dataDestPort[expand_idx] = mDataDestPort[idx];
      if (expand_lut) {
          expand_idx++;
          dataDestMacAddress[expand_idx] = mDataDestMacAddress[idx];
          dataDestIpAddress[expand_idx] = mDataDestIpAddress[idx];
          dataDestPort[expand_idx] = mDataDestPort[idx];
      }
  }

  // Set the number of farm mode destination nodes in the top-level control register - note this is
  // distinct from the underlying 10GigE UDP firmware block
  this->asicControlFarmModeNumDestinationsSet(dataFarmModeNumDestinations);

  // Reset the LUT counter in the top-level block so each acquisition starts sending data to the
  // same node
  this->asicControlFarmModeLutReset();

  // Load the UDP core and farm mode configuration into the 10GigE UDP block on the FEM
  u32 rc = this->configUDP(mDataSourceMacAddress, mDataSourceIpAddress, mDataSourcePort,
                           dataDestMacAddress, dataDestIpAddress, dataDestPort, mDataDestPortOffset,
                           dataFarmModeNumDestinations, mDataFarmModeEnable);
  if (rc != 0)
  {
    throw FemClientException((FemClientErrorCode) excaliburFemClientUdpSetupFailed,
                             "Failed to set up FEM 10GigE UDP data interface");
  }

  // Execute a fast matrix clear if necessary for this mode
  if (doMatrixClearFirst)
  {
    FEMLOG(mFemId, logDEBUG) << "Executing ASIC fast matrix clear";
    this->asicControlFastMatrixClear();
    usleep(10);
  }

  // Set up counter depth for ASIC control based on current OMR settings
  this->asicControlCounterDepthSet(mMpx3OmrParams[0].counterDepth);

  // Set LFSR decode mode
  this->asicControlLfsrDecodeModeSet(lfsrMode);

  // Set ASIC data reordering mode
  this->asicControlDataReorderModeSet(reorderMode);

  // Set up the readout length in clock cycles for the ASIC control block
  unsigned int readoutLengthCycles = this->asicReadoutLengthCycles();
  this->asicControlReadoutLengthSet(readoutLengthCycles);

  // Set up the acquisition DMA controller and arm it, based on operation mode
  unsigned int dmaSize = this->asicReadoutDmaSize();
  //FEMLOG(mFemId, logDEBUG) << "Configuring DMA controller";
  this->acquireConfig(acqMode, dmaSize, 0, numAcq, bdCoalesce);
  //FEMLOG(mFemId, logDEBUG) << "Starting DMA controller";
  this->acquireStart();
  //FEMLOG(mFemId, logDEBUG) << "Done";


  // Create a data receiver object if enabled
  if (mDataReceiverEnable)
  {
    try
    {
      mFemDataReceiver = new FemDataReceiver(mDataDestPort[0]);
    }
    catch (boost::system::system_error &e)
    {
      std::ostringstream msg;
      msg << "Failed to create FEM data receiver: " << e.what();
      throw FemClientException((FemClientErrorCode) excaliburFemClientDataReceviverSetupFailed,
                               msg.str());
    }

    // Pre-allocate frame buffers for data receiver if necessary
    if (bufferPreAllocate)
    {
      this->preallocateFrames(numRxFrames);
    }

    // Register callbacks for data receiver
    mFemDataReceiver->registerCallbacks(&mCallbackBundle);

    // Set up the number of frames, acquisition period and time for the receiver thread
    mFemDataReceiver->setNumFrames(numRxFrames);
    mFemDataReceiver->setAcquisitionPeriod(mAcquisitionPeriodMs);
    mFemDataReceiver->setAcquisitionTime(mAcquisitionTimeMs);

    // Set up frame length and header sizes for the data receiver thread
    mFemDataReceiver->setFrameHeaderLength(8);
    mFemDataReceiver->setFrameHeaderPosition(headerAtStart);
    mFemDataReceiver->setNumSubFrames(mNumSubFrames);

    unsigned int frameDataLengthBytes = this->frameDataLengthBytes();
    mFemDataReceiver->setFrameLength(frameDataLengthBytes);

    bool hasFrameCounter = (reorderMode == reorderedDataMode) ? true : false;
    FEMLOG(mFemId, logDEBUG) << "Setting frame counter mode to " << (hasFrameCounter ? "true" : "false");
    mFemDataReceiver->enableFrameCounter(hasFrameCounter);
    mFemDataReceiver->enableFrameCounterCheck(enableFrameCounterCheck);

    // Start the data receiver thread
    mFemDataReceiver->startAcquisition();

  }
  else
  {
      FEMLOG(mFemId, logDEBUG) << "Data receiver thread is NOT enabled";
  }

  // If the client is in control of this acquisition mode, set up and start the acquisition
  if (clientAcquisitionControl)
  {

    // Setup of shutters and frame counters is dependent on readout mode

    switch (mMpx3OmrParams[0].readWriteMode)
    {
      case sequentialReadWriteMode:
      {
        // Set up the number of frames to be acquired in the ASIC control block
        this->asicControlNumFramesSet(numRxFrames);

        // Set up the acquisition time in the ASIC control block, converting from milliseconds
        // to microseconds. Set both shutters to the same value (why??)
        unsigned int shutterTime = mAcquisitionTimeMs * 1000;
        this->asicControlShutterDurationSet(shutterTime, shutterTime);
      }
        break;

      case continuousReadWriteMode:
      {
        // In continuous mode, force the counter select to start with counter 1
        counterSelect = mpx3Counter1;

        // In this mode, shutter 1 controls the individual frame duration ...
        unsigned int shutter1Time = mAcquisitionTimeMs * 1000;

        // ... and shutter 0 controls the overall acquisition duration, i.e. should be
        // set to the acquisition time multiplied by the number of frames
        unsigned int shutter0Time = (mAcquisitionTimeMs * 1000) * numRxFrames;

        FEMLOG(mFemId, logDEBUG) << "CRW mode, setting shutter 0 duration to " << shutter0Time
            << "us and shutter 1 duration to " << shutter1Time << "us";
        this->asicControlShutterDurationSet(shutter0Time, shutter1Time);

        // Set frame counter to zero is this mode
        this->asicControlNumFramesSet(0);

      }
        break;

      default:
      {
        std::ostringstream msg;
        msg << "Cannot start acquisition, illegal read write modeh specified: "
            << mMpx3OmrParams[0].readWriteMode;
        throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalReadWriteMode,
                                 msg.str());
      }
        break;

    }

    // Build chip mask from the enable flags and determine which is the first chip active - this is used
    // to select settings for building the OMR for readout transactions, where the OMR is broadcast
    // to all chips
    int firstChipActive = -1;
    unsigned int chipMask = 0;
    for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
    {
      if (mMpx3Enable[iChip])
      {
        chipMask |= ((unsigned int) 1 << (7 - iChip));
        if (firstChipActive == -1)
        {
          firstChipActive = iChip;
        }
      }
    }
    FEMLOG(mFemId, logDEBUG) << "Chip mask: 0x" << std::hex << chipMask << std::dec
            << " First chip active: " << firstChipActive;

    // Set up the ASIC mux based on calculated chip mask
    this->asicControlMuxSet(chipMask);

    // Check if test pulses are enabled on any enabled chip, if so set the global test pulse enable flag
    for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
    {
      if (mMpx3Enable[iChip] && mMpx3OmrParams[iChip].testPulseEnable)
      {
        mMpx3GlobalTestPulseEnable = true;
      }
    }

    if (mMpx3GlobalTestPulseEnable)
    {
        FEMLOG(mFemId, logDEBUG) << "Enabling test pulse injection on FEM (count=" << mMpx3TestPulseCount << ")";
      this->asicControlTestPulseCountSet(mMpx3TestPulseCount);
    }

    // Set up OMR mode and execute command based on which counter is selected
    mpx3OMRMode omrMode = (mpx3OMRMode) 0;
    switch (counterSelect)
    {
      case mpx3Counter0:
        omrMode = readPixelMatrixC0;
        break;

      case mpx3Counter1:
        omrMode = readPixelMatrixC1;
        break;

      default:
      {
        std::ostringstream msg;
        msg << "Cannot start acquisition, illegal counter select specified: " << mMpx3CounterSelect;
        throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalCounterSelect,
                                 msg.str());
      }

        break;
    }

    // Set up the OMR for readout using the first active chip to retrieve
    // default values for OMR fields
    mpx3Omr theOmr = this->mpx3OMRBuild(firstChipActive, omrMode);
    //FEMLOG(mFemId, logDEBUG) << "Using MPX OMR: 0x" << std::hex << theOmr.raw << std::dec;
    this->asicControlOmrSet(theOmr);

    // Enable test pulses in the execute command if necessary
    if (mMpx3GlobalTestPulseEnable)
    {
      executeCmd |= asicTestPulseEnable;
    }

    // Build the configuration register based on trigger mode and polarity
    unsigned int controlConfigRegister = 0;

    if (mOperationMode != excaliburOperationModeMatrixRead)
    {
      switch (mTriggerMode)
      {
        case excaliburTriggerModeInternal:
          controlConfigRegister |= internalTriggerMode;
          break;

        case excaliburTriggerModeExternal:
          controlConfigRegister |= externalTriggerMode;
          break;

        case excaliburTriggerModeSync:
          controlConfigRegister |= externalSyncMode;
          break;

        default:
        {
          std::ostringstream msg;
          msg << "Cannot start acquisition, illegal trigger mode specified: " << mTriggerMode;
          throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalTriggerMode,
                                   msg.str());
        }
          break;
      }
    }
    else
    {
      FEMLOG(mFemId, logDEBUG) << "Forcing trigger mode to internal for matrix counter read";
      controlConfigRegister |= internalTriggerMode;
    }

    switch (mTriggerPolarity)
    {
      case excaliburTriggerPolarityActiveHigh:
        controlConfigRegister |= externalTrigActiveHigh;
        break;

      case excaliburTriggerPolarityActiveLow:
        controlConfigRegister |= externalTrigActiveLow;
        break;

      default:
      {
        std::ostringstream msg;
        msg << "Cannot start acquisition, illegal trigger polarity specified: " << mTriggerPolarity;
        throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalTriggerPolarity,
                                 msg.str());
      }
        break;
    }

    // Set the control configuration register accordingly
    FEMLOG(mFemId, logDEBUG) << "Setting control configuration register to 0x" << std::hex << controlConfigRegister
        << std::dec;
    this->asicControlConfigRegisterSet(controlConfigRegister);

    // Execute the command
    FEMLOG(mFemId, logDEBUG) << "Sending execute command 0x" << std::hex << executeCmd << std::dec;
    this->asicControlCommandExecute((asicControlCommand) executeCmd);

  }
  else
  {
    // Invoke the scan member execute function defined above
    if (theScanFunc != NULL)
    {
        FEMLOG(mFemId, logDEBUG) << "Executing autonomous scan sequence with " << numRxFrames << " steps";
      (this->*(theScanFunc))();
    }
    else
    {
      throw FemClientException((FemClientErrorCode) excaliburFemClientMissingScanFunction,
                               "Missing scan function for this acquisition mode");
    }

  }

  clock_gettime(CLOCK_REALTIME, &endTime);

  double startSecs = startTime.tv_sec + ((double) startTime.tv_nsec / 1.0E9);
  double endSecs = endTime.tv_sec + ((double) endTime.tv_nsec / 1.0E9);
  double elapsedSecs = endSecs - startSecs;

  FEMLOG(mFemId, logDEBUG) << "startAcquisition call took " << elapsedSecs << " secs";
}

void ExcaliburFemClient::stopAcquisition(void)
{

  u32 framesRead = 0;
  bool doFullAcqStop = true;

  // Check if acquisition is active in data receiver. If so, perform the steps necessary to bring the
  // system to a graceful halt. This is dependent on the operation mode currently in force.
  if (mFemDataReceiver != 0)
  {
    if (mFemDataReceiver->acqusitionActive())
    {
      switch (mOperationMode)
      {
        case excaliburOperationModeNormal:
        {
          FEMLOG(mFemId, logINFO) << "Normal mode acquisition is still active, sending stop to FEM ASIC control";
          this->asicControlCommandExecute(asicStopAcquisition);

          // Wait at least the acquisition time (shutter time) plus 500us readout time before
          // checking the state to allow last frame to be read out
          usleep((mAcquisitionTimeMs * 1000) + 500);

          // Read control state register for diagnostics
          u32 ctrlState = this->rdmaRead(kExcaliburAsicCtrlState1);
          framesRead = this->rdmaRead(kExcaliburAsicCtrlFrameCount);
          FEMLOG(mFemId, logINFO) << "FEM ASIC control has completed " << framesRead
              << " frames, control state register1: 0x" << std::hex << ctrlState << std::dec;

        }
          break;
        case excaliburOperationModeBurst: // Deliberate fall-thru for these modes where async stop not supported
        case excaliburOperationModeHistogram:
        case excaliburOperationModeMatrixRead:
            FEMLOG(mFemId, logWARNING)
              << "Cannot complete asynchronous stop in this operation mode, ignoring stop command while running";
          doFullAcqStop = false;
          break;

        case excaliburOperationModeDacScan:
        {
#ifdef MPX3_0
          FEMLOG(mFemId, logWARNING) << "Current FEM firmware does not support asynchronous stop of DAC scan";
          doFullAcqStop = false;
#else
          FEMLOG(mFemId, logINFO) << "Performing asynchronous stop of DAC scan";
          framesRead = this->dacScanAbort();

#endif
        }
          break;

        default:
        {
          std::ostringstream msg;
          msg << "Cannot stop acquisition, illegal operation mode specified: " << mOperationMode;
          throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalOperationMode,
                                   msg.str());
        }
          break;

      } // End of switch

      // Wait until DMA engine has transferred out the number of frames read out by the
      // ASIC control block. This loop will repeat until ten times the frame acquisition
      // length, after which it will assume that the completion has timed out
      bool acqCompletePending = true;
      int numAcqCompleteLoops = 0;
      int maxAcqCompleteLoops = 10;

      while (acqCompletePending && (numAcqCompleteLoops < maxAcqCompleteLoops))
      {
        FemAcquireStatus acqState = this->acquireStatus();
        FEMLOG(mFemId, logINFO) << "Asynchronous stop of DMA acquisition loop: " << numAcqCompleteLoops
            << " attempts, ACQ state: " << acqState.state << " sent BDs: " << acqState.totalSent;

        if (acqState.totalSent >= framesRead * 2)
        {
          FEMLOG(mFemId, logDEBUG) << "DMA controller has transmitted " << framesRead << " frames OK";
          acqCompletePending = false;
        }
        else
        {
          numAcqCompleteLoops++;
          usleep(mAcquisitionTimeMs * 1000);
        }
      }
      if (acqCompletePending)
      {
        FEMLOG(mFemId, logERROR) << "ERROR: DMA transfer of " << framesRead
            << " failed to complete in expected time during async stop";
      }

    }
  }

  if (doFullAcqStop)
  {

    // Send ACQUIRE stop command to the FEM
    //FEMLOG(mFemId, logDEBUG) << "Sending acquire STOP to FEM";
    this->acquireStop();

    if (mFemDataReceiver != 0)
    {
      // Ensure that the data receiver has stopped cleanly
      mFemDataReceiver->stopAcquisition(framesRead);

      // Delete the data receiver
      delete (mFemDataReceiver);
      mFemDataReceiver = 0;
    }

    // Reset ASIC control firmware block
    //FEMLOG(mFemId, logDEBUG) << "Sending ASIC control reset to FEM";
    this->asicControlReset();

    //FEMLOG(mFemId, logDEBUG) << "End of doFullAcqStop clause";
  }
}

void ExcaliburFemClient::triggerModeSet(unsigned int aTriggerMode)
{
  // Store trigger mode for use during acquisition start
  mTriggerMode = (excaliburTriggerMode) aTriggerMode;
}

void ExcaliburFemClient::triggerPolaritySet(unsigned int aTriggerPolarity)
{
  // Store trigger polarity for use during acquisition start
  mTriggerPolarity = (excaliburTriggerPolarity) aTriggerPolarity;
}

void ExcaliburFemClient::operationModeSet(unsigned int aOperationMode)
{
  // Store operation mode for use during acquisition start
  mOperationMode = (excaliburOperationMode) aOperationMode;
}

void ExcaliburFemClient::numFramesSet(unsigned int aNumFrames)
{
  // Store number of frames to be received for use during acquisition start
  mNumFrames = aNumFrames;
}

void ExcaliburFemClient::acquisitionPeriodSet(unsigned int aPeriodMs)
{
  // Store acquisition period for use during acquisition start
  mAcquisitionPeriodMs = aPeriodMs;
}

void ExcaliburFemClient::acquisitionTimeSet(unsigned int aTimeMs)
{
  // Store acquisition time for use during acquisition start
  mAcquisitionTimeMs = aTimeMs;
}

void ExcaliburFemClient::burstModeSubmitPeriodSet(double aPeriod)
{

  // Store burst mode submit period for use during acquisition
  mBurstModeSubmitPeriod = aPeriod;
  FEMLOG(mFemId, logDEBUG) << "Set burst mode submit period to " << aPeriod;

}

void ExcaliburFemClient::numTestPulsesSet(unsigned int aNumTestPulses)
{
  // Store number of test pulses for use during acquisition start
  mMpx3TestPulseCount = aNumTestPulses;
}

void ExcaliburFemClient::lfsrBypassEnableSet(unsigned int aBypassEnable)
{
  // Store LFSR bypass enable
  mLfsrBypassEnable = (bool) aBypassEnable;
}

unsigned int ExcaliburFemClient::asicReadoutDmaSize(void)
{

  // Get counter bit depth of ASIC
  unsigned int counterBitDepth = this->mpx3CounterBitDepth(mMpx3OmrParams[0].counterDepth);

  // DMA size is (numRows * numCols * (numAsics/2) counterDepth /  8 bits per bytes
  unsigned int theLength = (kNumRowsPerAsic * kNumColsPerAsic * (kNumAsicsPerFem / 2)
      * counterBitDepth) / 8;

  return theLength;
}

unsigned int ExcaliburFemClient::asicReadoutLengthCycles(void)
{

  unsigned int counterBitDepth = this->mpx3CounterBitDepth(mMpx3OmrParams[0].counterDepth);
  unsigned int readoutBitWidth = this->mpx3ReadoutBitWidth(mMpx3OmrParams[0].readoutWidth);

  unsigned int theLength = (kNumRowsPerAsic * kNumColsPerAsic * counterBitDepth) / readoutBitWidth;

  return theLength;

}

unsigned int ExcaliburFemClient::frameDataLengthBytes(void)
{

  unsigned int frameDataLengthBytes = 0;

  // Get the counter bit depth
  unsigned int counterBitDepth = this->mpx3CounterBitDepth(mMpx3OmrParams[0].counterDepth);

  // Calculate raw length of ASIC data in bits
  unsigned int asicDataLengthBits = kNumRowsPerAsic * kNumColsPerAsic * kNumAsicsPerFem
      * counterBitDepth;

  // Get the frame length in bytes. In 12/24-bit re-ordered mode, reordering expands each 12 bit ASIC
  // counter up to 16 bits (two bytes). In 6-bit re-ordered mode, reordering expands each 6 bit ASIC up
  // to 8 bits (one byte).
  if (mAsicDataReorderMode == reorderedDataMode)
  {
    switch (mMpx3OmrParams[0].counterDepth)
    {
      case counterDepth1:
        frameDataLengthBytes = asicDataLengthBits / 8; // 1-bit is always forced to raw data mode
        //frameDataLengthBytes = 90112;
        break;
      case counterDepth6:
        frameDataLengthBytes = ((asicDataLengthBits * 8) / 6) / 8;
        break;
      case counterDepth12:
      case counterDepth24:
        frameDataLengthBytes = ((asicDataLengthBits * 16) / 12) / 8;
        //frameDataLengthBytes = 768432;
        break;

      default:
        break;
    }
  }
  else
  {
    frameDataLengthBytes = asicDataLengthBits / 8;
  }

  // Add on size of frame counter(s), which is 8 bytes per subframe
  //frameDataLengthBytes += (mNumSubFrames * 8);

  return frameDataLengthBytes;

}

void ExcaliburFemClient::frontEndInitialise(void)
{

  FEMLOG(mFemId, logDEBUG) << "**** Front-end initialise ****";
  sleep(3);

  // Initialise front-end DACs
  this->frontEndDacInitialise();

  // Reset the ASIC control f/w block and ASICS
  this->asicControlReset();
  this->asicControlAsicReset();

  FEMLOG(mFemId, logDEBUG) << "**** Front-end init done ****";

}

void ExcaliburFemClient::dataReceiverEnable(unsigned int aEnable)
{
  if (aEnable > 0)
  {
    mDataReceiverEnable = true;
  }
  else
  {
    mDataReceiverEnable = false;
  }
}

unsigned int ExcaliburFemClient::frameCountGet(void)
{
  return (unsigned int) (this->rdmaRead(kExcaliburAsicCtrlFrameCount - 1));
}

unsigned int ExcaliburFemClient::controlStateGet(void)
{
  return (unsigned int) (this->rdmaRead(kExcaliburAsicCtrlState1));
}

void ExcaliburFemClient::dataAddrParamSet(excaliburDataAddrParam aAddrParam, std::size_t size,
    std::size_t offset, const char** aAddrValues)
{

  std::size_t max_size;
  switch (aAddrParam)
  {
    case excaliburDataAddrSourceIp:
    case excaliburDataAddrSourceMac:
      max_size = 1;
      break;

    case excaliburDataAddrDestIp:
    case excaliburDataAddrDestMac:
      max_size = kFarmModeLutSize;
      break;

    default:
      std::ostringstream msg;
      msg << "Illegal data address parameter specified: " << aAddrParam;
      throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalDataParam, msg.str());
      break;
  }

  if ((size  + offset) > max_size)
  {
    std::ostringstream msg;
    msg << "Data address parameter: " << excaliburDataAddrParamName[aAddrParam]
        << " indexing error: size " << size << " and offset " << offset
        << " exceeds max size " << max_size;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalDataParam, msg.str());
  }

  for (std::size_t val_idx = 0; val_idx < size; val_idx++)
  {
    std::size_t param_idx = val_idx + offset;
    switch (aAddrParam)
    {

      case excaliburDataAddrSourceIp:
        mDataSourceIpAddress = aAddrValues[val_idx];
        break;
      case excaliburDataAddrSourceMac:
        mDataSourceMacAddress = aAddrValues[val_idx];
        break;
      case excaliburDataAddrDestIp:
        mDataDestIpAddress[param_idx] = aAddrValues[val_idx];
        break;
      case excaliburDataAddrDestMac:
        mDataDestMacAddress[param_idx] = aAddrValues[val_idx];
        break;
      default:
        std::ostringstream msg;
        msg << "Illegal data address parameter specified: " << aAddrParam;
        throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalDataParam, msg.str());
        break;
    }
  }
}

void ExcaliburFemClient::dataPortParamSet(excaliburDataPortParam aPortParam, std::size_t size,
   std::size_t offset, const unsigned int* aPortValues)
{
  std::size_t max_size;
  switch (aPortParam)
  {
    case excaliburDataPortSource:
      max_size = 1;
      break;

    case excaliburDataPortDest:
      max_size = kFarmModeLutSize;
      break;

    default:
      std::ostringstream msg;
      msg << "Illegal data port parameter specified: " << aPortParam;
      throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalDataParam, msg.str());
      break;
  }

  if ((size  + offset) > max_size)
  {
    std::ostringstream msg;
    msg << "Data port parameter: " << excaliburDataPortParamName[aPortParam]
        << " indexing error: size " << size << " and offset " << offset
        << " exceeds max size " << max_size;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalDataParam, msg.str());
  }

  for (std::size_t val_idx = 0; val_idx < size; val_idx++)
  {
    std::size_t param_idx = val_idx + offset;
    switch (aPortParam)
    {
      case excaliburDataPortSource:
        mDataSourcePort = aPortValues[val_idx];
        break;
      case excaliburDataPortDest:
        mDataDestPort[param_idx] = aPortValues[val_idx];
        break;
      default:
        std::ostringstream msg;
        msg << "Illegal data port parameter specified: " << aPortParam;
        throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalDataParam, msg.str());
        break;
    }
  }
}

void ExcaliburFemClient::dataDestPortOffsetSet(unsigned int aDestPortOffset)
{
    mDataDestPortOffset = aDestPortOffset;
}

void ExcaliburFemClient::dataFarmModeNumDestinationsSet(unsigned int aNumDestinations)
{
  if (aNumDestinations > kFarmModeLutSize/2)
  {
    std::ostringstream msg;
    msg << "UDP data farm mode number of destinations requested (" << aNumDestinations
        << ") exceeds maximum (" << kFarmModeLutSize/2;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalDataParam, msg.str());
  }
  mDataFarmModeNumDestinations = aNumDestinations;
}

void ExcaliburFemClient::dataFarmModeEnableSet(unsigned int aEnable)
{
    mDataFarmModeEnable = (aEnable > 0) ? true : false;
}



void ExcaliburFemClient::firmwareVersionGet(int* versionValues)
{
  *(versionValues++) = (int)this->rdmaRead(kExcaliburSp3ConfigFirmwareVersion);
  *(versionValues++) = (int)this->rdmaRead(kExcaliburSp3TopFirmwareVersion);
  *(versionValues++) = (int)this->rdmaRead(kExcaliburSp3BotFirmwareVersion);
  *(versionValues++) = (int)this->rdmaRead(KExcaliburV5FirmwareVersion);
}
