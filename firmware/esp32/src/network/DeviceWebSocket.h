#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

#include <WebSocketsClient.h>

#include "../config/ConfigStore.h"

enum class WebSocketState { Disconnected, Connecting, Connected };

class DeviceWebSocket {
 public:
  void begin(const RuntimeConfig& config);
  void poll(uint64_t nowMs, bool networkConnected);
  bool connected() const { return state_ == WebSocketState::Connected; }
  bool sendText(const char* payload, size_t length);
  WebSocketState state() const { return state_; }

 private:
  static void eventCallback(WStype_t type, uint8_t* payload, size_t length);
  void handleEvent(WStype_t type, uint8_t* payload, size_t length);
  void startConnection(uint64_t nowMs);

  WebSocketsClient client_;
  std::string host_;
  std::string path_;
  std::string headers_;
  uint16_t port_{8000};
  WebSocketState state_{WebSocketState::Disconnected};
  uint64_t nextAttemptMs_{0};
  uint32_t attempt_{0};
  static DeviceWebSocket* active_;
};
