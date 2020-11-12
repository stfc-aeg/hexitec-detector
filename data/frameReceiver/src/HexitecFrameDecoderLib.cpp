/*
 * HexitecFrameDecoderLib.cpp
 *
 *  Created on: 11 Jul 2018
 *      Author: Christian Angelsen
 */

#include "HexitecFrameDecoder.h"
#include "ClassLoader.h"

namespace FrameReceiver
{
  /**
   * Registration of this decoder through the ClassLoader.  This macro
   * registers the class without needing to worry about name mangling
   */
  REGISTER(FrameDecoder, HexitecFrameDecoder, "HexitecFrameDecoder");

}
// namespace FrameReceiver

