/*
 * ExcaliburFemClientFrontEndDevices.cpp - ExcaliburFemClient methods for
 * supporting devices on the EXCALIBUR detector front-end electronics
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

/** setFrontEndEnable - set the front-end regulator enable
 *
 * Sets the supply regulator enable bit in the front-end IO register
 * to the specified value. Note this function is for testing only as
 * the production front-end PCBs have this enable forced high to
 * preserve control at the power card only
 *
 * @param aVal enable value to set (0 or 1)
 */
void ExcaliburFemClient::frontEndEnableSet(unsigned int aVal)
{

  // Construct byte value to send to device. Since only bit 0 is RW,
  // we mask this out of requested value and force other bits to 1
  // to retain input function (which monitor supply regulator status).

  unsigned int writeVal = (aVal & 0x1) | (0xFE);

  // Write to the IO device
  this->frontEndPCF8574Write(writeVal);

}

/** frontEndTemperatureRead - reads the temperature of the EXCALIBUR front-end
 *
 * Read the temperature of the EXCALIBUR front-end by accessing the temperature
 * channel of the SHT21 device via the I2C bus.
 *
 * @return temperature double precision temperature in Celsius
 */
double ExcaliburFemClient::frontEndTemperatureRead(void)
{

  // Read raw value from the device
  u16 rawVal = this->frontEndSht21Read(kSHT21TemperatureCmd);

  // Apply the magic conversion formula from the SHT21 datasheet
  double temperature = -46.85 + (175.72 * ((double) rawVal / 65536.0));

  return temperature;
}

/** frontEndHumidityRead - reads the humidity of the EXCALIBUR front-end
 *
 * Read the humidity of the EXCALIBUR front-end by accessing the humidity
 * channel of the SHT21 device via the I2C bus.
 *
 * @return humidity double precision humidity in percent
 */
double ExcaliburFemClient::frontEndHumidityRead(void)
{
  // Read raw value from the device
  u16 rawVal = this->frontEndSht21Read(kSHT21HumidityCmd);

  // Apply the magic conversion formula from the SHT21 datasheet
  double humidity = -6.0 + (125.0 * ((double) rawVal / 65536.0));

  return humidity;
}

/** frontEndDacOutRead - read the ASIC DAC output value
 *
 * Reads the MPX3 DAC output value, as selected by the device's
 * sense DAC setting. This is read from the appropriate channel
 * of the front-end ADC and converted to volts.
 *
 * @param aChipID ID of MPX3 ASIC to read for (1-8)
 * @return dacOutVolts double precision DAC output in volts
 */
double ExcaliburFemClient::frontEndDacOutRead(unsigned int aChipId)
{

  // Chip index starts from 0
  unsigned int chipIdx = aChipId - 1;

  // Map chipId into ADC device channel
  unsigned int device = chipIdx / 4;
  unsigned int chan = kAD7994ChipMap[chipIdx % 4];

  // Acquire ADC value
  u16 rawAdcValue = this->frontEndAD7994Read(device, chan);

  // Convert ADC units to volts (2V reference) and return
  double dacOutVolts = 2.0 * ((double) rawAdcValue / 4096.0);

  return dacOutVolts;
}

/** frontEndSupplyStatusRead - read the status bit for the front-end supply regulators
 *
 * Read the status of the front-end power supply regulators. This is done by reading
 * the IO expander and extracting the appropriate bit.
 *
 * @param aSupply which front-end supply to be read
 * @return status indicates status of that supply regulator (1=on)
 */
int ExcaliburFemClient::frontEndSupplyStatusRead(excaliburFrontEndSupply aSupply)
{

  // Read IO values from PCF
  u8 pcfValue = this->frontEndPCF8574Read();

  // Extract appropriate bit from the value and return;
  int status = (pcfValue >> aSupply) & 0x1;

  return status;
}

/** frontEndDacInWrite - set the front-end input DAC value
 *
 * Sets the front-end input DAC to the requested value via the I2C bus. These
 * DAC values are connected to the external DAC inputs of the MPX3 ASICs.
 *
 * @param aChipId ID of MPX3 device to set external input DAC for (1-8)
 * @param aDacCode DAC value (code) to be set
 */
void ExcaliburFemClient::frontEndDacInWrite(unsigned int aChipId, unsigned int aDacCode)
{

  // Chip index starts from 0
  unsigned int chipIdx = aChipId - 1;

  // Map chipId onto DAC device and channel. Chips 4,3,2,1 on DAC0, 8,7,6,5 on DAC1
  unsigned int device = chipIdx / 4;
  unsigned int chan = kAD5625ChipMap[chipIdx % 4];

  // Write the DAC value
  this->frontEndAD5625Write(device, chan, aDacCode);

  FEMLOG(mFemId, logDEBUG) << "Setting FE DAC for chip " << aChipId << " (dev="
          << device << " chan=" << chan << ") value: " << aDacCode;

}

/** frontEndDacInWrite - set the front-end input DAC value
 *
 * Sets the front-end input DAC to the requested value via the I2C bus. These
 * DAC values are connected to the external DAC inputs of the MPX3 ASICs.
 *
 * @param aChipId ID of MPX3 device to set external input DAC for (1-8)
 * @param aDacVolts DAC value in volts to be set
 */
void ExcaliburFemClient::frontEndDacInWrite(unsigned int aChipId, double aDacVolts)
{

    FEMLOG(mFemId, logDEBUG) << "DAC volts: " << aDacVolts;

  unsigned int aDacCode = (unsigned int) ((aDacVolts / kAD5625FullScale) * 4096) & 0xFFF;

  // Write the DAC value
  this->frontEndDacInWrite(aChipId, aDacCode);

}

void ExcaliburFemClient::frontEndDacInitialise(void)
{

  for (unsigned int iChip = 0; iChip < kAD5626NumDevices; iChip++)
  {
    this->frontEndAD5625InternalReferenceEnable(iChip, true);
  }

}
/// --------- Private methods ---------

/** frontEndSht21Read - low level access to SHT21 device
 *
 * Performs low-level read commands to the SHT21 device via the I2C bus. The
 * appropriate conversion is triggered then data are read back and packed into
 * the return value.
 *
 * @param aCmdByte SHT21 command byte to be sent
 * @return rawVal raw u16 value encoded from response bytes
 */
u16 ExcaliburFemClient::frontEndSht21Read(u8 aCmdByte)
{

  // Send conversion command to device
  std::vector<u8> cmd(1, aCmdByte);
  this->i2cWrite(kSHT21Address, cmd);

  // Wait 100ms
  struct timespec sleep;
  sleep.tv_sec = 0;
  sleep.tv_nsec = 100000000;
  nanosleep(&sleep, NULL);

  // Read three bytes back
  std::vector<u8> response = this->i2cRead(kSHT21Address, 3);

  // Pack bytes into raw value to be returned
  u16 rawVal = (((u16) response[0]) << 8) | response[1];

  return rawVal;
}

/** frontEndAD7994Read - low level read access to AD7994 ADC devices
 *
 * Performs a low-level read command on the front-end AD7994 ADC devices. The
 * required channel is selected, a read command is sent, and the converted value
 * read back from the device. This is decoded from the returned bytes and returned
 * as an ADC value
 *
 * @param aDevice which AD7994 device to read from
 * @param aChan which ADC channel to read
 * @return adcVal u16 ADC conversion value on that channel
 */
u16 ExcaliburFemClient::frontEndAD7994Read(unsigned int aDevice, unsigned int aChan)
{

  // Calculate address pointer to send to ADC
  u8 addrPtr = 1 << (aChan + 4);

  // Send channel select command to AD
  std::vector<u8> cmd(2);
  cmd[0] = 0;
  cmd[1] = addrPtr;

  this->i2cWrite(kAD7994Address[aDevice], cmd);

  // Wait 100ms
  struct timespec sleep;
  sleep.tv_sec = 0;
  sleep.tv_nsec = 100000000;
  nanosleep(&sleep, NULL);

  // Read two bytes back
  std::vector<u8> response = this->i2cRead(kAD7994Address[aDevice], 2);

  // Decode ADC value to return
  u16 adcVal = ((((u16) response[0]) << 8) | response[1]) & 0xFFF;

//	FEMLOG(mFemId, logDEBUG) << "AD7994 read: dev=" << aDevice << " chan=" << aChan
//			  << " addr=0x" << std::hex << kAD7994Address[aDevice] << std::dec
//			  << " val=" << adcVal;

  return adcVal;
}

/** frontEndPCF8574Read - reads the front-end PCF8574 IO register
 *
 * Reads the front-end PCF85754 IO register and returns the vale as a single
 * byte, with the bits representing the state of each input.
 *
 * @return response single byte containing the IO register state
 */
u8 ExcaliburFemClient::frontEndPCF8574Read(void)
{
  // Read a single byte from the device
  std::vector<u8> response = this->i2cRead(kPCF8574Address, 1);

  // Return value
  return response[0];

}

/** frontEndPCF8574Write - writes the front-end PCF8574 IO register
 *
 * Writes the front-end PCF85754 IO register, setting the inputs corresponding
 * to the bits in the byte specified. Note that this device has no data-direction
 * register, so it is up to the user to write '1' to bit corresponding to pins
 * set up as inputs
 *
 * @param aVal input value to write to register
 */
void ExcaliburFemClient::frontEndPCF8574Write(unsigned int aVal)
{

  std::vector<u8> cmd(1);

  // Construct single byte to write to device
  cmd[0] = (u8) (aVal & 0xFF);

  // Send command
  this->i2cWrite(kPCF8574Address, cmd);

}

/** frontEndAD5625Write - write to the front-end AD5625 DAC
 *
 * Writes a specified value to a channel of one of the front-end AD5626 DAC devices. The 2-byte
 * DAC value (12 bits used) and the command word to select the channel are written to
 * device via the I2C bus
 *
 * @param aDevice front-end device to write to
 * @param aChan channel to write to
 * @param aVal DAC value to write
 */
void ExcaliburFemClient::frontEndAD5625Write(unsigned int aDevice, unsigned int aChan,
    unsigned int aVal)
{

  std::vector<u8> cmd(3); // 3 byte write transaction to DAC

  // Assemble command byte from command and DAC channel
  cmd[0] = (kAD5626CmdMode << kAD5625CmdShift) | (aChan & 0x7);

  // Assemble two bytes of DAC value shifted up
  u16 dacWord = aVal << kAD5625DacShift;
  cmd[1] = (dacWord & 0xFF00) >> 8;
  cmd[2] = (dacWord & 0x00FF);

//	FEMLOG(mFemId, logDEBUG) << "AD5625 write: cmd=0x" << std::hex << (int)cmd[0] << " MSB=0x"
//	          << (int)cmd[1]<< " LSB=0x" << (int)cmd[2] << std::dec;
  // Send transaction to DAC
  this->i2cWrite(kAD5625Address[aDevice], cmd);

}

void ExcaliburFemClient::frontEndAD5625InternalReferenceEnable(unsigned int aDevice, bool aEnable)
{
  std::vector<u8> cmd(3); // 3 byte write transaction to DAC

  // Assemble command byte for internal reference setup, and LSB of data bytes to enable
  cmd[0] = (kAD5626RefSetup << kAD5625CmdShift);
  cmd[1] = 0;
  cmd[2] = aEnable ? 1 : 0;

  // Send transaction to DAC
  this->i2cWrite(kAD5625Address[aDevice], cmd);
}

