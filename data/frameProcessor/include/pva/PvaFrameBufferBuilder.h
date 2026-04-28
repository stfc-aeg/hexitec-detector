/*
* PvaFrameBufferBuilder.h - header file for the PvaFrameBufferBuilder class for building PVData
* flatbuffers from HEXITEC frames
*
*  Created on: 20 Apr 2026
*      Author: Tim Nicholls, STFC Detector Systems Software Group
*/
#ifndef PVA_FRAME_BUFFER_BUILDER_H
#define PVA_FRAME_BUFFER_BUILDER_H

#include <boost/shared_ptr.hpp>
#include <log4cxx/logger.h>
#include "pva0_generated.h"
#include "Frame.h"

using namespace log4cxx;
using namespace log4cxx::helpers;

namespace FrameProcessor {

// Forward declaration of the plugin class needed for the frame buffer
class HexitecKafkaPvaPlugin;

/*
* PvaFrameBuffer - structure containing a PVData frame flatbuffer to be sent to Kafka.
*
* Contains the frame buffer and associated metadata needed for building the PVData flatbuffer and
* handling in the Kafka message callback.
*/
struct PvaFrameBuffer {

    /*
    * Constructor for the PvaFrameBuffer structure.
    *
    * \param[in] frame_number - The frame number for this buffer
    * \param[in] frame_size - The size of the frame buffer
    * \param[in] plugin - Pointer to the HexitecKafkaPvaPlugin instance
    */
    PvaFrameBuffer(uint64_t frame_number, std::size_t frame_size, HexitecKafkaPvaPlugin* plugin)
        : frame_number_(frame_number),
          frame_size_(frame_size),
          frame_(new uint8_t[frame_size]),
          pvdata_(nullptr),
          pvdata_size_(0),
          plugin_(plugin) {}

    uint64_t frame_number_; //!< The frame number for this buffer
    std::size_t frame_size_; //!< The size of the frame buffer
    std::unique_ptr<uint8_t[]> frame_; //!< The PVData flatbuffer-encoded buffer
    uint8_t* pvdata_; //!< Pointer to the PVData flatbuffer once finished
    std::size_t pvdata_size_; //!< Size of the PVData flatbuffer once finished
    HexitecKafkaPvaPlugin* plugin_; //!< Pointer to the HexitecKafkaPvaPlugin instance
};

// Custom flatbuffers allocator class that writes into a user-provided buffer (i.e. in PvaFrameBuffer)
class PvaFrameBufferAllocator : public flatbuffers::Allocator {
public:

    /*
    * Constructor for the PvaFrameBufferAllocator class.
    *
    * \param[in] buffer - Pointer to the buffer to use for allocations
    * \param[in] buffer_size - Size of the buffer
    */
    PvaFrameBufferAllocator(uint8_t* buffer, size_t buffer_size)
        : buffer_(buffer), buffer_size_(buffer_size), offset_(0) { }

    /*
    * Allocate memory from the buffer.
    *
    * This method adjusts the internal offset to keep track of used space and returns a pointer to
    * the already-allocated memory in the buffer. If the requested size exceeds the remaining space
    * in the buffer, it returns nullptr.
    *
    * \param[in] size - The size of the memory to allocate
    * \return Pointer to the allocated memory, or nullptr if insufficient space
    */
    virtual uint8_t* allocate(size_t size) override {
        if (offset_ + size > buffer_size_) return nullptr;
        uint8_t* ptr = buffer_ + offset_;
        offset_ += size;
        return ptr;
    }

    /*
    * Deallocate memory from the buffer.
    *
    * This method is a no-op for the fixed buffer allocator, as memory is managed elsewhere.
    *
    * \param[in] p - Pointer to the memory to deallocate
    * \param[in] size - Size of the memory to deallocate
    */
    virtual void deallocate(uint8_t* /*p*/, size_t /*size*/) override {
        // No-op for fixed buffer
    }

private:
    uint8_t* buffer_; //!< Pointer to the buffer to use for allocations */
    size_t buffer_size_; //!< Size of the buffer */
    size_t offset_; //!< Current offset in the buffer */

};

/*
* PvaFrameBufferBuilder - class for building PVData flatbuffers from HEXITEC frames.
*/
class PvaFrameBufferBuilder {
public:

    /*
    * Constructor for the PvaFrameBufferBuilder class.
    *
    * \param[in] plugin - Pointer to the HexitecKafkaPvaPlugin instance
    */
    PvaFrameBufferBuilder(HexitecKafkaPvaPlugin* plugin) : plugin_(plugin) {
        // Setup logging for the class
        logger_ = Logger::getLogger("FP.PvaFrameBufferBuilder");
    }

    /*
    * Build a PvaFrameBuffer from a HEXITEC frame.
    *
    * \param[in] frame - Shared pointer to the HEXITEC frame
    * \return Pointer to the constructed PvaFrameBuffer
    */
    PvaFrameBuffer* build_buffer(boost::shared_ptr<Frame> frame);

private:
    HexitecKafkaPvaPlugin* plugin_; //!< Pointer to the HexitecKafkaPvaPlugin instance
    LoggerPtr logger_; //!< Logger for the class

    static constexpr std::size_t BUFFER_OVERHEAD = 1024; // Flatbuffers PVData buffer overhead
};


} // namespace FrameProcessor
#endif // PVA_FRAME_BUFFER_BUILDER_H
