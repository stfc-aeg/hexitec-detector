/*
 * FemClientAcquisition.cpp
 *
 *  Created on: Mar 16, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "FemClient.h"
#include "FemException.h"
#include "FemClientAcquisition.h"

void FemClient::acquireConfig(u32 aAcqMode, u32 aBufferSize, u32 aBufferCount, u32 aNumAcq,
    u32 aBdCoalesce)
{

  FemAcquireConfiguration config =
    { aAcqMode, aBufferSize, aBufferCount, aNumAcq, aBdCoalesce };

  this->commandAcquire(CMD_ACQ_CONFIG, &config);
}

void FemClient::acquireStart(void)
{

  this->commandAcquire(CMD_ACQ_START, NULL);
}

void FemClient::acquireStop(void)
{
  this->commandAcquire(CMD_ACQ_STOP, NULL);
}

FemAcquireStatus FemClient::acquireStatus(void)
{
  std::vector<u8> acqResponse = this->commandAcquire(CMD_ACQ_STATUS, NULL);

  FemAcquireStatus acqStatus = *((FemAcquireStatus*) &(acqResponse[4]));

  return acqStatus;
}
