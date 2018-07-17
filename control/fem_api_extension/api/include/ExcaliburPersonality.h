/*
 * ExcaliburPersonality.h
 *
 *  Created on: Oct 26, 2012
 *      Author: tcn45
 */

#ifndef EXCALIBURPERSONALITY_H_
#define EXCALIBURPERSONALITY_H_

#include "mpx3Parameters.h"
#define PERS_ERROR_STRING_MAX_LENGTH 80

typedef struct
{
  u32 state;
  u32 numOps;
  u32 completedOps;
  u32 error;
  char errorString[PERS_ERROR_STRING_MAX_LENGTH];
} personalityCommandStatus;

typedef struct
{
  u32 bottom;
  u32 top;
} alignedOmr;

typedef struct
{
  u32 scanDac;
  u32 dacStart;
  u32 dacStop;
  u32 dacStep;
  u32 dacCache[kNumAsicsPerFem][numExcaliburDacs];
  u32 asicMask;
  alignedOmr omrDacSet;
  alignedOmr omrAcquire;
  u32 executeCommand;
  u32 acquisitionTimeMs;
} dacScanParams;

typedef enum
{
  personalityCommandIdle = 0, personalityCommandBusy = 1
} personalityCommandState;

const unsigned int kDacScanMaxRetries = 100;

#endif /* EXCALIBURPERSONALITY_H_ */
