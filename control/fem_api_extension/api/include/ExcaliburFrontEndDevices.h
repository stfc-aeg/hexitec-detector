/*
 * ExcaliburFrontEndDevices.h
 *
 *  Created on: Mar 8, 2012
 *      Author: tcn45
 */

#ifndef EXCALIBYRFRONTENDDEVICES_H_
#define EXCALIBYRFRONTENDDEVICES_H_

#include "dataTypes.h"

const unsigned int kSHT21Address = 0x340;
const u8 kSHT21TemperatureCmd = 0xf3;
const u8 kSHT21HumidityCmd = 0xf5;

const unsigned int kAD7994Address[] =
  { 0x321, 0x322 };
const unsigned int kAD7994ChipMap[] =
  { 1, 3, 2, 0 };

const unsigned int kPCF8574Address = 0x338;

const unsigned int kAD5626NumDevices = 2;
const unsigned int kAD5625Address[] =
  { 0x30C, 0x30F };
const unsigned int kAD5625ChipMap[] =
  { 3, 2, 1, 0 };
const unsigned int kAD5626CmdMode = 0x3;
const unsigned int kAD5626RefSetup = 0x7;
const unsigned int kAD5625CmdShift = 3;
const unsigned int kAD5625DacShift = 4;
const double kAD5625FullScale = 2.5;

#endif /* EXCALIBYRFRONTENDDEVICES_H_ */
