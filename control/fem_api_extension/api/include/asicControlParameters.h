/*
 * asicControlParameters.h - addresses, settings & parameters for
 * the EXCALIBUR FEM ASIC control firmware block
 *
 *  Created on: Mar 21, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef EXCALIBURFEMRDMAADDRESSES_H_
#define EXCALIBURFEMRDMAADDRESSES_H_

//#define LEGACY_RDMA_ADDRESS_SCHEME
#include "dataTypes.h"

// RDMA address of top-level firmware control block and its registers
#ifdef LEGACY_RDMA_ADDRESS_SCHEME
const u32 kExcaliburTopLevelControlAddr = 0x30000000;
#else
const u32 kExcaliburTopLevelControlAddr = 0x06000000;
#endif
const u32 kExcaliburDataReorderMode = kExcaliburTopLevelControlAddr + 1;
const u32 kExcaliburUdpCounterReset = kExcaliburTopLevelControlAddr + 2;
const u32 kExcaliburFarmModeLutReset = kExcaliburTopLevelControlAddr + 4;
const u32 kExcaliburFarmModeLutCount = kExcaliburTopLevelControlAddr + 5;

// RDMA address of the ASIC control block and its registers
#ifdef LEGACY_RDMA_ADDRESS_SCHEME
const u32 kExcaliburAsicControlAddr = 0x48000000;
#else
const u32 kExcaliburAsicControlAddr = 0x09000000;
#endif

const u32 kExcaliburAsicMuxSelect = kExcaliburAsicControlAddr + 0;
const u32 kExcaliburAsicControlReg = kExcaliburAsicControlAddr + 1;
const u32 kExcaliburAsicOmrBottom = kExcaliburAsicControlAddr + 2;
const u32 kExcaliburAsicOmrTop = kExcaliburAsicControlAddr + 3;
const u32 kExcaliburAsicConfig1Reg = kExcaliburAsicControlAddr + 4;
const u32 kExcaliburAsicLfsrReg = kExcaliburAsicControlAddr + 5;
const u32 kExcaliburAsicShutter0Counter = kExcaliburAsicControlAddr + 6;
const u32 kExcaliburAsicShutter1Counter = kExcaliburAsicControlAddr + 7;
const u32 kExcaliburAsicFrameCounter = kExcaliburAsicControlAddr + 8;
const u32 kExcaliburAsicPixelCounterDepth = kExcaliburAsicControlAddr + 9;
const u32 kExcaliburAsicShutterResolution = kExcaliburAsicControlAddr + 10;
const u32 kExcaliburAsicReadoutLength = kExcaliburAsicControlAddr + 11;
const u32 kExcaliburAsicTestPulseCount = kExcaliburAsicControlAddr + 12;

const u32 KExcaliburV5FirmwareVersion = kExcaliburAsicControlAddr + 16;
const u32 kExcaliburAsicCtrlState1 = kExcaliburAsicControlAddr + 17;
const u32 kExcaliburAsicCtrlFrameCount = kExcaliburAsicControlAddr + 20;

#ifdef LEGACY_RDMA_ADDRESS_SCHEME
const u32 kExcaliburAsicDpmRdmaAddress = 0x50000000;
#else
const u32 kExcaliburAsicDpmRdmaAddress = 0x0A000000;
#endif

#ifdef LEGACY_RDMA_ADDRESS_SCHEME
const unsigned int kPixelConfigBaseAddr = 0x30000000;
#else
const unsigned int kPixelConfigBaseAddr = 0x70000000;
#endif

const unsigned int kExcaliburSp3ConfigAddr = 0x10000000;
const unsigned int kExcaliburSp3ConfigFirmwareVersion = kExcaliburSp3ConfigAddr + 16;
const unsigned int kExcaliburSp3TopAddr = 0x20000000;
const unsigned int kExcaliburSp3TopFirmwareVersion = kExcaliburSp3TopAddr + 16;
const unsigned int kExcaliburSp3BotAddr = 0x30000000;
const unsigned int kExcaliburSp3BotFirmwareVersion = kExcaliburSp3BotAddr + 16;


typedef enum
{
  unknownCommandExecute = -1,
  asicCommandWrite = 0x23,
  asicCommandRead = 0x25,
  asicPixelConfigLoad = 0x2b,
//	asicRunSequentialC0   = 0xa41,
//	asicRunSequentialC1   = 0x1241,
  asicPixelMatrixRead = 0x201,
  asicPixelConfigRead = 0x2601,
  asicTestPulseEnable = 0x4000,
  asicExternalTrigger = 0x20000000,
  asicStopAcquisition = 0x80000000

} asicControlCommand;

typedef enum
{
  unknownMode = -1, reorderedDataMode = 0, rawDataMode = 1

} asicDataReorderMode;

typedef enum
{
  unknownConfig = -1,
  internalTriggerMode = 0x0,
  externalTriggerMode = 0x8,
  externalSyncMode = 0x4,
  externalTrigActiveLow = 0x0,
  externalTrigActiveHigh = 0x2

} asicControlConfigSetting;

typedef enum
{
  lfsr12Bypass = 0, lfsr12Enable = 1, lfsr6Bypass = 2, lfsr6Enable = 3
} asicLfsrDecodeMode;

#endif /* EXCALIBURFEMRDMAADDRESSES_H_ */
