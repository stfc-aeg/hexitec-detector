/*
 * static_array.h
 *
 *  Created on: Jan 24, 2021
 *      Author: Christian Angelsen, STFC Application Engineering Group
 */

#ifndef INCLUDE_STATICARRAY_H_
#define INCLUDE_STATICARRAY_H_

#define ILLEGAL_FEM_IDX -1

namespace Hexitec {

  class StaticArray
  {
  public:

    StaticArray();
    ~StaticArray();

    inline const std::size_t tail_packet_size(int index)
    {
      return packet_size[index];
    }
  private:
    static const std::size_t packet_size[];  // UNRECOGNISED DECODER
  };

}

#endif /* INCLUDE_STATICARRAY_H_ */
