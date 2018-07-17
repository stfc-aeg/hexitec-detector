/*
 * ExcaliburPowerCardDevices.h
 *
 *  Created on: Jul 4, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Groups
 */

#ifndef EXCALIBURPOWERCARDDEVICES_H_
#define EXCALIBURPOWERCARDDEVICES_H_

#include "dataTypes.h"

const unsigned int kPwrCardPCF8574Address = 0x223;
const u8 kPwrCardPCF8574MonitorBitMask = 0xCF;
const unsigned int kPwrCardPCF8574BiasEnableBit = 4;
const unsigned int kPwrCardPCF8574LowVoltageEnableBit = 5;

const unsigned int kPwrCardAD5301Address = 0x20c;

const unsigned int kPwrCardBiasFullScale = 120;
const unsigned int kPwrCardBiasMaxDacCode = 255;

const unsigned int kPwrCardAD7998Address[] =
  { 0x222, 0x220, 0x221 };

typedef struct powerCardAD7998Map_t
{
  powerCardAD7998Map_t() :
      device(0),
      channel(0),
      scale(0.0),
      offset(0.0)
  {
  }
  powerCardAD7998Map_t(int aDevice, int aChannel, float aScale, float aOffset) :
      device(aDevice),
      channel(aChannel),
      scale(aScale),
      offset(aOffset)
  {
  }
  int device;
  int channel;
  float scale;
  float offset;
} powerCardAD7998Map;

const float kAD7998RawToVolts = 5.0 / 4096;
const float kAD7998RawToHumidity = 0.0394;
const float kAD7998HumidtyOffset = 30.9;
const float kAD7998RawToTemp = 0.01219;
const float kAD7998RawToFlow = 1.0;
const float kAD7998RawToBiasVolts = 0.06103;
#endif /* EXCALIBURPOWERCARDDEVICES_H_ */
