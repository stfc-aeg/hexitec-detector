/*
 * femApi.cpp
 *
 *  Created on: 2 Dec 2011
 *      Author: tcn
 */
#include "femApi.h"
#include "FemApiError.h"
#include "ExcaliburFemClient.h"
#include "FemLogger.h"
#include <map>
#include <sstream>
#include <cstring>

//#define FEM_API_TRACE
#ifdef FEM_API_TRACE
#include <stdio.h>
#include <time.h>
#include <pthread.h>
#endif

/* Initialise logging function pointer */
TLogFunc FemLogger::log_func_ = NULL;

// Forward declarations of internal functions
static int translateFemErrorCode(FemErrorCode error);

// Internal static variables, which cache the WP5 control handle and callback structures passed
// as arguments during the initialisation
static void* lCtlHandle = NULL;
static const CtlCallbacks* lCallbacks = NULL;

const unsigned int kClientTimeoutMsecs = 10000;

typedef struct
{
  ExcaliburFemClient* client;
  FemApiError error;
} FemHandle;

const char* femErrorMsg(void* handle)
{
  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  return (femHandle->error).get_string();
}

int femErrorCode(void* handle)
{
  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  return (femHandle->error).get_code();
}

int femInitialise(void* ctlHandle, const CtlCallbacks* callbacks, const CtlConfig* config,
    void** handle)
{

  int rc = FEM_RTN_OK;

  // Initialise FEM handle and client objects, which opens and manages the connection with the FEM
  FemHandle* femHandle = new FemHandle;
  femHandle->client = NULL;
  *handle = reinterpret_cast<void*>(femHandle);

  try
  {
    femHandle->client = new ExcaliburFemClient(ctlHandle, callbacks, config, kClientTimeoutMsecs);

  }
  catch (FemClientException& e)
  {
    femHandle->error.set() << "Failed to initialise FEM connection: " << e.what();
    rc = FEM_RTN_INITFAILED;
  }

  // Store the control API handle and callback structures
  lCtlHandle = ctlHandle;
  lCallbacks = callbacks;

  return rc;
}

void femSetLogFunction(logFunc log_func)
{
    FemLogger::SetLoggingFunction((TLogFunc)log_func);
}

int femGetId(void* handle)
{
  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  return (femHandle->client)->get_id();
}

void femClose(void* handle)
{
  //ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);
  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  if (femHandle->client != NULL)
  {
    delete femHandle->client;
  }

  delete femHandle;
}

int femSetInt(void* handle, int chipId, int id, std::size_t size, size_t offset, int* value)
{
  int rc = FEM_RTN_OK;

#ifdef FEM_API_TRACE
  {
    struct timespec tp;
    clock_gettime(CLOCK_REALTIME, &tp);
    printf("%09ld.%09ld femSetInt tid=0x%08x chip=%d id=%d size=%d value[0]=%d\n",
        (unsigned long)tp.tv_sec, (unsigned long)tp.tv_nsec, (unsigned int)pthread_self(),
        chipId, id, (int)size, value[0]);
  }
#endif

  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
  {
    femHandle->error.set() << "Illegal chipID (" << chipId << ") specified";
    rc = FEM_RTN_ILLEGALCHIP;
  }
  else
  {
    try
    {
      switch (id)
      {

        case FEM_OP_MPXIII_COLOURMODE:

          if (size == 1)
          {
            (femHandle->client)->mpx3ColourModeSet((int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_COUNTERDEPTH:

          if (size == 1)
          {
            (femHandle->client)->mpx3CounterDepthSet((int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_EXTERNALTRIGGER:

          if (size == 1)
          {
            (femHandle->client)->triggerModeSet((int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_OPERATIONMODE:

          if (size == 1)
          {
            (femHandle->client)->operationModeSet((int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_COUNTERSELECT:

          if (size == 1)
          {
            (femHandle->client)->mpx3CounterSelectSet((int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_NUMTESTPULSES:

          if (size == 1)
          {
            (femHandle->client)->numTestPulsesSet((int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_READWRITEMODE:

          if (size == 1)
          {
            (femHandle->client)->mpx3ReadWriteModeSet((unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_DISCCSMSPM:

          if (size == 1)
          {
            (femHandle->client)->mpx3DiscCsmSpmSet((unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_EQUALIZATIONMODE:

          if (size == 1)
          {
            (femHandle->client)->mpx3EqualizationModeSet((unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_CSMSPMMODE:

          if (size == 1)
          {
            (femHandle->client)->mpx3CsmSpmModeSet((unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_GAINMODE:

          if (size == 1)
          {
            (femHandle->client)->mpx3GainModeSet((unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_TRIGGERPOLARITY:

          if (size == 1)
          {
            (femHandle->client)->triggerPolaritySet((unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_LFSRBYPASS:

          if (size == 1)
          {
            (femHandle->client)->lfsrBypassEnableSet((unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_DACSENSE:

          if (size == 1)
          {
            (femHandle->client)->mpx3DacSenseSet((unsigned int) chipId, (int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_DACEXTERNAL:

          if (size == 1)
          {
            (femHandle->client)->mpx3DacExternalSet((unsigned int) chipId, (int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

          // Handle all DAC settings through the femSetDac helper function
        case FEM_OP_MPXIII_THRESHOLD0DAC:
        case FEM_OP_MPXIII_THRESHOLD1DAC:
        case FEM_OP_MPXIII_THRESHOLD2DAC:
        case FEM_OP_MPXIII_THRESHOLD3DAC:
        case FEM_OP_MPXIII_THRESHOLD4DAC:
        case FEM_OP_MPXIII_THRESHOLD5DAC:
        case FEM_OP_MPXIII_THRESHOLD6DAC:
        case FEM_OP_MPXIII_THRESHOLD7DAC:
        case FEM_OP_MPXIII_PREAMPDAC:
        case FEM_OP_MPXIII_IKRUMDAC:
        case FEM_OP_MPXIII_SHAPERDAC:
        case FEM_OP_MPXIII_DISCDAC:
        case FEM_OP_MPXIII_DISCLSDAC:
        case FEM_OP_MPXIII_SHAPERTESTDAC:
        case FEM_OP_MPXIII_DISCLDAC:
        case FEM_OP_MPXIII_DELAYDAC:
        case FEM_OP_MPXIII_TPBUFFERINDAC:
        case FEM_OP_MPXIII_TPBUFFEROUTDAC:
        case FEM_OP_MPXIII_RPZDAC:
        case FEM_OP_MPXIII_GNDDAC:
        case FEM_OP_MPXIII_TPREFDAC:
        case FEM_OP_MPXIII_FBKDAC:
        case FEM_OP_MPXIII_CASDAC:
        case FEM_OP_MPXIII_TPREFADAC:
        case FEM_OP_MPXIII_TPREFBDAC:
        case FEM_OP_MPXIII_TESTDAC:
        case FEM_OP_MPXIII_DISCHDAC:

          if (size == 1)
          {
            (femHandle->client)->mpx3DacSet(chipId, id, (unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_NUMFRAMESTOACQUIRE:

          (femHandle->client)->numFramesSet((unsigned int) *value);
          break;

        case FEM_OP_ACQUISITIONTIME:

          (femHandle->client)->acquisitionTimeSet((unsigned int) *value);
          break;

        case FEM_OP_ACQUISITIONPERIOD:

          (femHandle->client)->acquisitionPeriodSet((unsigned int) *value);
          break;

        case FEM_OP_VDD_ON_OFF:

          (femHandle->client)->frontEndEnableSet((unsigned int) *value);
          break;

        case FEM_OP_BIAS_ON_OFF:

          (femHandle->client)->powerCardBiasEnableWrite((unsigned int) *value);
          break;

        case FEM_OP_LV_ON_OFF:

          (femHandle->client)->powerCardLowVoltageEnableWrite((unsigned int) *value);
          break;

        case FEM_OP_MEDIPIX_CHIP_DISABLE:

          if (size == 1)
          {
            (femHandle->client)->mpx3DisableSet((unsigned int) chipId, (unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MPXIII_TESTPULSE_ENABLE:

          if (size == 1)
          {
            (femHandle->client)->mpx3TestPulseEnableSet((unsigned int) chipId,
                                                        (unsigned int) *value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_SCAN_DAC:

          (femHandle->client)->dacScanDacSet((unsigned int) *value);
          break;

        case FEM_OP_SCAN_START:

          (femHandle->client)->dacScanStartSet((unsigned int) *value);
          break;

        case FEM_OP_SCAN_STOP:

          (femHandle->client)->dacScanStopSet((unsigned int) *value);
          break;

        case FEM_OP_SCAN_STEP:

          (femHandle->client)->dacScanStepSet((unsigned int) *value);
          break;

        case FEM_OP_DATA_RECEIVER_ENABLE:

          (femHandle->client)->dataReceiverEnable((unsigned int) *value);
          break;

        case FEM_OP_SOURCE_DATA_PORT:
        case FEM_OP_DEST_DATA_PORT:
        {
          static std::map<int, excaliburDataPortParam> dataParamMap;
          if (dataParamMap.empty())
          {
            dataParamMap[FEM_OP_SOURCE_DATA_PORT] = excaliburDataPortSource;
            dataParamMap[FEM_OP_DEST_DATA_PORT] = excaliburDataPortDest;
          }
          if (dataParamMap.count(id))
          {
            (femHandle->client)->dataPortParamSet(dataParamMap[id], size, offset,
                                                  (const unsigned int*) value);
          }
          else
          {
            (femHandle->error).set() << "Internal error: param id " << id
                << "not in data port parameter map";
            rc = FEM_RTN_BADSIZE;
          }
        }
          break;

        case FEM_OP_DEST_DATA_PORT_OFFSET:

          (femHandle->client)->dataDestPortOffsetSet((unsigned int) *value);
          break;

        case FEM_OP_FARM_MODE_NUM_DESTS:

          (femHandle->client)->dataFarmModeNumDestinationsSet((unsigned int) *value);
          break;

        case FEM_OP_FARM_MODE_ENABLE:

          (femHandle->client)->dataFarmModeEnableSet((unsigned int) *value);
          break;

        default:
          femHandle->error.set() << "Illegal parameter ID (" << id << ") specified";
          rc = FEM_RTN_UNKNOWNOPID;
          break;
      }
      if (rc == FEM_RTN_BADSIZE)
      {
        femHandle->error.set() << "Bad value size (" << size << ") for parameter ID " << id
            << "specified";
      }
    }
    catch (FemClientException& e)
    {
      (femHandle->error).set() << e.what();
      rc = translateFemErrorCode(e.which());
    }
  }
  return rc;
}

int femSetShort(void* handle, int chipId, int id, std::size_t size, size_t offset, short* value)
{
  int rc = FEM_RTN_OK;

  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
  {
    femHandle->error.set() << "Illegal chipID (" << chipId << ") specified";
    rc = FEM_RTN_ILLEGALCHIP;
  }
  else
  {
    try
    {
      switch (id)
      {

        // Handle all pixel settings through single call
        case FEM_OP_MPXIII_PIXELMASK:
        case FEM_OP_MPXIII_PIXELDISCL:
        case FEM_OP_MPXIII_PIXELDISCH:
        case FEM_OP_MPXIII_PIXELTEST:

          if (size == (FEM_PIXELS_PER_CHIP_X * FEM_PIXELS_PER_CHIP_Y))
          {
            (femHandle->client)->mpx3PixelConfigSet((unsigned int) chipId, id, size,
                                                    (unsigned short*) value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        default:
          (femHandle->error).set() << "Illegal parameter id (" << id << ") specified";
          rc = FEM_RTN_UNKNOWNOPID;
          break;
      }
      if (rc == FEM_RTN_BADSIZE)
      {
        femHandle->error.set() << "Bad value size (" << size << ") for parameter ID " << id
            << "specified";
      }
    }
    catch (FemClientException& e)
    {
      (femHandle->error).set() << e.what();
      rc = translateFemErrorCode(e.which());
    }
  }
  return rc;
}

int femSetFloat(void* handle, int chipId, int id, std::size_t size, size_t offset, double* value)
{
  int rc = FEM_RTN_OK;

  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
  {
    femHandle->error.set() << "Illegal chipID (" << chipId << ") specified";
    rc = FEM_RTN_ILLEGALCHIP;
  }
  else
  {
    try
    {
      switch (id)
      {

        case FEM_OP_DAC_IN_TO_MEDIPIX:

          (femHandle->client)->frontEndDacInWrite(chipId, *value);
          break;

        case FEM_OP_BIAS_LEVEL:

          (femHandle->client)->powerCardBiasLevelWrite(*value);
          break;

        case FEM_OP_BURST_SUBMIT_PERIOD:

          (femHandle->client)->burstModeSubmitPeriodSet(*value);
          break;

        default:
          (femHandle->error).set() << "Illegal parameter id (" << id << ") specified";
          rc = FEM_RTN_UNKNOWNOPID;
          break;
      }
    }
    catch (FemClientException& e)
    {
      (femHandle->error).set() << e.what();
      rc = translateFemErrorCode(e.which());
    }
  }

  return rc;
}

int femGetInt(void* handle, int chipId, int id, size_t size,int* value)
{
  int rc = FEM_RTN_OK;

  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
  {
    femHandle->error.set() << "Illegal chipID (" << chipId << ") specified";
    rc = FEM_RTN_ILLEGALCHIP;
  }
  else
  {
    try
    {
      switch (id)
      {

        case FEM_OP_P1V5_AVDD_1_POK:
          *value = (femHandle->client)->frontEndSupplyStatusRead(frontEndAVDD1);
          break;

        case FEM_OP_P1V5_AVDD_2_POK:
          *value = (femHandle->client)->frontEndSupplyStatusRead(frontEndAVDD2);
          break;

        case FEM_OP_P1V5_AVDD_3_POK:
          *value = (femHandle->client)->frontEndSupplyStatusRead(frontEndAVDD3);
          break;

        case FEM_OP_P1V5_AVDD_4_POK:
          *value = (femHandle->client)->frontEndSupplyStatusRead(frontEndAVDD4);
          break;

        case FEM_OP_P1V5_VDD_1_POK:
          *value = (femHandle->client)->frontEndSupplyStatusRead(frontEndVDD);
          break;

        case FEM_OP_P2V5_DVDD_1_POK:
          *value = (femHandle->client)->frontEndSupplyStatusRead(frontEndDVDD);
          break;

        case FEM_OP_COOLANT_TEMP_STATUS:
          *value = (femHandle->client)->powerCardStatusRead(coolantTempStatus);
          break;

        case FEM_OP_HUMIDITY_STATUS:
          *value = (femHandle->client)->powerCardStatusRead(humidityStatus);
          break;

        case FEM_OP_COOLANT_FLOW_STATUS:
          *value = (femHandle->client)->powerCardStatusRead(coolantFlowStatus);
          break;

        case FEM_OP_AIR_TEMP_STATUS:
          *value = (femHandle->client)->powerCardStatusRead(airTempStatus);
          break;

        case FEM_OP_FAN_FAULT:
          *value = (femHandle->client)->powerCardStatusRead(fanFaultStatus);
          break;

        case FEM_OP_MPXIII_EFUSEID:
          *value = (femHandle->client)->mpx3eFuseIdRead(chipId);
          break;

        case FEM_OP_BIAS_ON_OFF:
          *value = (femHandle->client)->powerCardBiasEnableRead();
          break;

        case FEM_OP_LV_ON_OFF:
          *value = (femHandle->client)->powerCardLowVoltageEnableRead();
          break;

        case FEM_OP_FRAMES_ACQUIRED:
          *value = (femHandle->client)->frameCountGet();
          break;

        case FEM_OP_CONTROL_STATE:
          *value = (femHandle->client)->controlStateGet();
          break;

        case FEM_OP_DAC_SCAN_STATE:
          *value = (femHandle->client)->dacScanStateGet();
          break;

        case FEM_OP_DAC_SCAN_STEPS_COMPLETE:
          *value = (femHandle->client)->dacScanStepsCompleteGet();
          break;

        case FEM_OP_FIRMWARE_VERSION:
          if (size == 4)
          {
            (femHandle->client)->firmwareVersionGet(value);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        default:
          (femHandle->error).set() << "Illegal parameter ID (" << id << ") specified";
          rc = FEM_RTN_UNKNOWNOPID;
          break;

      }
    }
    catch (FemClientException& e)
    {
      (femHandle->error).set() << e.what();
      rc = translateFemErrorCode(e.which());
    }

  }

  return rc;
}

int femGetShort(void* handle, int chipId, int id, size_t size, short* value)
{
  int rc = FEM_RTN_OK;

  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  if ((chipId < 0) || (chipId >= (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
  {
    femHandle->error.set() << "Illegal chipID (" << chipId << ") specified";
    rc = FEM_RTN_ILLEGALCHIP;
  }
  else
  {
    try
    {
      switch (id)
      {

        default:
          (femHandle->error).set() << "Illegal parameter id (" << id << ") specified";
          rc = FEM_RTN_UNKNOWNOPID;
          break;

      }
    }
    catch (FemClientException& e)
    {
      (femHandle->error).set() << e.what();
      rc = translateFemErrorCode(e.which());
    }

  }

  return rc;
}

int femGetFloat(void* handle, int chipId, int id, size_t size, double* value)
{

  int rc = FEM_RTN_OK;

  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  if ((chipId < 0) || (chipId > (FEM_CHIPS_PER_BLOCK_X * FEM_BLOCKS_PER_STRIPE_X)))
  {
    femHandle->error.set() << "Illegal chipID (" << chipId << ") specified";
    rc = FEM_RTN_ILLEGALCHIP;
  }
  else
  {
    try
    {
      switch (id)
      {

        case FEM_OP_P5V_A_VMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p5vAVoltageMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P5V_B_VMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p5vBVoltageMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P5V_FEMO0_IMON:
        case FEM_OP_P5V_FEMO1_IMON:
        case FEM_OP_P5V_FEMO2_IMON:
        case FEM_OP_P5V_FEMO3_IMON:
        case FEM_OP_P5V_FEMO4_IMON:
        case FEM_OP_P5V_FEMO5_IMON:

          if (size == 1)
          {
            excaliburPowerCardMonitor theMon = (excaliburPowerCardMonitor) (p5vFem0CurrentMonitor
                + (id - FEM_OP_P5V_FEMO0_IMON));
            *value = (femHandle->client)->powerCardMonitorRead(theMon);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P48V_VMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p48vVoltageMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P48V_IMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p48vCurrentMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P5VSUP_VMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p5vSupVoltageMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P5VSUP_IMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p5vSupCurrentMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_HUMIDITY_MON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(humidityMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_AIR_TEMP_MON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(airTempMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_COOLANT_TEMP_MON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(coolantTempMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_COOLANT_FLOW_MON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(coolantFlowMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P3V3_IMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p3v3CurrentMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P1V8_IMON_A:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p1v8ACurrentMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_BIAS_IMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(biasCurrentMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P3V3_VMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p3v3VoltageMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P1V8_VMON_A:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p1v8AVoltageMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_BIAS_VMON:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(biasVoltageMontor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P1V8_IMON_B:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p1v8BCurrentMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_P1V8_VMON_B:

          if (size == 1)
          {
            *value = (femHandle->client)->powerCardMonitorRead(p1v8BVoltageMonitor);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_REMOTE_DIODE_TEMP:

          if (size == 1)
          {
            *value = (femHandle->client)->tempSensorRead(femFpgaTemp);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_LOCAL_TEMP:
          if (size == 1)
          {
            *value = (femHandle->client)->tempSensorRead(femBoardTemp);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MOLY_TEMPERATURE:
          if (size == 1)
          {
            *value = (femHandle->client)->frontEndTemperatureRead();
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_MOLY_HUMIDITY:
          if (size == 1)
          {
            *value = (femHandle->client)->frontEndHumidityRead();
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        case FEM_OP_DAC_OUT_FROM_MEDIPIX:
          if (size == 1)
          {
            *value = (femHandle->client)->frontEndDacOutRead(chipId);
          }
          else
          {
            rc = FEM_RTN_BADSIZE;
          }
          break;

        default:
          (femHandle->error).set() << "Illegal parameter id (" << id << ") specified";
          rc = FEM_RTN_UNKNOWNOPID;
          break;
      }
      if (rc == FEM_RTN_BADSIZE)
      {
        femHandle->error.set() << "Bad value size (" << size << ") for parameter ID " << id
            << "specified";
      }

    }
    catch (FemClientException& e)
    {
      (femHandle->error).set() << e.what();
      rc = translateFemErrorCode(e.which());
    }

  }
  return rc;
}

int femGetString(void* handle, int chipId, int id, size_t size, char** value)
{
  int rc = FEM_RTN_OK;

  return rc;
}

int femSetString(void* handle, int chipId, int id, size_t size, size_t offset, char** values)
{
  int rc = FEM_RTN_OK;

  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  try
  {
    switch (id)
    {
      case FEM_OP_SOURCE_DATA_ADDR:
      case FEM_OP_SOURCE_DATA_MAC:
      case FEM_OP_DEST_DATA_ADDR:
      case FEM_OP_DEST_DATA_MAC:

      {
        static std::map<int, excaliburDataAddrParam> dataParamMap;
        if (dataParamMap.empty())
        {
          dataParamMap[FEM_OP_SOURCE_DATA_ADDR] = excaliburDataAddrSourceIp;
          dataParamMap[FEM_OP_SOURCE_DATA_MAC] = excaliburDataAddrSourceMac;
          dataParamMap[FEM_OP_DEST_DATA_ADDR] = excaliburDataAddrDestIp;
          dataParamMap[FEM_OP_DEST_DATA_MAC] = excaliburDataAddrDestMac;
        }
        if (dataParamMap.count(id))
        {
          (femHandle->client)->dataAddrParamSet(dataParamMap[id], size, offset, (const char **) values);
        }
        else
        {
          (femHandle->error).set() << "Internal error: param id " << id
              << "not in data address parameter map";
          rc = FEM_RTN_BADSIZE;
        }
      }
        break;

      default:
        (femHandle->error).set() << "Illegal parameter id (" << id << ") specified";
        rc = FEM_RTN_UNKNOWNOPID;
        break;

    }
  }
  catch (FemClientException& e)
  {
    (femHandle->error).set() << e.what();
    rc = translateFemErrorCode(e.which());
  }

  return rc;
}

int femCmd(void* handle, int chipId, int id)
{
  int rc = FEM_RTN_OK;

#ifdef FEM_API_TRACE
  {
    struct timespec tp;
    clock_gettime(CLOCK_REALTIME, &tp);
    printf("%09ld.%09ld femCmd    tid=0x%08x chip=%d id=%d\n",
        (unsigned long)tp.tv_sec, (unsigned long)tp.tv_nsec, (unsigned int)pthread_self(),
        chipId, id);
  }
#endif

  FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

  try
  {
    switch (id)
    {

      case FEM_OP_STARTACQUISITION:
      case FEM_OP_STOPACQUISITION:
        (femHandle->client)->command(id);
        break;

      case FEM_OP_LOADDACCONFIG:
        (femHandle->client)->mpx3DacsWrite(chipId);
        break;

      case FEM_OP_LOADPIXELCONFIG:
        (femHandle->client)->mpx3PixelConfigWrite(chipId);
        break;

      case FEM_OP_FEINIT:
        (femHandle->client)->frontEndInitialise();
        break;

      case FEM_OP_FREEALLFRAMES:
        (femHandle->client)->freeAllFrames();
        break;

      case FEM_OP_REBOOT:
        (femHandle->client)->command(0);
        break;

      case FEM_OP_RESET_UDP_COUNTER:
        (femHandle->client)->command(id);
        break;

      default:
        (femHandle->error).set() << "Illegal command id (" << id << ") specified";
        rc = FEM_RTN_UNKNOWNOPID;
        break;
    }
  }
  catch (FemClientException& e)
  {
    (femHandle->error).set() << e.what();
    rc = translateFemErrorCode(e.which());
  }

  return rc;
}

// Internal functions
int translateFemErrorCode(FemErrorCode error)
{
  int rc = -1;

  switch (error)
  {
    case excaliburFemClientIllegalDacId:
      rc = FEM_RTN_ILLEGALCHIP;
      break;

    case excaliburFemClientIllegalChipId:
      rc = FEM_RTN_ILLEGALCHIP;
      break;

    case excaliburFemClientOmrTransactionTimeout:
      rc = FEM_RTN_ILLEGALCHIP;
      break;

    default:
      // Default translation is to just return error code
      rc = (int) error;
      break;
  }

  return rc;
}

