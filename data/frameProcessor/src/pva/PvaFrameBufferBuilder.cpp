#include "PvaFrameBufferBuilder.h"
#include "HexitecDefinitions.h"

namespace FrameProcessor {

    PvaFrameBuffer* PvaFrameBufferBuilder::build_buffer(boost::shared_ptr<Frame> frame)
    {
        const FrameMetaData meta_data = frame->get_meta_data();
        uint64_t frame_num = meta_data.get_frame_number();
        std::size_t frame_size = frame->get_image_size();
        std::string frame_dataset = frame->get_meta_data().get_dataset_name();

        // Resolve frame start time from metadata parameters if they exist, otherwise use current
        // system time
        uint64_t frame_start_time_sec, frame_start_time_nsec;
        if (meta_data.has_parameter(Hexitec::FRAME_START_SEC_PARAM) &&
            meta_data.has_parameter(Hexitec::FRAME_START_NSEC_PARAM)) {

            frame_start_time_sec = meta_data.get_parameter<time_t>(Hexitec::FRAME_START_SEC_PARAM);
            frame_start_time_nsec = meta_data.get_parameter<time_t>(Hexitec::FRAME_START_NSEC_PARAM);
            LOG4CXX_DEBUG(logger_, "Frame " << frame_num << " dataset " << frame_dataset
                << " has start time " << frame_start_time_sec
                << "s and " << frame_start_time_nsec << "ns");
        } else {
            LOG4CXX_DEBUG(logger_, "Frame " << frame_num << " dataset " << frame_dataset
                << " does not have start time parameters");
            auto now = std::chrono::system_clock::now();
            frame_start_time_sec = std::chrono::duration_cast<std::chrono::seconds>(
                now.time_since_epoch()).count();
            frame_start_time_nsec = std::chrono::duration_cast<std::chrono::nanoseconds>(
                now.time_since_epoch()).count() % 1000000000;
        }

        // Determine the buffer size needed from the frame size and the flatbuffers overhead
        std::size_t buffer_size = frame_size + BUFFER_OVERHEAD;

        // Create a new PvaFrameBuffer for this frame
        auto buffer = new PvaFrameBuffer(frame_num, buffer_size, plugin_);

        // Create an allocator that writes into the buffer
        PvaFrameBufferAllocator allocator(buffer->frame_.get(), buffer_size);

        // Create a flatbuffer builder with this allocator
        flatbuffers::FlatBufferBuilder builder(buffer_size, &allocator);

        // Copy the data into an array and create the appropriate AnyT union based on the data type
        flatbuffers::Offset<AnyT> value_offset;
        switch (meta_data.get_data_type()) {
            case raw_8bit:
                // Handle uint8_t data
                {
                    std::size_t frame_length = frame_size / sizeof(uint8_t);
                    auto data_vector = builder.CreateVector(static_cast<uint8_t *>(
                        frame->get_data_ptr()), frame_length);
                    auto byte_array = CreateUByteArray(builder, data_vector);
                    value_offset = CreateAnyT(builder, AnyInner_UByteArray, byte_array.Union());
                }
                break;
            case raw_16bit:
                // Handle uint16_t data
                {
                    std::size_t frame_length = frame_size / sizeof(uint16_t);
                    auto data_vector = builder.CreateVector(static_cast<uint16_t *>(
                        frame->get_data_ptr()), frame_length);
                    auto uint_array = CreateUShortArray(builder, data_vector);
                    value_offset = CreateAnyT(builder, AnyInner_UShortArray, uint_array.Union());
                }
                break;
            case raw_32bit:
                // Handle uint32_t data
                {
                    std::size_t frame_length = frame_size / sizeof(uint32_t);
                    auto data_vector = builder.CreateVector(static_cast<uint32_t *>(
                        frame->get_data_ptr()), frame_length);
                    auto uint_array = CreateUIntArray(builder, data_vector);
                    value_offset = CreateAnyT(builder, AnyInner_UIntArray, uint_array.Union());
                }
                break;
            case raw_64bit:
                // Handle uint64_t data
                {
                    std::size_t frame_length = frame_size / sizeof(uint64_t);
                    auto data_vector = builder.CreateVector(static_cast<uint64_t *>(
                        frame->get_data_ptr()), frame_length);
                    auto ulong_array = CreateULongArray(builder, data_vector);
                    value_offset = CreateAnyT(builder, AnyInner_ULongArray, ulong_array.Union());
                }
                break;
            case raw_float:
                // Handle float data
                {
                    std::size_t frame_length = frame_size / sizeof(float);
                    auto data_vector = builder.CreateVector(static_cast<float *>(
                        frame->get_data_ptr()), frame_length);
                    auto float_array = CreateFloatArray(builder, data_vector);
                    value_offset = CreateAnyT(builder, AnyInner_FloatArray, float_array.Union());
                }
                break;
            default:
                LOG4CXX_ERROR(logger_, "Unsupported data type " << meta_data.get_data_type()
                    << " for frame " << frame_num << " dataset " << frame_dataset);
                return nullptr;
        }

        // Create an empty codec descriptor
        auto codec_offset = CreateCodecT(builder, builder.CreateString(""));

        // Create a vector of dimension tables by iterating over the dimensions in the frame metadata
        std::vector<flatbuffers::Offset<DimensionT>> dimensions;
        for (auto dim_size : meta_data.get_dimensions()) {

            auto axis_dim_offset = CreateDimensionT(builder, dim_size, 0, dim_size, 1, false);
            dimensions.push_back(axis_dim_offset);
        }
        auto dimension_offset = builder.CreateVector(dimensions);

        // Create a TimeT table using the frame start time
        auto timet_offset = CreateTimeT(builder, frame_start_time_sec, frame_start_time_nsec, 0);

        // Create a colour mode attribute indicating a monochrome image
        auto color_mode_name_offset = builder.CreateString("ColorMode");
        int color_mode_value = 0;
        std::vector<std::string> color_mode_tags = {"tag1", "tag2"};
        auto color_mode_tags_offset = builder.CreateVectorOfStrings(color_mode_tags);
        auto color_mode_descriptor_offset = builder.CreateString("Color mode");
        int color_mode_source_type = 0;
        auto color_mode_source_offset = builder.CreateString("Driver");
        auto color_mode_attribute_offset = CreateNTAttribute(
            builder,
            color_mode_name_offset,
            color_mode_value,
            color_mode_tags_offset,
            color_mode_descriptor_offset,
            0, // no alarm
            timet_offset, // reuse TimeT table created earlier
            color_mode_source_type,
            color_mode_source_offset
        );

        std::vector<flatbuffers::Offset<NTAttribute>> attributes;
        attributes.push_back(color_mode_attribute_offset);
        auto attribute_offset = builder.CreateVector(attributes);

        // Create a descriptor field
        auto descriptor_offset = builder.CreateString("Test NTNDArray");

        // Create an alarm table
        auto alarm_msg_offset = builder.CreateString("NO ALARM");
        auto alarm_offset = CreateAlarmT(
            builder, AlarmSeverity_NONE, AlarmStatus_NONE, alarm_msg_offset
        );

        // Create a display table
        auto display_desc_offset = builder.CreateString("Example array");
        auto display_units_offset = builder.CreateString("pixels");
        auto display_offset = CreateDisplayT(
            builder,
            0.0,                   // limit_low
            0.0,                   // limit_high
            display_desc_offset,   // description
            display_units_offset,  // units
            1,                     // precision
            DisplayForm_DEFAULT    // form
        );

        // Create the NTNDarray object - could also use the CreateNTNDArray helper function
        NTNDArrayBuilder ntndarray_builder(builder);
        ntndarray_builder.add_value(value_offset);
        ntndarray_builder.add_codec(codec_offset);
        ntndarray_builder.add_compressed_size(frame_size);
        ntndarray_builder.add_uncompressed_size(frame_size);
        ntndarray_builder.add_dimension(dimension_offset);
        ntndarray_builder.add_unique_id(frame_num);
        ntndarray_builder.add_data_time_stamp(timet_offset);
        ntndarray_builder.add_attribute(attribute_offset);
        ntndarray_builder.add_descriptor(descriptor_offset);
        ntndarray_builder.add_alarm(alarm_offset);
        ntndarray_builder.add_time_stamp(timet_offset);
        ntndarray_builder.add_display(display_offset);

        auto ntndarray_offset = ntndarray_builder.Finish();

        // Create a source name string
        auto source_name_offset = builder.CreateString("hexitec");

        // Create a pulse ID table with value and timestamp
        uint64_t pulse_id_value = frame_num; // use the frame number as the pulse ID value for simplicity
        double pulse_id_timestamp = static_cast<double>(frame_start_time_sec)
            + static_cast<double>(frame_start_time_nsec) / 1e9;
        auto pulse_id_offset = CreatePulseID(
            builder, pulse_id_value, pulse_id_timestamp
        );

        // Create the root PVData table
        PVDataBuilder pvdata_builder(builder);
        pvdata_builder.add_data_type(PVType_NTNDArray);
        pvdata_builder.add_data(ntndarray_offset.Union());
        pvdata_builder.add_source_name(source_name_offset);
        pvdata_builder.add_pulse_id(pulse_id_offset);

        auto pvdata_offset = pvdata_builder.Finish();

        // Finish the buffer
        FinishPVDataBuffer(builder, pvdata_offset);

        // Update the buffer object with the pointer and size of the serialized data
        buffer->pvdata_ = builder.GetBufferPointer();
        buffer->pvdata_size_ = builder.GetSize();

        return buffer;
  }

} // namespace FrameProcessor
