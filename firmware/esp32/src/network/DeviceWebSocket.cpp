#include "DeviceWebSocket.h"

#include <Arduino.h>

#include "Backoff.h"

DeviceWebSocket* DeviceWebSocket::active_ = nullptr;

void DeviceWebSocket::begin(const RuntimeConfig& config) {
  host_ = config.backendHost;
  path_ = config.backendPath;
  port_ = config.backendPort;
  headers_ = "X-BioVolt-Device-ID: " + config.deviceId + "\r\nAuthorization: Bearer " +
             config.deviceToken + "\r\n";
  active_ = this;
  client_.onEvent(DeviceWebSocket::eventCallback);
  state_ = WebSocketState::Disconnected;
  nextAttemptMs_ = 0;
  attempt_ = 0;
}

void DeviceWebSocket::startConnection(uint64_t nowMs) {
  client_.setExtraHeaders(headers_.c_str());
  client_.begin(host_.c_str(), port_, path_.c_str());
  state_ = WebSocketState::Connecting;
  nextAttemptMs_ = nowMs + reconnectDelayMs(attempt_);
  if (attempt_ < 4) ++attempt_;
}

void DeviceWebSocket::poll(uint64_t nowMs, bool networkConnected) {
  if (!networkConnected) {
    if (state_ != WebSocketState::Disconnected) client_.disconnect();
    state_ = WebSocketState::Disconnected;
    return;
  }
  client_.loop();
  if (state_ == WebSocketState::Disconnected && nowMs >= nextAttemptMs_) startConnection(nowMs);
}

bool DeviceWebSocket::sendText(const char* payload, size_t length) {
  return connected() && payload && client_.sendTXT(payload, length);
}

void DeviceWebSocket::eventCallback(WStype_t type, uint8_t* payload, size_t length) {
  if (active_) active_->handleEvent(type, payload, length);
}

void DeviceWebSocket::handleEvent(WStype_t type, uint8_t*, size_t) {
  if (type == WStype_CONNECTED) {
    state_ = WebSocketState::Connected;
    attempt_ = 0;
    Serial.println("WebSocket connected");
  } else if (type == WStype_DISCONNECTED) {
    state_ = WebSocketState::Disconnected;
    nextAttemptMs_ = 0;
    Serial.println("WebSocket disconnected");
  }
}
