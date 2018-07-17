/*
 * ExcaliburFemClientPersonality.cpp
 *
 *  Created on: Oct 26, 2012
 *      Author: Tim Nicholls, STFC Application Engineering
 */

#include "ExcaliburFemClient.h"

personalityCommandStatus ExcaliburFemClient::personalityCommandStatusGet(void)
{

  FemTransaction response = this->personalityCommand(excaliburPersonalityCommandStatus, WIDTH_LONG,
                                                     NULL, 0);

  std::vector<u8> payload = response.getPayload();

  if (payload.size() != (sizeof(personalityCommandStatus) + sizeof(u32)))
  {
    std::ostringstream msg;
    msg << "Length mismatch when reading personality command status: expected "
        << sizeof(personalityCommandStatus) + sizeof(u32) << " got " << payload.size();
    throw FemClientException((FemClientErrorCode) excaliburFemClientPersonalityStatusError,
                             msg.str());
  }

  personalityCommandStatus* theStatus = (personalityCommandStatus*) &(payload[4]);

  return *theStatus;
}

