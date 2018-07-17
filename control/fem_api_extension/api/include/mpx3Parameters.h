/*
 * mpx3Parameters.h - parameters and settings for the EXCALIBUR MEDIPIX3 ASIC
 *
 *  Created on: Mar 21, 2012
 *      Author: Tim Nicholls, STFC Application Engineering Group
 */

#ifndef MPX3PARAMETERS_H_
#define MPX3PARAMETERS_H_

#include "dataTypes.h"

const unsigned int kNumAsicsPerFem = 8;

// Enumeration of DAC IDs, matching the definition in the MPX3 manual
typedef enum
{

  unknownDacId = -1,
  threshold0Dac = 0,
  threshold1Dac,
  threshold2Dac,
  threshold3Dac,
  threshold4Dac,
  threshold5Dac,
  threshold6Dac,
  threshold7Dac,
  preampDac,
  ikrumDac,
  shaperDac,
  discDac,
  discLsDac,
  shaperTestDac,
  discLDac,
  delayDac,
  tpBufferInDac,
  tpBufferOutDac,
  rpzDac,
  gndDac,
  tpRefDac,
  fbkDac,
  casDac,
  tpRefADac,
  tpRefBDac,
  testDac,
  discHDac,
  numExcaliburDacs

} mpx3Dac;

// Enumeration of colour mode settings
typedef enum
{

  unknownColourMode = -1, monochromeMode, colourMode, numColourModes

} mpx3ColourMode;

// Enumeration of counter depth settings
typedef enum
{

  unknownCounterDepth = -1,
  counterDepth1,
  counterDepth6,
  counterDepth12,
  counterDepth24,
  numCounterDepths

} mpx3CounterDepth;

// Enumeration of read/write mode settings
typedef enum
{

  unknownReadWriteMode = -1, sequentialReadWriteMode, continuousReadWriteMode

} mpx3ReadWriteMode;

// Enumeration of polarity mode settings
typedef enum
{

  unknownPolarity = -1, electronPolarity, holePolarity

} mpx3Polarity;

// Enumeration of readout width settings
typedef enum
{

  unknownReadoutWidth = -1, readoutWidth1, readoutWidth2, readoutWidth4, readoutWidth8

} mpx3ReadoutWidth;

// Enumeration of Disc_CSM_SPM (discriminator select) modes
typedef enum
{

  unknownDiscCsmSpm = -1, discCsmSpmDiscL, discCsmSpmDiscH

} mpx3DiscCsmSpm;

// Enumeration of equalization modes
typedef enum
{

  unknownEqualizationMode = -1, equalizationModeDisabled, equalizationModeEnabled

} mpx3EqualizationMode;

// Enumeration of CSM_SPM modes
typedef enum
{

  unknownCsmSpmMode = -1, csmSpmModeSpm, csmSpmModeCsm

} mpx3CsmSpmMode;

typedef enum
{

  unknownGainMode = -1, gainModeSuperHigh, gainModeHigh, gainModeLow, gainModeSuperLow

} mpx3GainMode;

// Enumeration of pixel config settings - this is for the internal
// storage of the settings before building the appropriate counter
// values for upload to the MPX3 device
typedef enum
{

#ifdef MPX3_0
  unknownPixelConfig = -1,
  pixelMaskConfig,
  pixelThresholdAConfig,
  pixelThresholdBConfig,
  pixelGainModeConfig,
  pixelTestModeConfig,
  numPixelConfigs
#else
  unknownPixelConfig = -1,
  pixelMaskConfig,
  pixelDiscLConfig,
  pixelDiscHConfig,
  pixelTestModeConfig,
  numPixelConfigs
#endif
} mpx3PixelConfig;

// Structure to store per-ASIC settings that are used to build the
// fields in the MPX3 operation mode register (OMR), which is
// used for each transaction with the device. These are ordered
// as defined in the MPX3 manual but only represent the interal
// storage - the appropriate 48-bit OMR is built explicitly
typedef struct
{
  mpx3ReadWriteMode readWriteMode;
  mpx3Polarity polarity;
  mpx3ReadoutWidth readoutWidth;
  mpx3DiscCsmSpm discCsmSpm;
  unsigned int testPulseEnable;
  mpx3CounterDepth counterDepth;
  unsigned int columnBlock;
  unsigned int columnBlockSelect;
  unsigned int rowBlock;
  unsigned int rowBlockSelect;
  mpx3EqualizationMode equalizationMode;
  mpx3ColourMode colourMode;
  mpx3CsmSpmMode csmSpmMode;
  unsigned int infoHeaderEnable;
  unsigned int fuseSel;
  unsigned int fusePulseWidth;
  mpx3GainMode gainMode;
  unsigned int dacSense;
  unsigned int dacExternal;
  unsigned int externalBandGapSelect;

} mpx3OMRParameters;

// Enumeration of OMR mode field settings
typedef enum
{
  setDacs = 1,
  setCtpr = 5,
  readDacs = 3,
  readEFuseId = 7,
  loadPixelMatrixC0 = 2,
  loadPixelMatrixC1 = 6,
  readPixelMatrixC0 = 0,
  readPixelMatrixC1 = 4

} mpx3OMRMode;

// Struct for storage of the OMR aligned on 32-bit word boundaries compatible
// with the RDMA structure of the FEM. This struct is used internally in the
// mpx3Omr union defined below
typedef struct
{
  u32 bottom;   // Bottom (least-significant) 32-bit word of the OMR
  u16 top;      // Top (most-siginificant) 16-bit word of the OMR
  u16 unused;   // Unused field (preserves size alignment with raw 64-bit value)

} mpx3OmrFields;

// Union to represent an OMR as both a full 48-bit value (in a 64bit word)
// overlaid with the fields that need to be extracted for RDMA transaction
// with the FEM.
typedef union
{
  u64 raw;
  mpx3OmrFields fields;

} mpx3Omr;

// Enumeration of MPX3 counter select for readout
typedef enum
{
  mpx3Counter0 = 0, mpx3Counter1 = 1

} mpx3CounterSelect;

#endif /* MPX3PARAMETERS_H_ */
