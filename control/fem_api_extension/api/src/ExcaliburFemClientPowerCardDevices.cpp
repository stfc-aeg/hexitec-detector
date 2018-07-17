/*
 * ExcaliburFemClientPowerCardDevices.cpp - Power card control functions for ExcaliburFemClient class
 *
 *  Created on: Jul 4, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "ExcaliburFemClient.h"
#include "ExcaliburPowerCardDevices.h"
#include "FemLogger.h"

void ExcaliburFemClient::powerCardBiasEnableWrite(unsigned int aEnable)
{
  this->powerCardPCF8574BitWrite(kPwrCardPCF8574BiasEnableBit, aEnable);
}

void ExcaliburFemClient::powerCardLowVoltageEnableWrite(unsigned int aEnable)
{
  this->powerCardPCF8574BitWrite(kPwrCardPCF8574LowVoltageEnableBit, aEnable);
}

unsigned int ExcaliburFemClient::powerCardBiasEnableRead(void)
{
  return this->powerCardPCF8574BitRead(kPwrCardPCF8574BiasEnableBit);
}

unsigned int ExcaliburFemClient::powerCardLowVoltageEnableRead(void)
{
  return this->powerCardPCF8574BitRead(kPwrCardPCF8574LowVoltageEnableBit);
}

void ExcaliburFemClient::powerCardBiasLevelWrite(float aBiasLevel)
{

  FEMLOG(mFemId, logDEBUG) << "Setting bias level to " << aBiasLevel << "V";
  // Calculate 8-bit DAC value from requested bias level
  u8 dacValue = (int) ((aBiasLevel / kPwrCardBiasFullScale) * kPwrCardBiasMaxDacCode);

  this->powerCardAD5301Write(dacValue);

}

int ExcaliburFemClient::powerCardStatusRead(excaliburPowerCardStatus aStatus)
{

  int theStatus = 0;

  static std::map<excaliburPowerCardStatus, int> statusBitMap;
  if (statusBitMap.empty())
  {
    statusBitMap[coolantTempStatus] = 0;
    statusBitMap[humidityStatus] = 1;
    statusBitMap[coolantFlowStatus] = 2;
    statusBitMap[airTempStatus] = 3;
    statusBitMap[fanFaultStatus] = 6;
  }

  if (statusBitMap.count(aStatus))
  {
    theStatus = this->powerCardPCF8574BitRead(statusBitMap[aStatus]);
  }
  else
  {
    // TODO : throw something?
  }

  return theStatus;
}

float ExcaliburFemClient::powerCardMonitorRead(excaliburPowerCardMonitor aMonitor)
{
  float monitorResult = -1.0;

  static std::map<excaliburPowerCardMonitor, powerCardAD7998Map> monitorMap;
  if (monitorMap.empty())
  {
    monitorMap[p5vAVoltageMonitor] = powerCardAD7998Map(0, 0, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vBVoltageMonitor] = powerCardAD7998Map(0, 1, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vFem0CurrentMonitor] = powerCardAD7998Map(0, 2, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vFem1CurrentMonitor] = powerCardAD7998Map(0, 3, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vFem2CurrentMonitor] = powerCardAD7998Map(0, 4, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vFem3CurrentMonitor] = powerCardAD7998Map(0, 5, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vFem4CurrentMonitor] = powerCardAD7998Map(0, 6, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vFem5CurrentMonitor] = powerCardAD7998Map(0, 7, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p48vVoltageMonitor] = powerCardAD7998Map(1, 0, kAD7998RawToVolts * 10, 0.0);
    monitorMap[p48vCurrentMonitor] = powerCardAD7998Map(1, 1, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vSupVoltageMonitor] = powerCardAD7998Map(1, 2, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p5vSupCurrentMonitor] = powerCardAD7998Map(1, 3, kAD7998RawToVolts * 2, 0.0);
    monitorMap[humidityMonitor] = powerCardAD7998Map(1, 4, kAD7998RawToHumidity,
                                                     kAD7998HumidtyOffset);
    monitorMap[airTempMonitor] = powerCardAD7998Map(1, 5, kAD7998RawToTemp, 0.0);
    monitorMap[coolantTempMonitor] = powerCardAD7998Map(1, 6, kAD7998RawToTemp, 0.0);
    monitorMap[coolantFlowMonitor] = powerCardAD7998Map(1, 7, kAD7998RawToFlow, 0.0);
    monitorMap[p3v3CurrentMonitor] = powerCardAD7998Map(2, 0, kAD7998RawToVolts * 2, 0.0);
    monitorMap[p1v8ACurrentMonitor] = powerCardAD7998Map(2, 1, kAD7998RawToVolts * 10, 0.0);
    monitorMap[biasCurrentMonitor] = powerCardAD7998Map(2, 2, kAD7998RawToVolts / 1000, 0.0);
    monitorMap[p3v3VoltageMonitor] = powerCardAD7998Map(2, 3, kAD7998RawToVolts, 0.0);
    monitorMap[p1v8AVoltageMonitor] = powerCardAD7998Map(2, 4, kAD7998RawToVolts, 0.0);
    monitorMap[biasVoltageMontor] = powerCardAD7998Map(2, 5, kAD7998RawToBiasVolts, 0.0);
    monitorMap[p1v8BCurrentMonitor] = powerCardAD7998Map(2, 6, kAD7998RawToVolts * 10, 0.0);
    monitorMap[p1v8BVoltageMonitor] = powerCardAD7998Map(2, 7, kAD7998RawToVolts, 0.0);

  }

  if (monitorMap.count(aMonitor))
  {
    powerCardAD7998Map theMonitor = monitorMap[aMonitor];
    u16 rawADCVal = this->powerCardAD7998Read(theMonitor.device, theMonitor.channel);

    monitorResult = ((float) rawADCVal * theMonitor.scale) - theMonitor.offset;

  }

  return monitorResult;
}

// ---- Private functions ----

int ExcaliburFemClient::powerCardPCF8574BitRead(int aBit)
{

  // Read a single byte from the device
  std::vector<u8> response = this->i2cRead(kPwrCardPCF8574Address, 1);

  // Extract bit from response
  int theBit = (response[0] >> aBit) & 0x1;

  return theBit;
}

void ExcaliburFemClient::powerCardPCF8574BitWrite(int aBit, int aVal)
{

  FEMLOG(mFemId, logDEBUG) << "powerCardPCF8475BitWrite aBit=" << aBit << " aVal=" << aVal;

  // Read a single byte from the device
  std::vector<u8> response = this->i2cRead(kPwrCardPCF8574Address, 1);

  // Calculate new value by masking out non-monitor bits and ORing in the new
  // value
  std::vector<u8> cmd(1);

  u8 otherWriteBits = response[0] & ~(kPwrCardPCF8574MonitorBitMask | (1 << aBit));
  cmd[0] = otherWriteBits | (aVal << aBit) | kPwrCardPCF8574MonitorBitMask;

  FEMLOG(mFemId, logDEBUG) << "Old value: 0x" << std::hex << (int) response[0] << " other write bits: 0x"
      << (int) otherWriteBits << " new value: 0x" << (int) cmd[0] << std::dec;

  // Send command
  this->i2cWrite(kPwrCardPCF8574Address, cmd);
}

void ExcaliburFemClient::powerCardAD5301Write(u8 aDacValue)
{
  // Calculate 16-bit field for write transaction
  // Bits 0-3 : don't care, 4-11: DAC code, 12-13: PowerDown bits, 14-15: don't care
  u16 dacWord = aDacValue << 4;

  std::vector<u8> cmd(2);
  cmd[0] = (u8) (dacWord >> 8);
  cmd[1] = (u8) (dacWord & 0xFF);

  FEMLOG(mFemId, logDEBUG) << "AD5301write: dac=" << (int) aDacValue << " MSB=0x" << std::hex
          << (int) cmd[0] << "LSB=0x" << (int) cmd[1] << std::dec;

  // Send 2-byte command to device
  this->i2cWrite(kPwrCardAD5301Address, cmd);

}

/** powerCardAD7998Read - low level read access to AD7998 ADC devices
 *
 * Performs a low-level read command on the power card AD7998 ADC devices. The
 * required channel is selected, a read command is sent, and the converted value
 * read back from the device. This is decoded from the returned bytes and returned
 * as an ADC value
 *
 * @param aDevice which AD7994 device to read from
 * @param aChan which ADC channel to read
 * @return adcVal u16 ADC conversion value on that channel
 */
u16 ExcaliburFemClient::powerCardAD7998Read(unsigned int aDevice, unsigned int aChan)
{

  // Calculate address pointer to send to ADC
  u8 addrPtr = 0x80 | (aChan << 4);

  // Send channel select command to ADC
  std::vector<u8> cmd(2);
  cmd[0] = 0;
  cmd[1] = addrPtr;

  this->i2cWrite(kPwrCardAD7998Address[aDevice], cmd);

  // Wait 100ms
  struct timespec sleep;
  sleep.tv_sec = 0;
  sleep.tv_nsec = 100000000;
  nanosleep(&sleep, NULL);

  // Read two bytes back
  std::vector<u8> response = this->i2cRead(kPwrCardAD7998Address[aDevice], 2);

  // Decode ADC value to return
  u16 adcVal = ((((u16) response[0]) << 8) | response[1]) & 0xFFF;

  return adcVal;
}

