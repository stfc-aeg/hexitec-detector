/*
 * ExcaliburFemClientMpx3.cpp - ExcaliburFemClient methods for
 * setup and load of the MEDIPIX3 ASICs
 *
 *  Created on: May 17, 2012
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

void ExcaliburFemClient::mpx3DacSet(unsigned int aChipId, int aDacId, unsigned int aDacValue)
{

  // Map the API-level DAC ID onto the internal ID
  mpx3Dac dacIdx = mpx3DacIdGet(aDacId);
  if (dacIdx == unknownDacId)
  {
    std::ostringstream msg;
    msg << "Illegal DAC ID specified: " << aDacId;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalDacId, msg.str());
  }

  // Check chip ID is legal (noting that id = 0 implies all chips)
  if ((aChipId < 0) || (aChipId > kNumAsicsPerFem))
  {
    std::ostringstream msg;
    msg << "Illegal chip ID specified: " << aChipId;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalChipId, msg.str());
  }

  // If chip ID = 0, set the given DAC of all chips to the specified value. Otherwise set
  // the value for a particular chip and DAC (NB chip indexing offset from zero in API)
  if (aChipId == 0)
  {
    for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
    {
      mMpx3DacCache[iChip][dacIdx] = aDacValue;
    }
  }
  else
  {
    mMpx3DacCache[aChipId - 1][dacIdx] = aDacValue;
  }

}

void ExcaliburFemClient::mpx3DacSenseSet(unsigned int aChipId, int aDac)
{

  FEMLOG(mFemId, logDEBUG) << "DAC sense set chip=" << aChipId << " DAC=" << aDac;

  // Check chip ID is legal (noting that id = 0 implies all chips)
  if ((aChipId < 0) || (aChipId > kNumAsicsPerFem))
  {
    std::ostringstream msg;
    msg << "Illegal chip ID specified: " << aChipId;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalChipId, msg.str());
  }

  if (aChipId == 0)
  {
    for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
    {
      mMpx3OmrParams[iChip].dacSense = (unsigned int) aDac;
    }
  }
  else
  {
    mMpx3OmrParams[aChipId - 1].dacSense = (unsigned int) aDac;
  }

}

void ExcaliburFemClient::mpx3DacExternalSet(unsigned int aChipId, int aDac)
{

  FEMLOG(mFemId, logDEBUG) << "DAC external set chip=" << aChipId << " DAC=" << aDac;

  // Check chip ID is legal (noting that id = 0 implies all chips)
  if ((aChipId < 0) || (aChipId > kNumAsicsPerFem))
  {
    std::ostringstream msg;
    msg << "Illegal chip ID specified: " << aChipId;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalChipId, msg.str());
  }

  if (aChipId == 0)
  {
    for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
    {
      mMpx3OmrParams[iChip].dacExternal = (unsigned int) aDac;
    }
  }
  else
  {
    mMpx3OmrParams[aChipId - 1].dacExternal = (unsigned int) aDac;
  }

}

void ExcaliburFemClient::mpx3DacsWrite(unsigned int aChipId)
{

  // If chip ID = 0, loop over all chips and call this function recursively
  if (aChipId == 0)
  {
    for (unsigned int iChip = 1; iChip <= kNumAsicsPerFem; iChip++)
    {
      this->mpx3DacsWrite(iChip);
    }
  }
  else
  {
    // Internal chip index runs from 0 to 7
    unsigned int chipIdx = aChipId - 1;

    // Pack DAC values into u32 vector for upload to FEM
    std::vector<u32> dacValues(kNumAsicDpmWords, 0);

#ifdef MPX3_0
    dacValues[0] |= (u32)(mMpx3DacCache[chipIdx][tpRefBDac] & 0x1FF) << 23;
    dacValues[0] |= (u32)(mMpx3DacCache[chipIdx][tpRefADac] & 0x1FF) << 14;
    dacValues[0] |= (u32)(mMpx3DacCache[chipIdx][casDac] & 0x0FF) << 6;
    dacValues[0] |= (u32)(mMpx3DacCache[chipIdx][fbkDac] & 0x0FC) >> 2;

    dacValues[1] |= (u32)(mMpx3DacCache[chipIdx][fbkDac] & 0x003) << 30;
    dacValues[1] |= (u32)(mMpx3DacCache[chipIdx][tpRefDac] & 0x0FF) << 22;
    dacValues[1] |= (u32)(mMpx3DacCache[chipIdx][gndDac] & 0x0FF) << 14;
    dacValues[1] |= (u32)(mMpx3DacCache[chipIdx][rpzDac] & 0x0FF) << 6;
    dacValues[1] |= (u32)(mMpx3DacCache[chipIdx][tpBufferOutDac] & 0x0FC) >> 2;

    dacValues[2] |= (u32)(mMpx3DacCache[chipIdx][tpBufferOutDac] & 0x003) << 30;
    dacValues[2] |= (u32)(mMpx3DacCache[chipIdx][tpBufferInDac] & 0x0FF) << 22;
    dacValues[2] |= (u32)(mMpx3DacCache[chipIdx][delayDac] & 0x0FF) << 14;
    dacValues[2] |= (u32)(mMpx3DacCache[chipIdx][dacPixelDac] & 0x0FF) << 6;
    dacValues[2] |= (u32)(mMpx3DacCache[chipIdx][thresholdNDac] & 0x0FC) >> 2;

    dacValues[3] |= (u32)(mMpx3DacCache[chipIdx][thresholdNDac] & 0x003) << 30;
    dacValues[3] |= (u32)(mMpx3DacCache[chipIdx][discLsDac] & 0x0FF) << 22;
    dacValues[3] |= (u32)(mMpx3DacCache[chipIdx][discDac] & 0x0FF) << 14;
    dacValues[3] |= (u32)(mMpx3DacCache[chipIdx][shaperDac] & 0x0FF) << 6;
    dacValues[3] |= (u32)(mMpx3DacCache[chipIdx][ikrumDac] & 0x0FC) >> 2;

    dacValues[4] |= (u32)(mMpx3DacCache[chipIdx][ikrumDac] & 0x003) << 30;
    dacValues[4] |= (u32)(mMpx3DacCache[chipIdx][preampDac] & 0x0FF) << 22;
    dacValues[4] |= (u32)(mMpx3DacCache[chipIdx][threshold7Dac] & 0x1FF) << 13;
    dacValues[4] |= (u32)(mMpx3DacCache[chipIdx][threshold6Dac] & 0x1FF) << 4;
    dacValues[4] |= (u32)(mMpx3DacCache[chipIdx][threshold5Dac] & 0x1E0) >> 5;

    dacValues[5] |= (u32)(mMpx3DacCache[chipIdx][threshold5Dac] & 0x01F) << 27;
    dacValues[5] |= (u32)(mMpx3DacCache[chipIdx][threshold4Dac] & 0x1FF) << 18;
    dacValues[5] |= (u32)(mMpx3DacCache[chipIdx][threshold3Dac] & 0x1FF) << 9;
    dacValues[5] |= (u32)(mMpx3DacCache[chipIdx][threshold2Dac] & 0x1FF) << 0;

    dacValues[6] |= (u32)(mMpx3DacCache[chipIdx][threshold1Dac] & 0x1FF) << 23;
    dacValues[6] |= (u32)(mMpx3DacCache[chipIdx][threshold0Dac] & 0x1FF) << 14;
#else
    dacValues[0] |= (u32) (mMpx3DacCache[chipIdx][tpRefBDac] & 0x1FF) << 23;
    dacValues[0] |= (u32) (mMpx3DacCache[chipIdx][tpRefADac] & 0x1FF) << 14;
    dacValues[0] |= (u32) (mMpx3DacCache[chipIdx][casDac] & 0x0FF) << 6;
    dacValues[0] |= (u32) (mMpx3DacCache[chipIdx][fbkDac] & 0x0FC) >> 2;

    dacValues[1] |= (u32) (mMpx3DacCache[chipIdx][fbkDac] & 0x003) << 30;
    dacValues[1] |= (u32) (mMpx3DacCache[chipIdx][tpRefDac] & 0x0FF) << 22;
    dacValues[1] |= (u32) (mMpx3DacCache[chipIdx][gndDac] & 0x0FF) << 14;
    dacValues[1] |= (u32) (mMpx3DacCache[chipIdx][rpzDac] & 0x0FF) << 6;
    dacValues[1] |= (u32) (mMpx3DacCache[chipIdx][tpBufferOutDac] & 0x0FC) >> 2;

    dacValues[2] |= (u32) (mMpx3DacCache[chipIdx][tpBufferOutDac] & 0x003) << 30;
    dacValues[2] |= (u32) (mMpx3DacCache[chipIdx][tpBufferInDac] & 0x0FF) << 22;
    dacValues[2] |= (u32) (mMpx3DacCache[chipIdx][delayDac] & 0x0FF) << 14;
    dacValues[2] |= (u32) (mMpx3DacCache[chipIdx][discHDac] & 0x0FF) << 6;
    dacValues[2] |= (u32) (mMpx3DacCache[chipIdx][testDac] & 0x0FC) >> 2;

    dacValues[3] |= (u32) (mMpx3DacCache[chipIdx][testDac] & 0x003) << 30;
    dacValues[3] |= (u32) (mMpx3DacCache[chipIdx][discLDac] & 0x0FF) << 22;
    dacValues[3] |= (u32) (mMpx3DacCache[chipIdx][shaperTestDac] & 0x0FF) << 14;
    dacValues[3] |= (u32) (mMpx3DacCache[chipIdx][discLsDac] & 0x0FF) << 6;
    dacValues[3] |= (u32) (mMpx3DacCache[chipIdx][discDac] & 0x0FC) >> 2;

    dacValues[4] |= (u32) (mMpx3DacCache[chipIdx][discDac] & 0x003) << 30;
    dacValues[4] |= (u32) (mMpx3DacCache[chipIdx][shaperDac] & 0x0FF) << 22;
    dacValues[4] |= (u32) (mMpx3DacCache[chipIdx][ikrumDac] & 0x0FF) << 14;
    dacValues[4] |= (u32) (mMpx3DacCache[chipIdx][preampDac] & 0x0FF) << 6;
    dacValues[4] |= (u32) (mMpx3DacCache[chipIdx][threshold7Dac] & 0x1F8) >> 3;

    dacValues[5] |= (u32) (mMpx3DacCache[chipIdx][threshold7Dac] & 0x007) << 29;
    dacValues[5] |= (u32) (mMpx3DacCache[chipIdx][threshold6Dac] & 0x1FF) << 20;
    dacValues[5] |= (u32) (mMpx3DacCache[chipIdx][threshold5Dac] & 0x1FF) << 11;
    dacValues[5] |= (u32) (mMpx3DacCache[chipIdx][threshold4Dac] & 0x1FF) << 2;
    dacValues[5] |= (u32) (mMpx3DacCache[chipIdx][threshold3Dac] & 0x180) >> 7;

    dacValues[6] |= (u32) (mMpx3DacCache[chipIdx][threshold3Dac] & 0x07F) << 25;
    dacValues[6] |= (u32) (mMpx3DacCache[chipIdx][threshold2Dac] & 0x1FF) << 16;
    dacValues[6] |= (u32) (mMpx3DacCache[chipIdx][threshold1Dac] & 0x1FF) << 7;
    dacValues[6] |= (u32) (mMpx3DacCache[chipIdx][threshold0Dac] & 0x1FC) >> 2;

    dacValues[7] |= (u32) (mMpx3DacCache[chipIdx][threshold0Dac] & 0x003) << 30;

#endif
    {
        std::ostringstream os;
        for (unsigned int iWord = 0; iWord < 8; iWord++)
        {
          os << "0x" << std::hex << std::setw(8) << std::setfill('0') << dacValues[iWord] << std::dec << " ";
        }
        FEMLOG(mFemId, logDEBUG) << "DACS: Chip: " << chipIdx << " " << os.str();
    }
    // Write DAC values into FEM (into DPM area accessed via RDMA)
    this->rdmaWrite(kExcaliburAsicDpmRdmaAddress, dacValues);

    // Set ASIC MUX register
    u32 muxSelectVal = ((u32) 1 << (7 - chipIdx));
    this->rdmaWrite(kExcaliburAsicMuxSelect, muxSelectVal);

    // Set OMR registers
    mpx3Omr theOmr = this->mpx3OMRBuild(chipIdx, setDacs);
    this->asicControlOmrSet(theOmr);

    // Trigger OMR command write
    this->asicControlCommandExecute(asicCommandWrite);

  }
}

/** mpx3CtprWrite - write the column test pulse enable registers to an ASIC
 *
 * This function uploads the current column test pulse enable settings to the FEM and
 * then loads them into the specified ASIC. The settings are derived from the
 * locally-cached values, which in turn are set up by the pixel configuration calls.
 *
 * @param aChipId chip ID  to write (1-8, 0=all)
 */
void ExcaliburFemClient::mpx3CtprWrite(unsigned int aChipId)
{

  // If chip ID = 0, loop over all chips and call this function recursively
  if (aChipId == 0)
  {
    for (unsigned int iChip = 1; iChip <= kNumAsicsPerFem; iChip++)
    {
      this->mpx3CtprWrite(iChip);
    }
  }
  else
  {
    // Internal chip index runs from 0 to 7
    unsigned int chipIdx = aChipId - 1;

    // Store CTPR values into u32 vector for upload to FEM
    std::vector<u32> ctprValues(kNumAsicDpmWords, 0);

    // Pack CTPR values into the words of the vector, starting with the rightmost column (255)
    // as the bits are loaded MSB first
    unsigned int wordIdx = 0;
    unsigned int bitIdx = 31;

    for (int iCol = (kNumColsPerAsic - 1); iCol >= 0; iCol--)
    {
      ctprValues[wordIdx] |= (mMpx3ColumnTestPulseEnable[chipIdx][iCol] & 1) << bitIdx;
      if (bitIdx == 0)
      {
        bitIdx = 31;
        wordIdx++;
      }
      else
      {
        bitIdx--;
      }
    }

    {
        std::ostringstream os;
        for (unsigned int iWord = 0; iWord < 8; iWord++)
        {
          os  << "0x" << std::hex << std::setw(8) << std::setfill('0') << ctprValues[iWord]
              << std::dec << " ";
        }
        FEMLOG(mFemId, logDEBUG) << "CTPR Chip: " << chipIdx << " " << os.str();
    }

    // Write DAC values into FEM (into DPM area accessed via RDMA)
    this->rdmaWrite(kExcaliburAsicDpmRdmaAddress, ctprValues);

    // Set ASIC MUX register
    this->asicControlMuxChipSelect(chipIdx);

    // Set OMR registers
    mpx3Omr theOmr = this->mpx3OMRBuild(chipIdx, setCtpr);
    this->asicControlOmrSet(theOmr);

    // Trigger OMR command write
    this->asicControlCommandExecute(asicCommandWrite);

  }
}

void ExcaliburFemClient::mpx3PixelConfigSet(unsigned int aChipId, int aConfigId, std::size_t aSize,
    unsigned short* apValues)
{

  // Map the API-level pixel config ID onto the internal ID
  mpx3PixelConfig configIdx = mpx3PixelConfigIdGet(aConfigId);

  if (configIdx == unknownPixelConfig)
  {
    std::ostringstream msg;
    msg << "Illegal pixel configuration ID specified: " << aConfigId;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalConfigId, msg.str());
  }

  // Check chip ID is legal (noting that id = 0 implies all chips)
  if ((aChipId < 0) || (aChipId > kNumAsicsPerFem))
  {
    std::ostringstream msg;
    msg << "Illegal chip ID specified: " << aChipId;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalChipId, msg.str());
  }

  // Check that the size of the array matches the number of pixels for the chip
  if (aSize != kNumPixelsPerAsic)
  {
    std::ostringstream msg;
    msg << "Illegal pixel configuration length specified: " << aSize;
    throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalConfigSize, msg.str());
  }

  // If chip ID = 0, set the given config array of all chips to the specified value. Otherwise set
  // the values for a particular chip and pixel config (NB chip indexing offset from zero in API)
  if (aChipId == 0)
  {
    for (unsigned int iChip = 0; iChip < kNumAsicsPerFem; iChip++)
    {
      for (unsigned int iPixel = 0; iPixel < kNumPixelsPerAsic; iPixel++)
      {
        mMpx3PixelConfigCache[iChip][configIdx][iPixel] = apValues[iPixel];
      }
    }
  }
  else
  {
    for (unsigned int iPixel = 0; iPixel < kNumPixelsPerAsic; iPixel++)
    {
      mMpx3PixelConfigCache[aChipId - 1][configIdx][iPixel] = apValues[iPixel];
    }
  }

}

void ExcaliburFemClient::mpx3PixelConfigWrite(unsigned int aChipId)
{

//#define SHOW_CONFIG_WRITE_TIME
#ifdef SHOW_CONFIG_WRITE_TIME
  struct timespec startTime, endTime, writeTime;

  clock_gettime(CLOCK_REALTIME, &startTime);
#endif

  // If chip ID = 0, loop over all chips and call this function recursively
  if (aChipId == 0)
  {

    for (unsigned int iChip = 1; iChip <= kNumAsicsPerFem; iChip++)
    {
      this->mpx3PixelConfigWrite(iChip);
    }
  }
  else
  {
    // Internal chip index runs from 0 to 7
    unsigned int chipIdx = aChipId - 1;

    // Zero test pulse enable param and column test pulse cache for this chip, so they are not
    // left enabled when all test pulse bits are cleared

    mMpx3OmrParams[chipIdx].testPulseEnable = 0;
    for (unsigned int iCol = 0; iCol < kNumColsPerAsic; iCol++)
    {
      mMpx3ColumnTestPulseEnable[chipIdx][iCol] = 0;
    }

    // Per-pixel counter values to be loaded with bits from cache arrays
    unsigned short pixelConfigCounter0[kNumRowsPerAsic][kNumColsPerAsic];
    unsigned short pixelConfigCounter1[kNumRowsPerAsic][kNumColsPerAsic];

    // Extract pixel configuration from cache and build 12-bit counter 0 and 1 values for each pixel,
    // ordered in the pixel configuration bitstream load order as described in the MPX3 manual. For now
    // these are 'sparse' values stored in unsigned shorts, which we will then need to pack into a bitstream

    unsigned int iPixel = 0;
    for (unsigned int iRow = 0; iRow < kNumRowsPerAsic; iRow++)
    {
      for (unsigned int iCol = 0; iCol < kNumColsPerAsic; iCol++)
      {
        // Calculate index into cache arrays, API order is in EPICS ADR order, with
        // pixel (0,0) at top left, column varying fastest
        unsigned int pixelCacheIdx = ((kNumRowsPerAsic - (iRow + 1)) * kNumColsPerAsic) + iCol;

        // Extract bit fields from cache arrays
#ifdef MPX3_0
        unsigned short gainMode = mMpx3PixelConfigCache[chipIdx][pixelGainModeConfig][pixelCacheIdx] & 1;
        unsigned short testBit = mMpx3PixelConfigCache[chipIdx][pixelTestModeConfig][pixelCacheIdx] & 1;
        unsigned short maskBit = mMpx3PixelConfigCache[chipIdx][pixelMaskConfig][pixelCacheIdx] & 1;
        unsigned short configThA0 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdAConfig][pixelCacheIdx] >> 0) & 1;
        unsigned short configThA1 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdAConfig][pixelCacheIdx] >> 1) & 1;
        unsigned short configThA2 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdAConfig][pixelCacheIdx] >> 2) & 1;
        unsigned short configThA3 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdAConfig][pixelCacheIdx] >> 3) & 1;
        unsigned short configThA4 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdAConfig][pixelCacheIdx] >> 4) & 1;
        unsigned short configThB0 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdBConfig][pixelCacheIdx] >> 0) & 1;
        unsigned short configThB1 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdBConfig][pixelCacheIdx] >> 1) & 1;
        unsigned short configThB2 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdBConfig][pixelCacheIdx] >> 2) & 1;
        unsigned short configThB3 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdBConfig][pixelCacheIdx] >> 3) & 1;
        unsigned short configThB4 = (mMpx3PixelConfigCache[chipIdx][pixelThresholdBConfig][pixelCacheIdx] >> 4) & 1;

        // Build pixel configuration counter values from bit fields
        pixelConfigCounter0[iRow][iCol] =
        (gainMode << 8) | (configThA4 << 7) | (configThA2 << 6) | (configThA1 << 5) | (configThB4 << 4);
        pixelConfigCounter1[iRow][iCol] =
        (configThB1 << 10) | (maskBit << 9) | (configThB2 << 8) | (configThA3 << 7) | (configThB0 << 6) |
        (configThA0 << 5) | (configThB3 << 4) | (testBit << 3);
#else
        unsigned short testBit = mMpx3PixelConfigCache[chipIdx][pixelTestModeConfig][pixelCacheIdx]
            & 1;
        unsigned short maskBit = mMpx3PixelConfigCache[chipIdx][pixelMaskConfig][pixelCacheIdx] & 1;
        unsigned short configDiscL0 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscLConfig][pixelCacheIdx] >> 0) & 1;
        unsigned short configDiscL1 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscLConfig][pixelCacheIdx] >> 1) & 1;
        unsigned short configDiscL2 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscLConfig][pixelCacheIdx] >> 2) & 1;
        unsigned short configDiscL3 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscLConfig][pixelCacheIdx] >> 3) & 1;
        unsigned short configDiscL4 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscLConfig][pixelCacheIdx] >> 4) & 1;
        unsigned short configDiscH0 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscHConfig][pixelCacheIdx] >> 0) & 1;
        unsigned short configDiscH1 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscHConfig][pixelCacheIdx] >> 1) & 1;
        unsigned short configDiscH2 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscHConfig][pixelCacheIdx] >> 2) & 1;
        unsigned short configDiscH3 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscHConfig][pixelCacheIdx] >> 3) & 1;
        unsigned short configDiscH4 =
            (mMpx3PixelConfigCache[chipIdx][pixelDiscHConfig][pixelCacheIdx] >> 4) & 1;

        // Build pixel configuration counter values from bit fields
        pixelConfigCounter0[iRow][iCol] = 0;
        pixelConfigCounter1[iRow][iCol] = (testBit << 11) | (configDiscH4 << 10)
            | (configDiscH3 << 9) | (configDiscH2 << 8) | (configDiscH1 << 7) | (configDiscH0 << 6)
            | (configDiscL4 << 5) | (configDiscL3 << 4) | (configDiscL2 << 3) | (configDiscL1 << 2)
            | (configDiscL0 << 1) | (maskBit << 0);
        iPixel++;
#endif
//#define PIXEL_COUNTER_PACKING_DEBUG
#ifdef PIXEL_COUNTER_PACKING_DEBUG
        if ((iRow == 0) && (iCol == 0))
        {

          FEMLOG(mFemId, logDEBUG) << "Chip=" << aChipId << " Row=" << iRow << " Col=" << iCol
          << " ThreshAConfig=" << mMpx3PixelConfigCache[chipIdx][pixelThresholdAConfig][pixelCacheIdx]
          << " ConfigTHA4=" << configThA4
          << " Counter0=0x" << std::hex << pixelConfigCounter0[iRow][iCol] << std::dec
          << " ThreshBConfig=" << mMpx3PixelConfigCache[chipIdx][pixelThresholdBConfig][pixelCacheIdx]
          << " ConfigTHB4=" << configThB4
          << " Counter1=0x" << std::hex << pixelConfigCounter1[iRow][iCol] << std::dec;
        }
#endif
        // If any columns have test pulses enabled, enable the test pulse flag in the OMR parameters and set the
        // appropriate bits in the column test pulse cache
        if (testBit == 1)
        {
          mMpx3ColumnTestPulseEnable[chipIdx][iCol] = 1;
          mMpx3OmrParams[chipIdx].testPulseEnable = 1;
        }

        // DEBUG - put recognizable values into first few pixels for counter 0 and 1
//#define PIXEL_COUNTER_DEBUG
#ifdef PIXEL_COUNTER_DEBUG
        if ((iRow == 0) && (iCol == 255))
        {
          pixelConfigCounter0[iRow][iCol] = 0xABC;
          pixelConfigCounter1[iRow][iCol] = 0x123;
        }
        if ((iRow == 0) && (iCol == 254))
        {
          pixelConfigCounter0[iRow][iCol] = 0xDEF;
          pixelConfigCounter1[iRow][iCol] = 0x456;
        }
#endif
      }
    }

    // Pack the configuration counter values into a contiguous array ready to be uploaded to the FEM. These are packed
    // with MSB first for each pixel counter, bitwise over all pixels in each row of the chip. The bitstream is
    // shifted into the chip from the top-left corner, so the bottom-right pixel (0,255) is the head of the bistream.
    // This means it is necessary to 'flip' the column order of the columns into the bitstream.

    u32 pixelConfigCounter0Buffer[kPixelConfigBufferSizeWords] =
      { 0 };
    u32 pixelConfigCounter1Buffer[kPixelConfigBufferSizeWords] =
      { 0 };

    unsigned int bufferWordIdx = 0;  // Index of position in bitstream word buffer
    unsigned int bufferBitIdx = 31; // Bit position in bitstream word buffer

    // Loop over all rows
    for (unsigned int iRow = 0; iRow < kNumRowsPerAsic; iRow++)
    {
      // Loop over all counter bits, MSB first
      for (int iBit = (kPixelConfigBitsPerPixel - 1); iBit >= 0; iBit--)
      {
        // Loop over all columns, right-hand column (255) first
        for (int iCol = (kNumColsPerAsic - 1); iCol >= 0; iCol--)
        {

          pixelConfigCounter0Buffer[bufferWordIdx] |= ((u32) ((pixelConfigCounter0[iRow][iCol]
              >> iBit) & 0x1)) << bufferBitIdx;
          pixelConfigCounter1Buffer[bufferWordIdx] |= ((u32) ((pixelConfigCounter1[iRow][iCol]
              >> iBit) & 0x1)) << bufferBitIdx;

          // If we've reached bit 0 in the buffer word, restart at bit 31 in the next word, otherwise
          // decrement the buffer bit position index
          if (bufferBitIdx == 0)
          {
            bufferBitIdx = 31;
            bufferWordIdx++;
          }
          else
          {
            bufferBitIdx--;
          }

        } // iCol
      } // iBit
    } // iRow

//#define PIXEL_BUFFER_DEBUG
#ifdef PIXEL_BUFFER_DEBUG
    for (unsigned int iBuffer = 0; iBuffer < kPixelConfigBufferSizeWords; iBuffer++)
    {
      pixelConfigCounter0Buffer[iBuffer] = 0x0; // 0xFFFFFFFF; //(0 << 24) | iBuffer;
      pixelConfigCounter1Buffer[iBuffer] = 0xFFFFFFFF;//(1 << 24) | iBuffer;
    }

#endif

    // Load the CTPR registers with the appropriate test pulse bits
    this->mpx3CtprWrite(aChipId);

#ifndef MPX3_0
    // Set up rowBlock to 0x7 for pixel config load workaround on 3RX
    unsigned int savedOmrRowBlock = mMpx3OmrParams[chipIdx].rowBlock;

    mMpx3OmrParams[chipIdx].rowBlock = 0x7;
#endif

    // Upload pixel configuration to FEM memory

#ifdef MPX3_0
    // Write counter 0 configuration into the FEM memory
    this->memoryWrite(kPixelConfigBaseAddr, (u32*)&pixelConfigCounter0Buffer, kPixelConfigBufferSizeWords);
#endif

    // Write counter 1 configuration into the FEM memory
    this->memoryWrite(kPixelConfigBaseAddr + kPixelConfigBufferSizeBytes,
                      (u32*) &pixelConfigCounter1Buffer, kPixelConfigBufferSizeWords);

#ifdef SHOW_CONFIG_WRITE_TIME
    clock_gettime(CLOCK_REALTIME, &writeTime);
#endif

#ifdef MPX3_0
    // Set up the PPC1 DMA engine for upload mode for two configurations
    this->acquireConfig(ACQ_MODE_UPLOAD, kPixelConfigBufferSizeBytes, 2, kPixelConfigBaseAddr, 1);
#else
    // Set up the PPC1 DMA engine for upload mode for counter 1 only, and split the load into two halves
    // to comply with the pixel config load workaround on the 3RX chip
    this->acquireConfig(ACQ_MODE_UPLOAD, kPixelConfigBufferSizeBytes / 2, 2,
                        (kPixelConfigBaseAddr + kPixelConfigBufferSizeBytes), 1);
#endif

    // Start the DMA engine
    this->acquireStart();

    // Set ASIC MUX register
    this->asicControlMuxChipSelect(chipIdx);

#ifdef MPX3_0
    // Setup OMR value C0 load in the FEM
    mpx3Omr theOmr = this->mpx3OMRBuild(chipIdx, loadPixelMatrixC0);
    this->asicControlOmrSet(theOmr);

    // Execute the config load command
    this->asicControlCommandExecute(asicPixelConfigLoad);

    u32 ctrlState = this->rdmaRead(kExcaliburAsicCtrlState1);
    FEMLOG(mFemId, logDEBUG) << "ctrlState1=0x" << std::hex << ctrlState << std::dec;
#endif

    // Setup OMR value C1 load in the FEM
    mpx3Omr theOmr = this->mpx3OMRBuild(chipIdx, loadPixelMatrixC1);
    this->asicControlOmrSet(theOmr);

    // Execute the config load command
    this->asicControlCommandExecute(asicPixelConfigLoad);

    u32 ctrlState = this->rdmaRead(kExcaliburAsicCtrlState1);

#ifndef MPX3_0
    // Execute the config load command
    this->asicControlCommandExecute(asicPixelConfigLoad);

    ctrlState = this->rdmaRead(kExcaliburAsicCtrlState1);

#endif

    // Poll state of acquisition to test for completion of upload
    FemAcquireStatus acqStatus = this->acquireStatus();

    int retries = 0;
    while ((retries < 100) && (acqStatus.state != acquireIdle))
    {
      usleep(10000);
      acqStatus = this->acquireStatus();
      retries++;
    }

    if (acqStatus.state != acquireIdle)
    {
      std::ostringstream msg;
      msg << "Timeout on pixel configuration write to chip" << aChipId << " acqState="
          << acqStatus.state;
      throw FemClientException((FemClientErrorCode) excaliburFemClientOmrTransactionTimeout,
                               msg.str());
    }

#ifndef MPX3_0
    // Restore saved rowBlock for pixel config load workaround on 3RX
    mMpx3OmrParams[chipIdx].rowBlock = savedOmrRowBlock;
#endif

  }
#ifdef SHOW_CONFIG_WRITE_TIME
  clock_gettime(CLOCK_REALTIME, &endTime);

  double startSecs = startTime.tv_sec + ((double)startTime.tv_nsec / 1.0E9);
  double endSecs = endTime.tv_sec + ((double)endTime.tv_nsec / 1.0E9);
  double writeSecs = writeTime.tv_sec + ((double)writeTime.tv_nsec / 1.0E9);

  double elapsedSecs = endSecs - startSecs;
  double elapsedWrite = writeSecs - startSecs;

  FEMLOG(mFemId, logDEBUG) << "Config write time          " << elapsedWrite << " secs";
  FEMLOG(mFemId, logDEBUG) << "pixelConfigWrite call took " << elapsedSecs << " secs";
#endif
}

unsigned int ExcaliburFemClient::mpx3eFuseIdRead(unsigned int aChipId)
{

  unsigned int chipIdx = aChipId - 1;

  this->asicControlReset();

  // Set ASIC MUX register
  this->asicControlMuxChipSelect(chipIdx);

  // Set OMR registers
  mpx3Omr theOmr = this->mpx3OMRBuild(chipIdx, readEFuseId);
  this->asicControlOmrSet(theOmr);

  // Trigger an OMR transaction
  this->asicControlCommandExecute(asicCommandRead);

  // Wait for the OMR transaction to complete
  u32 ctrlState = this->rdmaRead(kExcaliburAsicCtrlState1);

  int retries = 0;
  while ((retries < 10) && (ctrlState != 0x80000000))
  {
    usleep(10000);
    ctrlState = this->rdmaRead(kExcaliburAsicCtrlState1);
    retries++;
  }

  // If the transaction didn't complete throw an exception
  if ((ctrlState & 0xF0000000) != 0x80000000)
  {
    std::ostringstream msg;
    msg << "Timeout on OMR read transaction to chip " << aChipId << " state=0x" << std::hex
        << ctrlState << std::dec;
    throw FemClientException((FemClientErrorCode) excaliburFemClientOmrTransactionTimeout,
                             msg.str());
  }

  u32 eFuseId = this->rdmaRead(kExcaliburAsicDpmRdmaAddress + 5);

  return eFuseId;
}

void ExcaliburFemClient::mpx3ColourModeSet(int aColourMode)
{

  // Set value for all chips
  for (unsigned int iChipIdx = 0; iChipIdx < kNumAsicsPerFem; iChipIdx++)
  {
    mMpx3OmrParams[iChipIdx].colourMode = (mpx3ColourMode) aColourMode;
  }
}

void ExcaliburFemClient::mpx3CounterDepthSet(int aCounterDepth)
{

  // Set value for all chips
  for (unsigned int iChipIdx = 0; iChipIdx < kNumAsicsPerFem; iChipIdx++)
  {
    mMpx3OmrParams[iChipIdx].counterDepth = (mpx3CounterDepth) aCounterDepth;
  }
}

void ExcaliburFemClient::mpx3CounterSelectSet(int aCounterSelect)
{

  mMpx3CounterSelect = (mpx3CounterSelect) aCounterSelect;

}

void ExcaliburFemClient::mpx3DisableSet(unsigned int aChipId, unsigned int aDisable)
{
  // If chip ID = 0, loop over all chips and call this function recursively
  if (aChipId == 0)
  {

    for (unsigned int iChip = 1; iChip <= kNumAsicsPerFem; iChip++)
    {
      this->mpx3DisableSet(iChip, aDisable);
    }
  }
  else
  {
    // Internal chip index runs from 0 to 7
    unsigned int chipIdx = aChipId - 1;

    // Set the enable flag for the chip - this is inverted in sense from the disable in the API
    mMpx3Enable[chipIdx] = (aDisable == 0) ? true : false;

  }
}

/** mpx3TestPulseEnableSet - enable/disable test pulses for a chip
 *
 * This method is a workaround to allow non-persistent client applications to user test pulses.
 * In normal circumstances, the TP enable/disable decision is made on the basis of the currently
 * loaded pixel configuration, which manages the individual TP enable fields of the OMRs of the
 * active chips, and allows a decision about running test pulses to be made at acquisition start.
 * With a non-persistent client (e.g. femApiTest), the configuration may be loaded into a device
 * by a separate invocation, so the this allows the enable to be forced to match the current
 * configuration.
 *
 * @param aChipId - chip to set enable on (0=all)
 * @param aEnable - enable flag (1=enabled, 0=disabled)
 */
void ExcaliburFemClient::mpx3TestPulseEnableSet(unsigned int aChipId, unsigned int aEnable)
{
  // If chip ID = 0, loop over all chips and call this function recursively
  if (aChipId == 0)
  {

    for (unsigned int iChip = 1; iChip <= kNumAsicsPerFem; iChip++)
    {
      this->mpx3TestPulseEnableSet(iChip, aEnable);
    }
  }
  else
  {
    // Internal chip index runs from 0 to 7
    unsigned int chipIdx = aChipId - 1;

    mMpx3OmrParams[chipIdx].testPulseEnable = aEnable;
  }

}

/// --- Private methods ---

/** mpx3DacIdGet - map API-level DAC IDs onto internal values
 *
 * This method maps the API-level MPX3 DAC IDs onto the the internal
 * index used to address and store DAC values. It will return a value
 * of unknownDacId for undefined API IDs.
 *
 * @param aId - API-level DAC ID to look up
 * @return excaliburMpx3Dac index for internal addressing of DAC values
 */
mpx3Dac ExcaliburFemClient::mpx3DacIdGet(int aId)
{
  // Set default resolved ID to unknown DAC
  mpx3Dac resolvedId = unknownDacId;

  // Static STL map to store mapping from API DAC IDs to internal.
  // If map is empty (i.e. at first call to this function, initialise
  // the values.
  static std::map<int, mpx3Dac> dacMap;
  if (dacMap.empty())
  {
    dacMap[FEM_OP_MPXIII_THRESHOLD0DAC] = threshold0Dac;
    dacMap[FEM_OP_MPXIII_THRESHOLD1DAC] = threshold1Dac;
    dacMap[FEM_OP_MPXIII_THRESHOLD2DAC] = threshold2Dac;
    dacMap[FEM_OP_MPXIII_THRESHOLD3DAC] = threshold3Dac;
    dacMap[FEM_OP_MPXIII_THRESHOLD4DAC] = threshold4Dac;
    dacMap[FEM_OP_MPXIII_THRESHOLD5DAC] = threshold5Dac;
    dacMap[FEM_OP_MPXIII_THRESHOLD6DAC] = threshold6Dac;
    dacMap[FEM_OP_MPXIII_THRESHOLD7DAC] = threshold7Dac;
    dacMap[FEM_OP_MPXIII_PREAMPDAC] = preampDac;
    dacMap[FEM_OP_MPXIII_IKRUMDAC] = ikrumDac;
    dacMap[FEM_OP_MPXIII_SHAPERDAC] = shaperDac;
    dacMap[FEM_OP_MPXIII_DISCDAC] = discDac;
    dacMap[FEM_OP_MPXIII_DISCLSDAC] = discLsDac;
    dacMap[FEM_OP_MPXIII_SHAPERTESTDAC] = shaperTestDac;
    dacMap[FEM_OP_MPXIII_DISCLDAC] = discLDac;
    dacMap[FEM_OP_MPXIII_DELAYDAC] = delayDac;
    dacMap[FEM_OP_MPXIII_TPBUFFERINDAC] = tpBufferInDac;
    dacMap[FEM_OP_MPXIII_TPBUFFEROUTDAC] = tpBufferOutDac;
    dacMap[FEM_OP_MPXIII_RPZDAC] = rpzDac;
    dacMap[FEM_OP_MPXIII_GNDDAC] = gndDac;
    dacMap[FEM_OP_MPXIII_TPREFDAC] = tpRefDac;
    dacMap[FEM_OP_MPXIII_FBKDAC] = fbkDac;
    dacMap[FEM_OP_MPXIII_CASDAC] = casDac;
    dacMap[FEM_OP_MPXIII_TPREFADAC] = tpRefADac;
    dacMap[FEM_OP_MPXIII_TPREFBDAC] = tpRefBDac;
    dacMap[FEM_OP_MPXIII_TESTDAC] = testDac;
    dacMap[FEM_OP_MPXIII_DISCHDAC] = discHDac;
  }

  // Check if the DAC ID is present in the map. If so, resolve
  // to the internal value.
  if (dacMap.count(aId))
  {
    resolvedId = dacMap[aId];
  }

  return resolvedId;
}

mpx3PixelConfig ExcaliburFemClient::mpx3PixelConfigIdGet(int aConfigId)
{
  // Set default resolved ID to unknown config
  mpx3PixelConfig resolvedId = unknownPixelConfig;

  // Static STL map to store amping from API config IDs to internal.
  // If map is empty (i.e. at first call to this function, initialise
  // the values
  static std::map<int, mpx3PixelConfig> pixelConfigMap;
  if (pixelConfigMap.empty())
  {
#ifdef MPX3_0
    pixelConfigMap[FEM_OP_MPXIII_PIXELMASK] = pixelMaskConfig;
    pixelConfigMap[FEM_OP_MPXIII_PIXELTHRESHOLDA] = pixelThresholdAConfig;
    pixelConfigMap[FEM_OP_MPXIII_PIXELTHRESHOLDB] = pixelThresholdBConfig;
    pixelConfigMap[FEM_OP_MPXIII_PIXELGAINMODE] = pixelGainModeConfig;
    pixelConfigMap[FEM_OP_MPXIII_PIXELTEST] = pixelTestModeConfig;
#else
    pixelConfigMap[FEM_OP_MPXIII_PIXELMASK] = pixelMaskConfig;
    pixelConfigMap[FEM_OP_MPXIII_PIXELDISCL] = pixelDiscLConfig;
    pixelConfigMap[FEM_OP_MPXIII_PIXELDISCH] = pixelDiscHConfig;
    pixelConfigMap[FEM_OP_MPXIII_PIXELTEST] = pixelTestModeConfig;
#endif
  }

  // Check if the config ID is present in the map. If so, resolve to
  // the internal value
  if (pixelConfigMap.count(aConfigId))
  {
    resolvedId = pixelConfigMap[aConfigId];
  }

  return resolvedId;
}

mpx3Omr ExcaliburFemClient::mpx3OMRBuild(unsigned int aChipIdx, mpx3OMRMode aMode)
{

  mpx3Omr theOMR;

  theOMR.raw = (((u64) aMode & 0x7) << 0)
      | (((u64) mMpx3OmrParams[aChipIdx].readWriteMode & 0x1) << 3)
      | (((u64) mMpx3OmrParams[aChipIdx].polarity & 0x1) << 4)
      | (((u64) mMpx3OmrParams[aChipIdx].readoutWidth & 0x3) << 5)
      | (((u64) mMpx3OmrParams[aChipIdx].discCsmSpm & 0x1) << 7)
      | (((u64) mMpx3GlobalTestPulseEnable & 0x1) << 8)
      | (((u64) mMpx3OmrParams[aChipIdx].counterDepth & 0x3) << 9)
      | (((u64) mMpx3OmrParams[aChipIdx].columnBlock & 0x7) << 11)
      | (((u64) mMpx3OmrParams[aChipIdx].columnBlockSelect & 0x1) << 14)
      | (((u64) mMpx3OmrParams[aChipIdx].rowBlock & 0x7) << 15)
      | (((u64) mMpx3OmrParams[aChipIdx].rowBlockSelect & 0x1) << 18)
      | (((u64) mMpx3OmrParams[aChipIdx].equalizationMode & 0x1) << 19)
      | (((u64) mMpx3OmrParams[aChipIdx].colourMode & 0x1) << 20)
      | (((u64) mMpx3OmrParams[aChipIdx].csmSpmMode & 0x1) << 21)
      | (((u64) mMpx3OmrParams[aChipIdx].infoHeaderEnable & 0x1) << 22)
      | (((u64) mMpx3OmrParams[aChipIdx].fuseSel & 0x1F) << 23)
      | (((u64) mMpx3OmrParams[aChipIdx].fusePulseWidth & 0x7F) << 28)
      | (((u64) mMpx3OmrParams[aChipIdx].gainMode & 0x3) << 35)
      | (((u64) mMpx3OmrParams[aChipIdx].dacSense & 0x1F) << 37)
      | (((u64) mMpx3OmrParams[aChipIdx].dacExternal & 0x1F) << 42)
      | (((u64) mMpx3OmrParams[aChipIdx].externalBandGapSelect & 0x1) << 47);

  return theOMR;
}

unsigned int ExcaliburFemClient::mpx3CounterBitDepth(mpx3CounterDepth aCounterDepth)
{
  unsigned int counterBitDepth = 0;

  switch (aCounterDepth)
  {
    case counterDepth1:
      counterBitDepth = 1;
      break;

    case counterDepth6:
      counterBitDepth = 6;
      break;

    case counterDepth12:
      counterBitDepth = 12;
      break;

    case counterDepth24:
      counterBitDepth = 12; // 24bit counter = 2x12 readout
      break;

    default:
      break;
  }

  return counterBitDepth;

}

unsigned int ExcaliburFemClient::mpx3ReadoutBitWidth(mpx3ReadoutWidth aReadoutWidth)
{
  unsigned int readoutBitWidth = 0;

  switch (aReadoutWidth)
  {
    case readoutWidth1:
      readoutBitWidth = 1;
      break;
    case readoutWidth2:
      readoutBitWidth = 2;
      break;

    case readoutWidth4:
      readoutBitWidth = 4;
      break;

    case readoutWidth8:
      readoutBitWidth = 8;
      break;

    default:
      break;
  }

  return readoutBitWidth;

}

// Methods added to support MPX3 RX ASICs

/** mpx3ReadWriteModeSet - sets the read/write mode field of all MPX3 ASICs
 * @param aReadWriteMode - integer value for sequential or continuous (0 or 1 respectively)
 * @return None
 */
void ExcaliburFemClient::mpx3ReadWriteModeSet(unsigned int aReadWriteMode)
{

  // Set value in OMR parameter block for all chips
  for (unsigned int iChipIdx = 0; iChipIdx < kNumAsicsPerFem; iChipIdx++)
  {
    mMpx3OmrParams[iChipIdx].readWriteMode = (mpx3ReadWriteMode) aReadWriteMode;
  }

}

/** mpx3DiscCsmSpmSet - sets the MPX3 discriminator output mode
 * @param aDiscCsmSpm - integer value for DiscL or DiscH (0 or 1 respectively)
 * @return None
 */
void ExcaliburFemClient::mpx3DiscCsmSpmSet(unsigned int aDiscCsmSpm)
{

  // Set value in OMR parameter block for all chips
  for (unsigned int iChipIdx = 0; iChipIdx < kNumAsicsPerFem; iChipIdx++)
  {
    mMpx3OmrParams[iChipIdx].discCsmSpm = (mpx3DiscCsmSpm) aDiscCsmSpm;
  }

}

/** mpx3EqualizationModeSet - sets the MPX3 equalization threshold mode
 * @param aEqualizationMode - integer value for off or on (0 or 1 respectively)
 * @return None
 */
void ExcaliburFemClient::mpx3EqualizationModeSet(unsigned int aEqualizationMode)
{

  // Set value in OMR parameter block for all chips
  for (unsigned int iChipIdx = 0; iChipIdx < kNumAsicsPerFem; iChipIdx++)
  {
    mMpx3OmrParams[iChipIdx].equalizationMode = (mpx3EqualizationMode) aEqualizationMode;
  }

}

/** mpx3CsmSpmModeSet - sets the MPX3 CSM/SPM mode
 * @param acsmSpmMode - integer value for SPM or CSM (0 or 1 respectively)
 * @return None
 */
void ExcaliburFemClient::mpx3CsmSpmModeSet(unsigned int aCsmSpmMode)
{

  // Set value in OMR parameter block for all chips
  for (unsigned int iChipIdx = 0; iChipIdx < kNumAsicsPerFem; iChipIdx++)
  {
    mMpx3OmrParams[iChipIdx].csmSpmMode = (mpx3CsmSpmMode) aCsmSpmMode;
  }

}

/** mpx3GainModeSet - sets the MPX3 gain mode
 * @param aEqualizationMode - integer value for gain mode (0-3, inverse meaning)
 * @return None
 */
void ExcaliburFemClient::mpx3GainModeSet(unsigned int aGainMode)
{

  // Set value in OMR parameter block for all chips
  for (unsigned int iChipIdx = 0; iChipIdx < kNumAsicsPerFem; iChipIdx++)
  {
    mMpx3OmrParams[iChipIdx].gainMode = (mpx3GainMode) aGainMode;
  }

}
