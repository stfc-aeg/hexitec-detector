#ifndef PVA_FRAME_BUFFER_BUILDER_H
#define PVA_FRAME_BUFFER_BUILDER_H

#include <boost/shared_ptr.hpp>
#include <log4cxx/logger.h>
#include "pva0_generated.h"
#include "Frame.h"

using namespace log4cxx;
using namespace log4cxx::helpers;

namespace FrameProcessor {

class HexitecKafkaPvaPlugin;

struct PvaFrameBuffer {

    PvaFrameBuffer(uint64_t frame_number, std::size_t frame_size, HexitecKafkaPvaPlugin* plugin)
        : frame_number_(frame_number),
          frame_size_(frame_size),
          frame_(new uint8_t[frame_size]),
          pvdata_(nullptr),
          pvdata_size_(0),
          plugin_(plugin) {}

    uint64_t frame_number_;
    std::size_t frame_size_;
    std::unique_ptr<uint8_t[]> frame_;
    uint8_t* pvdata_;
    std::size_t pvdata_size_;
    HexitecKafkaPvaPlugin* plugin_;
};

// Custom allocator that writes into a user-provided buffer
class PvaFrameBufferAllocator : public flatbuffers::Allocator {
public:
    PvaFrameBufferAllocator(uint8_t* buffer, size_t buffer_size)
        : buffer_(buffer), buffer_size_(buffer_size), offset_(0) { }

    virtual uint8_t* allocate(size_t size) override {
        if (offset_ + size > buffer_size_) return nullptr;
        uint8_t* ptr = buffer_ + offset_;
        offset_ += size;
        return ptr;
    }

    virtual void deallocate(uint8_t* /*p*/, size_t /*size*/) override {
        // No-op for fixed buffer
    }

private:
    uint8_t* buffer_;
    size_t buffer_size_;
    size_t offset_;

};

class PvaFrameBufferBuilder {
public:
    PvaFrameBufferBuilder(HexitecKafkaPvaPlugin* plugin) : plugin_(plugin) {
        logger_ = Logger::getLogger("FP.PvaFrameBufferBuilder");
    }
    PvaFrameBuffer* build_buffer(boost::shared_ptr<Frame> frame);

private:
    HexitecKafkaPvaPlugin* plugin_;
    LoggerPtr logger_;

    static constexpr std::size_t BUFFER_OVERHEAD = 1024; // Flatbuffers PVData buffer overhead
};


} // namespace FrameProcessor
#endif // PVA_FRAME_BUFFER_BUILDER_H
