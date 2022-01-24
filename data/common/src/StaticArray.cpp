#include "StaticArrary.h"

namespace Hexitec {

  StaticArray::StaticArray()
  {
    static const std::size_t packet_size[]	= {4800, 3200, 1600, 5120, 5120, 0};  // UNRECOGNISED DECODER
  }

  StaticArray::~StaticArray()
  {
    ;
  }
}