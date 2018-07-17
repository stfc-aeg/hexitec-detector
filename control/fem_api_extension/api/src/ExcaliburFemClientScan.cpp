/*
 * ExcaliburFemClientScan.cpp
 *
 *  Created on: Oct 24, 2012
 *      Author:  Tim Nicholls, STFC Application Engineering Group
 */

#include "ExcaliburFemClient.h"
#include "FemLogger.h"

void ExcaliburFemClient::dacScanDacSet(unsigned int aDac)
{
  mDacScanDac = aDac;
}

void ExcaliburFemClient::dacScanStartSet(unsigned int aDacStart)
{
  mDacScanStart = aDacStart;
}

void ExcaliburFemClient::dacScanStopSet(unsigned int aDacStop)
{
  mDacScanStop = aDacStop;
}

void ExcaliburFemClient::dacScanStepSet(unsigned int aDacStep)
{
  mDacScanStep = aDacStep;
}

unsigned int ExcaliburFemClient::dacScanNumSteps(void)
{

  unsigned int interval = abs((int) mDacScanStart - (int) mDacScanStop);
  unsigned int numSteps = (interval / mDacScanStep) + 1;

  if ((interval == 0) || (numSteps < 1))
  {
    std::ostringstream msg;
    msg << "Bad DAC scan parameters specified: start=" << mDacScanStart << " stop=" << mDacScanStop
        << " step=" << mDacScanStep;
    throw FemClientException((FemClientErrorCode) excaliburFemClientBadDacScanParameters,
                             msg.str());
  }

  return numSteps;
}

void ExcaliburFemClient::dacScanExecute(void)
{
  dacScanParams scanParams;

  // Copy scan parameters into block from locally-cached parameter values
  scanParams.scanDac = mDacScanDac;
  scanParams.dacStart = mDacScanStart;
  scanParams.dacStop = mDacScanStop;
  scanParams.dacStep = mDacScanStep;

  // Build active ASIC mask, identify first active ASIC and copy cached DACs into
  // parameter block
  scanParams.asicMask = 0;
  int firstActiveAsic = -1;
  for (unsigned int iAsic = 0; iAsic < kNumAsicsPerFem; iAsic++)
  {

    for (unsigned int iDac = 0; iDac < numExcaliburDacs; iDac++)
    {
      scanParams.dacCache[iAsic][iDac] = mMpx3DacCache[iAsic][iDac];
    }

    scanParams.asicMask |= ((unsigned int) mMpx3Enable[iAsic] << (7 - iAsic));
    if ((firstActiveAsic == -1) && mMpx3Enable[iAsic])
    {
      firstActiveAsic = iAsic;
    }
  }

  // Force FEM to internal trigger mode for DAC scans
  unsigned int controlConfigRegister = internalTriggerMode;
  this->asicControlConfigRegisterSet(controlConfigRegister);

  // Build OMR values for DAC set and acquire commands and copy into parameter
  // block. Note that this currently hard codes DAQ scan to use counter 0 at all
  // times
  // Set up OMR mode and execute command based on which counter is selected
  mpx3OMRMode omrMode = (mpx3OMRMode) 0;
  unsigned int executeCmd = asicPixelMatrixRead;
  switch (mMpx3CounterSelect)
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
      msg << "Cannot set up DAC can parameters, illegal counter select specified: "
          << mMpx3CounterSelect;
      throw FemClientException((FemClientErrorCode) excaliburFemClientIllegalCounterSelect,
                               msg.str());
    }

      break;
  }

  mpx3Omr omrDacSet = this->mpx3OMRBuild(firstActiveAsic, setDacs);
  mpx3Omr omrAcquire = this->mpx3OMRBuild(firstActiveAsic, omrMode);
  scanParams.omrDacSet.bottom = omrDacSet.fields.bottom;
  scanParams.omrDacSet.top = omrDacSet.fields.top;
  scanParams.omrAcquire.bottom = omrAcquire.fields.bottom;
  scanParams.omrAcquire.top = omrAcquire.fields.top;
  scanParams.executeCommand = executeCmd;
  scanParams.acquisitionTimeMs = mAcquisitionTimeMs;

  FEMLOG(mFemId, logDEBUG) << "DAC     : " << scanParams.scanDac
          << " Start   : " << scanParams.dacStart
          << " Stop    : " << scanParams.dacStop
          << " Step    : " << scanParams.dacStep;
  FEMLOG(mFemId, logDEBUG) << "Mask    : 0x" << std::hex << scanParams.asicMask << std::dec;
  FEMLOG(mFemId, logDEBUG) << "DAC OMR : 0x" << std::hex << omrDacSet.raw << std::dec;
  FEMLOG(mFemId, logDEBUG) << "ACQ OMR : 0x" << std::hex << omrAcquire.raw << std::dec;
  FEMLOG(mFemId, logDEBUG) << "Exec    : 0x" << std::hex << scanParams.executeCommand;
  FEMLOG(mFemId, logDEBUG) << "Acq time: " << std::dec << scanParams.acquisitionTimeMs;

  this->personalityCommand(excaliburPersonalityCommandDacScan, WIDTH_LONG, (u8*) &scanParams,
                           sizeof(scanParams));

}

int ExcaliburFemClient::dacScanAbort(void)
{
  int scanStepsCompleted = 0;

  // Read the personality command status from the FEM
  personalityCommandStatus theStatus = personalityCommandStatusGet();

  if (theStatus.state == personalityCommandIdle)
  {
    FEMLOG(mFemId, logDEBUG) << "DAC scan has already completed";
    scanStepsCompleted = theStatus.completedOps;
  }
  else
  {
    FEMLOG(mFemId, logDEBUG) << "Sending scan abort command to FEM, current state = "
            << theStatus.state << " completed steps = " << theStatus.completedOps;

    // Send abort command to FEM personality module
    this->personalityCommand(excaliburPersonalityCommandAbort, WIDTH_LONG, 0, 0);

    // Wait at least the acquisition time (shutter time) plus 500us readout time before
    // checking the state to allow last frame to be read out
    usleep((mAcquisitionTimeMs * 1000) + 500);

    // Wait for the scan command to terminate cleanly then read back number of completed steps
    bool scanAbortPending = true;
    int numAbortLoops = 0;
    int maxAbortLoops = 10;

    while (scanAbortPending && (numAbortLoops < maxAbortLoops))
    {
      theStatus = personalityCommandStatusGet();
      FEMLOG(mFemId, logDEBUG) << "Abort of scan command: " << numAbortLoops << " attempts, state: "
          << theStatus.state << " completed steps: " << theStatus.completedOps;
      if (theStatus.state == personalityCommandIdle)
      {
        FEMLOG(mFemId, logDEBUG) << "Scan aborted OK after " << theStatus.completedOps << " steps";
        scanAbortPending = false;
        scanStepsCompleted = theStatus.completedOps;
      }
      else
      {
        numAbortLoops++;
        usleep(mAcquisitionTimeMs * 1000);
      }
    }
    if (scanAbortPending)
    {
      FEMLOG(mFemId, logERROR) << "FEM DAC scan failed to abort correctly ";
      scanStepsCompleted = theStatus.completedOps;
    }
  }

  return scanStepsCompleted;
}

int ExcaliburFemClient::dacScanStateGet(void)
{
  // Read the personality command status from the FEM
  personalityCommandStatus theStatus = personalityCommandStatusGet();

  return (int) (theStatus.state);

}

int ExcaliburFemClient::dacScanStepsCompleteGet(void)
{
  // Read the personality command status from the FEM
  personalityCommandStatus theStatus = personalityCommandStatusGet();

  return (int) (theStatus.completedOps);

}
