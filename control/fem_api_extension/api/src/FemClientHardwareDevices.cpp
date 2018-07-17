/*
 * femClientHardwareDevices.cpp - FemClient support methods for FEM hardware devices
 *
 *  Created on: Mar 7, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#include "FemClient.h"
#include "FemException.h"
#include <iostream>
#include <sstream>

/** tempSensorRead - reads an on-board temperature sensor from the FEM
 *
 * This function reads one of the on-board temperature sensors on the FEM,
 * which are accessible via the LM82 device on the internal I2C bus. The
 * temperature is returned as a double-precision value in Celsius.
 *
 * @param aSensor which sensor to read (0=board temperature, 1=FPGA temperature)
 * @return temperature in Celsius
 */
double FemClient::tempSensorRead(FemTemperatureSensor aSensor)
{

  const int deviceAddress = 0x18; // TODO put this in define somewhere

  double value = -100.0;
  u8 lm82CommandAddr = 0;

  // Determine LM82 command value to write to select sensor
  switch (aSensor)
  {
    case femBoardTemp:
      lm82CommandAddr = 0;
      break;

    case femFpgaTemp:
      lm82CommandAddr = 1;
      break;

    default:
    {
      std::ostringstream msg;
      msg << "Illegal temperature sensor specified (" << aSensor << ")";
      throw FemClientException(femClientIllegalSensor, msg.str());
    }
      break;
  }

  // Send command to LM82 to select device
  std::vector<u8> cmd(1, lm82CommandAddr);
  this->i2cWrite(deviceAddress, cmd);

  // Receive response, decode and return
  std::vector<u8> response = this->i2cRead(deviceAddress, 1);
  value = (double) response[0];

  return value;

}

