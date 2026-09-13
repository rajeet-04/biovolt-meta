#pragma once

#include <cstdint>
#include <string>

#include <WiFi.h>

#include "../config/ConfigStore.h"

enum class NetworkState { Disconnected, Connecting, Connected };

class NetworkManager {
 public:
  void begin(const RuntimeConfig& config);
  void poll(uint64_t nowMs);
  bool connected() const { return state_ == NetworkState::Connected; }
  NetworkState state() const { return state_; }

 private:
  void startConnection(uint64_t nowMs);

  std::string ssid_;
  std::string password_;
  NetworkState state_{NetworkState::Disconnected};
  uint64_t nextAttemptMs_{0};
  uint32_t attempt_{0};
};

