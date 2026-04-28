/*
 * HexitecKafkaPvaPlugin.cpp
 *
 *  Created on: 25 Mar 2019
 *      Author: Emilio Perez
 */
#include <cstring>
#include <cstdlib>
#include <algorithm>
#include <boost/algorithm/string.hpp>
#include <climits>
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"

#include "HexitecKafkaPvaPlugin.h"
#include "version.h"

namespace FrameProcessor {

  /**
   * Callback function used to report status of a delivered message.
   *
   * This function is only used internally.
   *
   * \param[in] kafka_producer- Pointer to a Kafka producer handler.
   * \param[in] kafka_message - Pointer to the message structure of the message being reported
   * \param[in] opaque - Opaque pointer (not used)
   */
  static void kafka_message_callback(rd_kafka_t *kafka_producer,
                                     const rd_kafka_message_t *kafka_message,
                                     void *opaque)
  {
    // Resolve message buffer from private pointer in message
    if (!kafka_message->_private) {
      LOG4CXX_ERROR(Logger::getLogger("FP.KafkaProducer"),
        "Message buffer not found in callback");
      return;
    }
    PvaFrameBuffer* buffer = static_cast<PvaFrameBuffer*>(kafka_message->_private);
    LOG4CXX_DEBUG(Logger::getLogger("FP.KafkaProducer"),
      "Message callback for frame " << buffer->frame_number_);

    HexitecKafkaPvaPlugin *kafka_producer_plugin = static_cast<HexitecKafkaPvaPlugin *>(buffer->plugin_);
    if (kafka_message->err) {
      kafka_producer_plugin->on_message_error(
        rd_kafka_err2str(kafka_message->err));
    } else {
      // count message as acknowledged
      kafka_producer_plugin->on_message_ack();
    }

    delete buffer;
  }

  const std::string HexitecKafkaPvaPlugin::CONFIG_SERVERS = "servers";
  const std::string HexitecKafkaPvaPlugin::CONFIG_TOPIC = "topic";
  const std::string HexitecKafkaPvaPlugin::CONFIG_PARTITION = "partition";
  const std::string HexitecKafkaPvaPlugin::CONFIG_DATASETS = "datasets";
  const std::string HexitecKafkaPvaPlugin::CONFIG_INCLUDE_PARAMETERS = "include_parameters";

  /**
   * The constructor sets up logging used within the class.
   */
  HexitecKafkaPvaPlugin::HexitecKafkaPvaPlugin()
    : datasets_({KAFKA_DEFAULT_DATASET}),
      topic_name_(KAFKA_DEFAULT_TOPIC),
      kafka_producer_(NULL), kafka_topic_(NULL),
      partition_(RD_KAFKA_PARTITION_UA),
      include_parameters_(true),
      builder_(this)
  {
    // Setup logging for the class
    logger_ = Logger::getLogger("FP.HexitecKafkaPvaPlugin");
    LOG4CXX_TRACE(logger_, "HexitecKafkaPvaPlugin constructor.");
    this->reset_statistics();
  }

  /**
   * The destructor cleans up Kafka handlers.
   */
  HexitecKafkaPvaPlugin::~HexitecKafkaPvaPlugin()
  {
    LOG4CXX_TRACE(logger_, "HexitecKafkaPvaPlugin destructor.");
    destroy_kafka();
  }

  /**
   * Set configuration options for this Plugin.
   *
   * This sets up the Kafka Producer Plugin according to the configuration IpcMessage
   * objects that are received.
   *
   * \param[in] config - IpcMessage containing configuration data.
   * \param[out] reply - Response IpcMessage.
   */
  void HexitecKafkaPvaPlugin::configure(OdinData::IpcMessage &config,
                                      OdinData::IpcMessage &reply)
  {
    boost::lock_guard<boost::recursive_mutex> lock(mutex_);
    if (config.has_param(CONFIG_SERVERS)) {
      destroy_kafka();
      configure_kafka_servers(config.get_param<std::string>(CONFIG_SERVERS));
      configure_kafka_topic(this->topic_name_);
    }

    if (config.has_param(CONFIG_TOPIC)) {
      configure_kafka_topic(config.get_param<std::string>(CONFIG_TOPIC));
    }

    if (config.has_param(CONFIG_PARTITION)) {
      configure_partition(config.get_param<uint32_t>(CONFIG_PARTITION));
    }

    if (config.has_param(CONFIG_DATASETS)) {
      configure_datasets(config.get_param<std::string>(CONFIG_DATASETS));
    }

    if (config.has_param(CONFIG_INCLUDE_PARAMETERS)) {
      this->include_parameters_ = config.get_param<bool>(CONFIG_INCLUDE_PARAMETERS);
    }
  }

  /**
   * Get the configuration values for this Plugin.
   *
   * \param[out] reply - Response IpcMessage.
   */
  void HexitecKafkaPvaPlugin::requestConfiguration(OdinData::IpcMessage &reply)
  {
    reply.set_param(get_name() + "/" + HexitecKafkaPvaPlugin::CONFIG_SERVERS,
                    this->servers_);
    reply.set_param(get_name() + "/" + HexitecKafkaPvaPlugin::CONFIG_TOPIC,
                    this->topic_name_);
    reply.set_param(get_name() + "/" + HexitecKafkaPvaPlugin::CONFIG_PARTITION,
                    this->partition_);
    reply.set_param(get_name() + "/" + HexitecKafkaPvaPlugin::CONFIG_DATASETS,
                    boost::algorithm::join(datasets_, ","));
    reply.set_param(get_name() + "/" + HexitecKafkaPvaPlugin::CONFIG_INCLUDE_PARAMETERS,
                    this->include_parameters_);
  }

  /**
   * Collate status information for the plugin. The status is added to the status IpcMessage object.
   *
   * \param[out] status - Reference to an IpcMessage value to store the status.
   */
  void HexitecKafkaPvaPlugin::status(OdinData::IpcMessage &status)
  {
    // Make sure statistics are updated
    poll_delivery_message_report_queue();
    /* Number of sent frames */
    status.set_param(get_name() + "/" + "sent", frames_sent_);
    /* Number of lost frames */
    status.set_param(get_name() + "/" + "lost", frames_lost_);
    /* Number of acknowledged frames */
    status.set_param(get_name() + "/" + "ack", frames_ack_);
  }

  /**
   * Clear frame statistics
   */
  bool HexitecKafkaPvaPlugin::reset_statistics()
  {
    this->frames_sent_ = 0;
    this->frames_lost_ = 0;
    this->frames_ack_ = 0;
    return true;
  }

  /**
   * Destroy Kafka handlers for the connection and the topic
   */
  void HexitecKafkaPvaPlugin::destroy_kafka()
  {
    if (kafka_topic_ != NULL) {
      rd_kafka_flush(kafka_producer_, KAFKA_LINGER_MS);
      rd_kafka_topic_destroy(kafka_topic_);
      kafka_topic_ = NULL;
    }
    if (kafka_producer_ != NULL) {
      rd_kafka_destroy(kafka_producer_);
      kafka_producer_ = NULL;
    }
  }

  /**
   * Poll the delivery message report queue, calling the
   * callback function if appropriate.
   */
  void HexitecKafkaPvaPlugin::poll_delivery_message_report_queue()
  {
    if (kafka_producer_ != NULL) {
      boost::lock_guard<boost::recursive_mutex> lock(mutex_);
      rd_kafka_poll(kafka_producer_, 0);
    }
  }

  /**
   * Configure Kafka connection handler for the server/s specified.
   *
   * \param[in] servers - string representing Kafka brokers using format: IP:PORT[,IP2:PORT2,...]
   */
  void HexitecKafkaPvaPlugin::configure_kafka_servers(std::string servers)
  {
    rd_kafka_t *kafka_producer;
    rd_kafka_conf_t *kafka_config;
    char errBuf[KAFKA_ERROR_BUFFER_LEN];
    kafka_config = rd_kafka_conf_new();
    int status;

    status = rd_kafka_conf_set(kafka_config,
                               "message.max.bytes",
                               KAFKA_MESSAGE_MAX_BYTES,
                               errBuf,
                               sizeof(errBuf));

    if (status != RD_KAFKA_CONF_OK) {
      LOG4CXX_ERROR(logger_, "Kafka configuration error while setting max message size: "
        << errBuf);
      return;
    }

    status = rd_kafka_conf_set(kafka_config,
                               "bootstrap.servers",
                               servers.c_str(),
                               errBuf,
                               sizeof(errBuf));

    if (status != RD_KAFKA_CONF_OK) {
      LOG4CXX_ERROR(logger_, "Kafka configuration error while setting botstrap servers"
        << errBuf);
      return;
    }

    // Configure callback to count ACKed messages
    rd_kafka_conf_set_dr_msg_cb(kafka_config, kafka_message_callback);

    // kafkaProducer will free kafka_config when destroyed
    kafka_producer = rd_kafka_new(RD_KAFKA_PRODUCER, kafka_config, errBuf,
                                  sizeof(errBuf));
    if (!kafka_producer) {
      LOG4CXX_ERROR(logger_, "Kafka handler error: " << errBuf);
      return;
    }

    this->kafka_producer_ = kafka_producer;

    this->servers_ = servers;
    LOG4CXX_TRACE(logger_, "Configured kafka servers: " << servers);

  }

  /**
   * Configure Kafka topic handler for the topic specified
   *
   * \param[in] topic_name - string representing the topic name.
   */
  void HexitecKafkaPvaPlugin::configure_kafka_topic(std::string topic_name)
  {

    if (this->kafka_producer_ == NULL) {
      LOG4CXX_WARN(logger_, "Broker is not configured");
      this->kafka_topic_ = NULL;
      return;
    }

    if (this->kafka_topic_ != NULL) {
      rd_kafka_topic_destroy(kafka_topic_);
    }

    this->kafka_topic_ = rd_kafka_topic_new(kafka_producer_,
                                            topic_name.c_str(),
                                            NULL);

    if (!this->kafka_topic_) {
      LOG4CXX_ERROR(logger_, "Kafka topic error");
    }

    this->topic_name_ = topic_name;
    LOG4CXX_TRACE(logger_, "Configured kafka topic: " << topic_name);
  }

  /**
   * Configure the dataset that will be published
   */
  void HexitecKafkaPvaPlugin::configure_datasets(std::string datasets)
  {
    const std::string delimiter = ",";
    std::vector<std::string> dataset_names;
    datasets_.clear();

    boost::algorithm::split(dataset_names, datasets, boost::is_any_of(delimiter));
    std::for_each(dataset_names.begin(), dataset_names.end(), [this](std::string dataset) {
      boost::algorithm::trim(dataset);
      if (!dataset.empty()) {
        this->datasets_.push_back(dataset);
      }
    });
    LOG4CXX_TRACE(logger_, "Configured datasets: " << boost::algorithm::join(datasets_, ","));
  }

  /**
   * Set Kafka partition to send messages to
   *
   * If it is not configured, it defaults to automatic partitioning (using
   * the topic's partitioner function)
   *
   * \param[in] partition - partition number.
   */
  void HexitecKafkaPvaPlugin::configure_partition(int32_t partition)
  {
    this->partition_ = partition;
  }

  /**
   * Create and enqueue a frame message to kafka server/s
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecKafkaPvaPlugin::enqueue_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Sending frame to message queue ...");
    if (!this->kafka_topic_) {
      LOG4CXX_WARN(logger_, "Topic not configured");
      return;
    }
    // This lock avoids configuring/destroying/enqueuing at the same time
    boost::lock_guard<boost::recursive_mutex> lock(mutex_);

    //PvaFrameBuffer *buffer = create_message(frame);
    auto buffer = builder_.build_buffer(frame);
    if (!buffer) {
      LOG4CXX_ERROR(logger_, "Error creating PVA message buffer");
      return;
    }

    // enqueue message
    int status = rd_kafka_produce(
      this->kafka_topic_,
      partition_,
      /* default message flags, buffer will be freed in callback */
      0,
      /* buffer data and size */
      buffer->pvdata_, buffer->pvdata_size_,
      /* No key */
      NULL, 0,
      /* Opaque pointer to the buffer, allows cleanup in callback*/
      buffer);

    if (status) {
      // Dropping frame, probably the queue is full
      LOG4CXX_ERROR(logger_, "Error while producing: "
        << rd_kafka_err2str(rd_kafka_last_error()));
      delete buffer;
      frames_lost_++;
    } else {
      frames_sent_++;
    }
    rd_kafka_poll(this->kafka_producer_, 0);
  }

  /**
   * It updates stats when a message is acknowledged
   */
  void HexitecKafkaPvaPlugin::on_message_ack()
  {
    this->frames_ack_++;
  }

  /**
   * It logs an error when a message delivery has failed
   */
  void HexitecKafkaPvaPlugin::on_message_error(const char *error)
  {
    LOG4CXX_ERROR(logger_, "Error while delivering message: " << error);
  }

  /**
   * If dataset configured matches, it sends the frame to kafka server/s
   *
   * \param[in] frame - Pointer to a Frame object.
   */
  void HexitecKafkaPvaPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    LOG4CXX_TRACE(logger_, "Received a new frame...");
    std::string frame_dataset = frame->get_meta_data().get_dataset_name();
    if (std::find(this->datasets_.begin(), this->datasets_.end(), frame_dataset) != this->datasets_.end()) {
      this->enqueue_frame(frame);
    }
    this->push(frame);
  }

  int HexitecKafkaPvaPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }

  int HexitecKafkaPvaPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }

  int HexitecKafkaPvaPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }

  std::string HexitecKafkaPvaPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }

  std::string HexitecKafkaPvaPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }

} /* namespace FrameProcessor */
