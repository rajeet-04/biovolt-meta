#include "NetworkManager.h"

#include <Arduino.h>

#include "Backoff.h"

void NetworkManager::begin(const RuntimeConfig& config) {
  ssid_ = config.wifiSsid;
  password_ = config.wifiPassword;
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  startConnection(0);
}

void NetworkManager::startConnection(uint64_t nowMs) {
  WiFi.disconnect(false, false);
  WiFi.begin(ssid_.c_str(), password_.c_str());
  state_ = NetworkState::Connecting;
  nextAttemptMs_ = nowMs + reconnectDelayMs(attempt_);
  if (attempt_ < 4) ++attempt_;
  Serial.println("Wi-Fi connecting");
}

void NetworkManager::poll(uint64_t nowMs) {
  if (WiFi.status() == WL_CONNECTED) {
    if (state_ != NetworkState::Connected) {
      state_ = NetworkState::Connected;
      attempt_ = 0;
      Serial.print("Wi-Fi connected, IP=");
      Serial.println(WiFi.localIP());
    }
    return;
  }

  if (state_ == NetworkState::Connected) {
    state_ = NetworkState::Disconnected;
    nextAttemptMs_ = nowMs;
    Serial.println("Wi-Fi disconnected");
  }
  if (nowMs >= nextAttemptMs_) startConnection(nowMs);
}

